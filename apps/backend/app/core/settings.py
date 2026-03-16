"""Application settings and configuration."""

import os
from typing import Literal


class Settings:
    """App settings from environment variables."""

    environment: Literal["development", "staging", "production"] = os.getenv(
        "ENVIRONMENT", "development"
    )
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_db",
    )
    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )
    api_key: str = os.getenv(
        "API_KEY",
        "test-api-key-12345",
    )


settings = Settings()
