from dotenv import load_dotenv
import os

load_dotenv(override=True)


class Settings:
    QDRANT_HOST: str = os.getenv("QDRANT_HOST")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL")
    SENTENCE_TRANSFORMER_MODEL: str = os.getenv("SENTENCE_TRANSFORMER_MODEL")
    VECTOR_DISTANCE_METRIC: str = os.getenv("VECTOR_DISTANCE_METRIC")
    VECTOR_SEARCH_LIMIT: int = int(os.getenv("VECTOR_SEARCH_LIMIT"))
    VECTOR_SEARCH_SCORE_THRESHOLD: float = float(os.getenv("VECTOR_SEARCH_SCORE_THRESHOLD"))
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE"))
    MAX_THREADING_WORKERS: int = int(os.getenv("MAX_THREADING_WORKERS"))
    FUZZ_THRESHOLD: int = int(os.getenv("FUZZ_THRESHOLD"))
    RAW_NBA_DATA_PATH: str = os.getenv("RAW_NBA_DATA_PATH")
    PROCESSED_NBA_DATA_PATH: str = os.getenv("PROCESSED_NBA_DATA_PATH")


settings = Settings()
