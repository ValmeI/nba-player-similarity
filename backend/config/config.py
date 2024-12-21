from dotenv import load_dotenv
import os

load_dotenv(override=True)


class Settings:
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", str(6333)))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SENTENCE_TRANSFORMER_MODEL: str = os.getenv("SENTENCE_TRANSFORMER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    VECTOR_DISTANCE_METRIC: str = os.getenv("VECTOR_DISTANCE_METRIC", "Cosine")
    VECTOR_SEARCH_LIMIT: int = int(os.getenv("VECTOR_SEARCH_LIMIT", str(5)))
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE", str(512)))
    MAX_THREADING_WORKERS: int = int(os.getenv("MAX_THREADING_WORKERS", str(10)))
    FUZZ_THRESHOLD: int = int(os.getenv("FUZZ_THRESHOLD", str(80)))


settings = Settings()
