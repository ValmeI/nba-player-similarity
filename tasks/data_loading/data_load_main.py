import time
from datetime import datetime
from shared.utils.app_logger import logger
from tasks.data_loading.get_nba_data import fetch_all_players_stats_in_threads
from tasks.data_loading.process_data import process_player_metrics_in_processes
import os
from shared.config import settings


if __name__ == "__main__":
    logger.info(f"Starting data fetching process on {datetime.now()}")

    # NB! Next part is about fetching all players raw data
    if settings.FETCH_RAW_DATA_FETCH:
        start_time = time.perf_counter()
        logger.info(f"Starting NBA raw data fetching process on {datetime.now()}")
        fetch_all_players_stats_in_threads()
        logger.info(
            f"Finished NBA raw data fetching process on {datetime.now()} and it took {time.perf_counter() - start_time:.2f} seconds"
        )

    if not os.path.exists(settings.RAW_NBA_DATA_PATH):
        logger.error(f"Raw NBA data folder {settings.RAW_NBA_DATA_PATH} does not exist.")
        exit(1)

    # NB! Next part is about processing all players metrics
    # In case u want to process all players metrics again
    if settings.PROCESS_ALL_PLAYERS_METRIC:
        process_player_metrics_in_processes(settings.OWERWRITE_PLAYER_METRICS_IF_EXISTS)
