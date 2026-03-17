"""Application settings and configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = (
        "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_db"
    )
    redis_url: str = "redis://localhost:6379/0"
    api_key: str = "test-api-key-12345"

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str = "2024-05-01-preview"
    azure_openai_deployment_name: str | None = None
    azure_openai_embedding_deployment: str | None = None

    embedding_provider: str = "local"

    chroma_api_url: str = "http://localhost:8000"


settings = Settings()
