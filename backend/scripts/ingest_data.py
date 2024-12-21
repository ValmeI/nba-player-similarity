import datetime
from backend.src.store_data import process_player_files_in_threads
from backend.utils.app_logger import logger
from backend.config import settings
import os
import time

if __name__ == "__main__":
    start_time = time.time()
    start_datetime = datetime.datetime.now()
    logger.info(f"Starting data fetching process on {start_datetime}")
    folder_path = "data/players_parquet"
    logger.info(f"Loading data from {folder_path}")
    file_paths = [os.path.join(folder_path, file_path) for file_path in os.listdir(folder_path)]
    logger.info(f"Found {len(file_paths)} files")
    process_player_files_in_threads(
        file_paths=file_paths,
        collection_name="player_career_trajectory",
        max_workers=settings.MAX_THREADING_WORKERS,
        host="localhost",
        port=6333,
        reset_collection=False,
    )
    logger.info(
        f"Finished data fetching process on {datetime.datetime.now()} and it took in minutes {round((time.time() - start_time) / 60, 2)}"
    )
