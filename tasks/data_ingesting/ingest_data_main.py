import asyncio
import datetime
from backend.src.qdrant_wrapper import AsyncQdrantClientWrapper
from shared.utils.app_logger import logger
from shared.config import settings
import time


async def main():
    start_time = time.time()
    start_datetime = datetime.datetime.now()
    logger.info(f"Starting data fetching process on {start_datetime}")
    folder_path = settings.PROCESSED_NBA_DATA_PATH
    logger.info(f"Loading data from {folder_path}")

    async with AsyncQdrantClientWrapper(
        host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, collection_name=settings.QDRANT_COLLECTION_NAME
    ) as qdrant_object:
        await qdrant_object.initialize_qdrant_collection(
            vector_size=settings.QDRANT_VECTOR_SIZE,
            reset_collection=settings.QDRANT_RESET_COLLECTION,  # True to allow duplication of the data
        )
        await qdrant_object.store_players_embedding(data_dir=folder_path)  # ✅ Await the async function

    logger.info(
        f"Finished data fetching process on {datetime.datetime.now()} and it took in minutes {round((time.time() - start_time) / 60, 2)}"
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())  # ✅ Safe in scripts, but NOT inside FastAPI or Jupyter
    except RuntimeError:  # Handles cases where an event loop is already running
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
