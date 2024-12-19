from dotenv import load_dotenv
import os

load_dotenv(override=True)


class Settings:
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", str(6333)))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SENTENCE_TRANSFORMER_MODEL: str = os.getenv("SENTENCE_TRANSFORMER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    VECTOR_SIZE = os.getenv("VECTOR_SIZE", "384")


settings = Settings()
