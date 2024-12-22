import time
from datetime import datetime
from tqdm import tqdm
from backend.utils.app_logger import logger
from data.get_nba_data import fetch_all_players_stats
from data.process_data import add_all_player_metrics_to_parquet
import os
from backend.config import settings
import pandas as pd


if __name__ == "__main__":
    # NB! Next part is about fetching all players raw data
    FETCH_RAW_DATA_FETCH = False

    if FETCH_RAW_DATA_FETCH:
        start_time = time.perf_counter()
        logger.info(f"Starting NBA raw data fetching process on {datetime.now()}")
        fetch_all_players_stats()
        logger.info(
            f"Finished NBA raw data fetching process on {datetime.now()} and it took {time.perf_counter() - start_time:.2f} seconds"
        )

    # NB! Next part is about processing all players metrics
    PROCESS_ALL_PLAYERS_METRIC = True  # In case u want to process all players metrics again
    OWERWRITE_PLAYER_METRICS_IF_EXISTS = True

    if PROCESS_ALL_PLAYERS_METRIC and os.path.exists(settings.RAW_NBA_DATA_PATH):
        start_time = time.perf_counter()
        logger.info(
            f"Starting to process all players metrics on {datetime.now()} and add them to folder {settings.PROCESSED_NBA_DATA_PATH}"
        )
        all_raw_files = os.listdir(settings.RAW_NBA_DATA_PATH)
        for file in tqdm(all_raw_files):
            file_path = os.path.join(settings.RAW_NBA_DATA_PATH, file)
            player_name = file.split("_career_stats.parquet")[0].replace("_", " ")  # Temporary fix
            df = pd.read_parquet(file_path)
            add_all_player_metrics_to_parquet(df, player_name, overwrite_all_metrics=OWERWRITE_PLAYER_METRICS_IF_EXISTS)
        logger.info(
            f"Finished processing all players metrics on {datetime.now()} and it took {time.perf_counter() - start_time:.2f} seconds"
        )
