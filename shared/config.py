from dotenv import load_dotenv
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field
import os


load_dotenv(override=True)


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
    QDRANT_RESET_COLLECTION: bool

    # FastAPI settings
    FAST_API_HOST: str
    FAST_API_PORT: int

    # Logging settings
    # Valid log levels that loguru accepts, incase there is typos in the .env and it would make whole code unresponsive
    LOG_LEVEL: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    LOG_TO_FILE: bool
    LOG_TO_CONSOLE: bool
    LOG_ERRORS_TO_SEPARATE_FILE: bool

    # Processing settings, takes account of CPU cores available
    MAX_WORKERS: int = Field(1, env="MAX_WORKERS")  # Default to 1 if not set
    cpu_count = os.cpu_count()
    MAX_WORKERS: int = Field(default=min(MAX_WORKERS, cpu_count), gt=0)

    # Fuzzy matching settings
    FUZZ_THRESHOLD_LOCAL_STATS_FILE: int = Field(..., ge=0, le=100)
    FUZZ_THRESHOLD_LOCAL_NAME: int = Field(..., ge=0, le=100)

    # Data paths
    RAW_NBA_DATA_PATH: str
    PROCESSED_NBA_DATA_PATH: str

    # NBA Data Loading settings
    FETCH_RAW_DATA_FETCH: bool
    PROCESS_ALL_PLAYERS_METRIC: bool
    OWERWRITE_PLAYER_METRICS_IF_EXISTS: bool

    # Frontend settings
    API_REQUEST_TIMEOUT: int
    STREAMLIT_TITLE: str
    STREAMLIT_INITIAL_MESSAGE: str
    STREAMLIT_INPUT_PLACEHOLDER: str

    # LLM settings
    LLM_API_KEY: str
    LLM_MODEL_NAME: str
    LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int
    LLM_PROMPT_TEMPLATE: str

    class Config:
        case_sensitive = True
        env_file = ".env"


try:
    settings = Settings()
except Exception as e:
    raise ValueError(f"Environment validation failed: {str(e)}") from e
