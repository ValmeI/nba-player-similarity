import time
from datetime import datetime
from backend.utils.app_logger import logger
from data.get_nba_data import fetch_all_players_stats
from data.process_data import process_player_metrics_in_parallel
import os
from backend.config import settings


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
        process_player_metrics_in_parallel(OWERWRITE_PLAYER_METRICS_IF_EXISTS)
