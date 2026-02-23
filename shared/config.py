from typing import Literal, ClassVar
from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):

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

    FAST_API_HOST: str
    FAST_API_PORT: int

    LOG_LEVEL: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    LOG_TO_FILE: bool
    LOG_TO_CONSOLE: bool
    LOG_ERRORS_TO_SEPARATE_FILE: bool

    cpu_count: ClassVar[int] = os.cpu_count()
    MAX_WORKERS: int = Field(default=min(1, cpu_count), gt=0, env="MAX_WORKERS")  # Default to 1 if not set

    FUZZ_THRESHOLD_LOCAL_STATS_FILE: int = Field(..., ge=0, le=100)
    FUZZ_THRESHOLD_LOCAL_NAME: int = Field(..., ge=0, le=100)

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

    RECENT_SEARCHES_ENABLED: bool = Field(default=True)
    RECENT_SEARCHES_FILE_PATH: str = Field(
        default_factory=lambda: os.path.join(
            "/app" if os.path.exists("/app") else ".", "nba_data", "recent_searches", "recent_searches.json"
        )
    )
    RECENT_SEARCHES_DISPLAY_LIMIT: int = Field(default=8, gt=0)
    RECENT_SEARCHES_TTL_DAYS: int = Field(default=7, gt=0)

    FETCH_RAW_DATA_FETCH: bool
    PROCESS_ALL_PLAYERS_METRIC: bool
    OWERWRITE_PLAYER_METRICS_IF_EXISTS: bool

    NBA_API_RETRY_ATTEMPTS: int = Field(default=5, gt=0)
    NBA_API_RETRY_WAIT_MIN: float = Field(default=3.0, ge=0.0)
    NBA_API_RETRY_WAIT_MAX: float = Field(default=10.0, ge=0.0)
    NBA_API_TIMEOUT: int = Field(default=30, gt=0)
    NBA_API_RATE_LIMIT_DELAY: float = Field(default=0.6, ge=0.0)

    API_REQUEST_TIMEOUT: int
    STREAMLIT_TITLE: str
    STREAMLIT_INITIAL_MESSAGE: str
    STREAMLIT_INPUT_PLACEHOLDER: str

    LLM_API_KEY: str
    LLM_MODEL_NAME: str
    LLM_TEMPERATURE: float = Field(..., ge=0.0, le=1.0)
    LLM_MAX_TOKENS: int
    LLM_PROMPT_TEMPLATE: str

    LLM_INTENT_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=1.0)
    LLM_INTENT_MAX_TOKENS: int = Field(default=150, gt=0)

    FRONTEND_VERSION: str
    BACKEND_VERSION: str

    class Config:
        case_sensitive = True
        env_file = ".env"


try:
    settings = Settings()
except Exception as e:
    raise ValueError(f"Environment validation failed: {str(e)}") from e
