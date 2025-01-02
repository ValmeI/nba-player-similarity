from concurrent.futures import ThreadPoolExecutor, as_completed
from nba_api.stats.static import players
import os
import pandas as pd
from nba_api.stats.endpoints import playercareerstats
from tqdm import tqdm
from backend.utils.app_logger import logger
from backend.config import settings
import random
import time


NBA_STATS_TIMEOUT = 10
pd.set_option("future.no_silent_downcasting", True)


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
        career = playercareerstats.PlayerCareerStats(player_id=player_id, timeout=NBA_STATS_TIMEOUT)
        player_stats_df = career.get_data_frames()[0]
        if player_stats_df.empty:
            logger.warning(f"Empty DataFrame for {player_name} not saved.")
            return
        player_stats_df.to_parquet(file_path, index=False)
        logger.info(f"Raw NBA data for {player_name} saved to {file_path}.")
        # Introduce a random delay between requests, try to avoid rate limits
        time.sleep(random.uniform(0.5, 2.0))  # Random delay between 0.5 to 2 seconds
    except Exception as e:
        logger.error(f"Error fetching data for {player_name}: {e}")
        raise


def fetch_all_players_stats_in_threads():
    all_players = players.get_players()
    logger.info(f"Found {len(all_players)} players in NBA. Fetching raw NBA data...")

    with ThreadPoolExecutor(max_workers=settings.MAX_THREADING_WORKERS) as executor:
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
