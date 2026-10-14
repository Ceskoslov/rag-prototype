"""Application settings and configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
    )

    environment: str = "development"
    database_url: str = (
        "postgresql+asyncpg://rag_user:rag_password@localhost:5432/rag_db"
    )
    redis_url: str = "redis://localhost:6379/0"
    arq_redis_url: str | None = None
    api_key: str = "test-api-key-12345"
    data_dir: Path = Path("data")
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    cors_origin_regex: str | None = None
    enable_evaluation: bool = False
    evaluation_model: str | None = None
    rag_timeout_seconds: float = 180

    llm_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_deployment_name: str | None = None
    azure_openai_embedding_deployment: str | None = None

    dense_max_distance: float | None = 0.8
    reranker_model: str | None = None

    embedding_provider: str = "mock"
    embedding_model_name: str = "BAAI/bge-m3"
    openai_embedding_model: str = "text-embedding-3-small"

    chroma_provider: str = "http"
    chroma_api_url: str = "http://localhost:8000"
    chroma_cloud_host: str = "api.trychroma.com"
    chroma_tenant: str | None = None
    chroma_database: str | None = None
    chroma_api_key: str | None = None


settings = Settings()
