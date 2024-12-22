from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from nba_api.stats.static import players
import os
import pandas as pd
from nba_api.stats.endpoints import playercareerstats
from backend.utils.app_logger import logger
from backend.config import settings


pd.set_option("future.no_silent_downcasting", True)


def fetch_and_save_player_stats(player_name: str):
    if not os.path.exists(settings.RAW_NBA_DATA_PATH):
        os.makedirs(settings.RAW_NBA_DATA_PATH)

    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        logger.info(f"Player '{player_name}' not found.")
        return None
    player_id = player_dict[0]["id"]

    file_path = os.path.join(settings.RAW_NBA_DATA_PATH, f'{player_name.replace(" ", "_")}_career_stats.parquet')

    def fetch_data_worker():
        logger.info(f"Fetching raw NBA data for {player_name} from NBA API.")
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        player_stats_df = career.get_data_frames()[0]
        player_stats_df.to_parquet(file_path, index=False)
        logger.info(f"Raw NBA data for {player_name} saved to {file_path}.")

    if os.path.exists(file_path):
        logger.info(f"Raw NBA data for {player_name} already exists, continuing with next player.")
        return None
    else:
        logger.info(f"Starting thread to fetch raw NBA data for {player_name} from NBA API.")
        with ThreadPoolExecutor(max_workers=settings.MAX_THREADING_WORKERS) as executor:
            future = executor.submit(fetch_data_worker)

            for future in as_completed([future]):
                try:
                    future.result()
                    logger.info(
                        f"Successfully fetched raw NBA data for {player_name} with thread {threading.get_ident()}."
                    )
                except Exception as e:
                    logger.error(
                        f"Error fetching raw NBA data for {player_name} with thread {threading.get_ident()}: {e}"
                    )

    logger.info(f"Finished thread to fetch raw NBA data for {player_name}.")


def fetch_all_players_stats():
    all_players = players.get_players()
    logger.info(f"Found {len(all_players)} players in NBA. Fetching raw NBA data for {len(all_players)} players...")
    for index, player in enumerate(all_players):
        logger.info(f"Processing player {index + 1}/{len(all_players)}: {player['full_name']}")
        try:
            fetch_and_save_player_stats(player["full_name"])
        except Exception as e:
            logger.error(f"Error processing player {player['full_name']}: {e}")
