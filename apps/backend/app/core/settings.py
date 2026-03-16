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


settings = Settings()
