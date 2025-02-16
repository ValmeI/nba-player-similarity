from typing import Literal, ClassVar
from pydantic_settings import BaseSettings
from pydantic import Field
import os


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
    cpu_count: ClassVar[int] = os.cpu_count()
    MAX_WORKERS: int = Field(default=min(1, cpu_count), gt=0, env="MAX_WORKERS")  # Default to 1 if not set

    # Fuzzy matching settings
    FUZZ_THRESHOLD_LOCAL_STATS_FILE: int = Field(..., ge=0, le=100)
    FUZZ_THRESHOLD_LOCAL_NAME: int = Field(..., ge=0, le=100)

    # Data paths Constants, (dynamic handling for Docker vs local)
    IS_DOCKER: bool = Field(default=os.path.exists("/app"), description="Detect if running inside Docker")
    BASE_DIR: str = Field(default_factory=lambda: "/app" if os.path.exists("/app") else ".")
    RAW_NBA_DATA_PATH: str = Field(
        default_factory=lambda: os.path.join("/app" if os.path.exists("/app") else ".", "nba_data/raw_parquet_files")
    )
    PROCESSED_NBA_DATA_PATH: str = Field(
        default_factory=lambda: os.path.join(
            "/app" if os.path.exists("/app") else ".", "nba_data/processed_parquet_files"
        )
    )

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
    LLM_TEMPERATURE: float = Field(..., ge=0.0, le=1.0)
    LLM_MAX_TOKENS: int
    LLM_PROMPT_TEMPLATE: str

    # Frontend and Backend versions
    FRONTEND_VERSION: str
    BACKEND_VERSION: str

    class Config:
        case_sensitive = True
        env_file = ".env"


try:
    settings = Settings()
except Exception as e:
    raise ValueError(f"Environment validation failed: {str(e)}") from e
