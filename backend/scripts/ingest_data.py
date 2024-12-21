import datetime
from qdrant_client import QdrantClient
from backend.src.store_data import process_player_files_in_threads, initialize_qdrant_collection
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
    client = QdrantClient(host="localhost", port=6333)
    initialize_qdrant_collection(
        client=client,
        collection_name="player_career_trajectory",
        vector_size=settings.VECTOR_SIZE,
        reset_collection=True,  # True to allow duplication of the data
    )
    process_player_files_in_threads(
        client=client,
        file_paths=file_paths,
        collection_name="player_career_trajectory",
        max_workers=settings.MAX_THREADING_WORKERS,
    )
    logger.info(
        f"Finished data fetching process on {datetime.datetime.now()} and it took in minutes {round((time.time() - start_time) / 60, 2)}"
    )
