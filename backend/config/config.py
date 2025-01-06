from dotenv import load_dotenv
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


load_dotenv(override=True)

# Valid log levels that loguru accepts, incase there is typos in the .env and it would make whole code unresponsive
LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    # Qdrant settings
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_COLLECTION_NAME: str
    QDRANT_VECTOR_DISTANCE_METRIC: Literal["Cosine", "Dot", "Euclidean"] = Field(
        ..., description="Distance metric used for vector similarity"
    )
    QDRANT_VECTOR_SEARCH_LIMIT: int = Field(..., gt=0)
    QDRANT_VECTOR_SEARCH_SCORE_THRESHOLD: float = Field(..., ge=0.0, le=1.0)
    QDRANT_VECTOR_SIZE: int = Field(..., gt=0)

    # Logging settings
    LOG_LEVEL: LogLevel
    LOG_TO_FILE: bool
    LOG_TO_CONSOLE: bool
    LOG_ERRORS_TO_SEPARATE_FILE: bool

    # Threading settings
    MAX_THREADING_WORKERS: int = Field(..., gt=0)

    # Fuzzy matching settings
    FUZZ_THRESHOLD_LOCAL_STATS_FILE: int = Field(..., ge=0, le=100)
    FUZZ_THRESHOLD_LOCAL_NAME: int = Field(..., ge=0, le=100)

    # Data paths
    RAW_NBA_DATA_PATH: str
    PROCESSED_NBA_DATA_PATH: str

    # Logging settings
    LOG_LEVEL: LogLevel
    LOG_TO_FILE: bool
    LOG_TO_CONSOLE: bool
    LOG_ERRORS_TO_SEPARATE_FILE: bool

    class Config:
        case_sensitive = True
        env_file = ".env"


try:
    settings = Settings()
except Exception as e:
    raise ValueError(f"Environment validation failed: {str(e)}") from e
