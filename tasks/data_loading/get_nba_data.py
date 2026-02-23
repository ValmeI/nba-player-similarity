import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from nba_api.stats.static import players
import os
import pandas as pd
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints.commonplayerinfo import CommonPlayerInfo
from tqdm import tqdm
from shared.utils.app_logger import logger
from shared.config import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter, before_sleep_log
import logging


pd.set_option("future.no_silent_downcasting", True)

# Tenacity uses stdlib logging, bridge it to our logger
_std_logger = logging.getLogger("nba_api_retry")


def _nba_api_retry():
    """Return a tenacity retry decorator configured from settings.

    Uses exponential backoff with jitter to avoid thundering herd against NBA API.
    Retries on JSONDecodeError (empty/HTML responses from rate-limiting).
    """
    return retry(
        stop=stop_after_attempt(settings.NBA_API_RETRY_ATTEMPTS),
        wait=wait_exponential_jitter(
            initial=settings.NBA_API_RETRY_WAIT_MIN,
            max=settings.NBA_API_RETRY_WAIT_MAX,
        ),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, json.JSONDecodeError)),
        before_sleep=before_sleep_log(_std_logger, logging.WARNING),
        reraise=True,
    )


@_nba_api_retry()
def _fetch_career_stats(player_id: int) -> pd.DataFrame:
    career = playercareerstats.PlayerCareerStats(player_id=player_id, timeout=settings.NBA_API_TIMEOUT)
    return career.get_data_frames()[0]


@_nba_api_retry()
def _fetch_player_info(player_id: int) -> pd.DataFrame:
    time.sleep(settings.NBA_API_RATE_LIMIT_DELAY)
    info = CommonPlayerInfo(player_id=player_id, timeout=settings.NBA_API_TIMEOUT)
    return info.get_data_frames()[0]


def fetch_and_save_player_stats(player_name: str):
    os.makedirs(settings.RAW_NBA_DATA_PATH, exist_ok=True)
    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        logger.info(f"Player '{player_name}' not found.")
        return None
    player_id = player_dict[0]["id"]

    file_path = os.path.join(settings.RAW_NBA_DATA_PATH, f'{player_name.replace(" ", "_")}_career_stats.parquet')

    if os.path.exists(file_path):
        logger.debug(f"Raw NBA data for {player_name} already exists, skipping.")
        return None

    try:
        logger.info(f"Fetching raw NBA data for {player_name} from NBA API.")
        player_stats_df = _fetch_career_stats(player_id)
        if player_stats_df.empty:
            logger.warning(f"Empty DataFrame for {player_name} not saved.")
            return
        player_stats_df.to_parquet(file_path, index=False)
        logger.info(f"Raw NBA data for {player_name} saved to {file_path}.")
    except Exception as e:
        logger.error(f"Error fetching data for {player_name}: {e}")
        raise


def get_player_position(player_id: int) -> str:
    """Fetch position for a player using the NBA API.

    Returns the full compound position string (e.g., "Guard-Forward").
    Returns "Unknown" if the position cannot be fetched.
    """
    try:
        player_info_df = _fetch_player_info(player_id)
        position = player_info_df["POSITION"].iloc[0] if not player_info_df.empty else "Unknown"
        return position if position else "Unknown"
    except Exception as e:
        logger.warning(f"Failed to fetch position for player_id={player_id}: {e}")
        return "Unknown"


def fetch_all_players_stats_in_threads():
    all_players = players.get_players()
    logger.info(f"Found {len(all_players)} players in NBA. Fetching raw NBA data...")

    with ThreadPoolExecutor(max_workers=settings.MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_and_save_player_stats, player["full_name"]): player["full_name"]
            for player in all_players
        }

        # Wrap the `as_completed` loop with tqdm for progress tracking
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching Players", unit="player"):
            player_name = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Failed to fetch data for {player_name}: {e}")
