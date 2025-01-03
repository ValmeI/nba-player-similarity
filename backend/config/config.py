from dotenv import load_dotenv
import os

load_dotenv(override=True)


def str_to_bool(value):
    """
    Convert string to boolean. Workaround for bool(os.getenv(...))
    as bool('False') evaluates to True.
    """
    return value.lower() in ("true", "1", "yes")


class Settings:
    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT"))
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL")
    LOG_TO_FILE: bool = str_to_bool(os.getenv("LOG_TO_FILE"))
    LOG_TO_CONSOLE: bool = str_to_bool(os.getenv("LOG_TO_CONSOLE"))
    LOG_ERRORS_TO_SEPARATE_FILE: bool = str_to_bool(os.getenv("LOG_ERRORS_TO_SEPARATE_FILE"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME")
    VECTOR_DISTANCE_METRIC: str = os.getenv("VECTOR_DISTANCE_METRIC")
    VECTOR_SEARCH_LIMIT: int = int(os.getenv("VECTOR_SEARCH_LIMIT"))
    VECTOR_SEARCH_SCORE_THRESHOLD: float = float(os.getenv("VECTOR_SEARCH_SCORE_THRESHOLD"))
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE"))
    MAX_THREADING_WORKERS: int = int(os.getenv("MAX_THREADING_WORKERS"))
    FUZZ_THRESHOLD_LOCAL_STATS_FILE: int = int(os.getenv("FUZZ_THRESHOLD_LOCAL_STATS_FILE"))
    FUZZ_THRESHOLD_LOCAL_NAME: int = int(os.getenv("FUZZ_THRESHOLD_LOCAL_NAME"))
    RAW_NBA_DATA_PATH: str = str(os.getenv("RAW_NBA_DATA_PATH"))
    PROCESSED_NBA_DATA_PATH: str = str(os.getenv("PROCESSED_NBA_DATA_PATH"))
    OPENAI_API_KEY: str = str(os.getenv("OPENAI_API_KEY"))


settings = Settings()
