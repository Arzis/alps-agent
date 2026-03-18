"""Global configuration - loaded from environment variables / .env file."""

from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration - from environment variables/.env"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # === Application Configuration ===
    APP_NAME: str = "Enterprise QA Assistant"
    APP_VERSION: str = "0.1.0"
    ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # === Service Ports ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # === LLM Configuration ===
    OPENAI_API_KEY: SecretStr
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Primary model
    PRIMARY_LLM_MODEL: str = "gpt-4o"
    PRIMARY_LLM_TEMPERATURE: float = 0.1
    PRIMARY_LLM_MAX_TOKENS: int = 4096

    # Fallback model (Codex / lightweight model)
    FALLBACK_LLM_MODEL: str = "gpt-4o-mini"
    FALLBACK_LLM_TEMPERATURE: float = 0.0

    # Embedding model
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 3072

    # === PostgreSQL ===
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: SecretStr = SecretStr("pass")
    POSTGRES_DB: str = "qa_assistant"
    POSTGRES_POOL_MIN: int = 5
    POSTGRES_POOL_MAX: int = 20

    @property
    def POSTGRES_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_ASYNC_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    # === Redis ===
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: SecretStr | None = None
    REDIS_POOL_MAX: int = 50

    @property
    def REDIS_URL(self) -> str:
        password_part = ""
        if self.REDIS_PASSWORD:
            password_part = f":{self.REDIS_PASSWORD.get_secret_value()}@"
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # === Milvus ===
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_TOKEN: str = ""
    MILVUS_DB_NAME: str = "default"
    MILVUS_COLLECTION_NAME: str = "knowledge_base"

    @property
    def MILVUS_URI(self) -> str:
        return f"http://{self.MILVUS_HOST}:{self.MILVUS_PORT}"

    # === RAG Configuration ===
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    RAG_MIN_CONFIDENCE: float = 0.7

    # === Concurrency Control ===
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 120

    # === Session TTL (seconds) ===
    SESSION_TTL: int = 86400  # 24 hours


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
