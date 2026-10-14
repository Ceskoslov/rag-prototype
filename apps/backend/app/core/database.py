"""Database async engine and session configuration."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.settings import settings


def prepare_async_database_url(
    database_url: str,
) -> tuple[URL, dict[str, object]]:
    """Normalize managed Postgres URLs for SQLAlchemy's asyncpg dialect."""
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")

    connect_args: dict[str, object] = {}
    if url.drivername == "postgresql+asyncpg":
        query = dict(url.query)
        ssl_mode = query.pop("sslmode", None)
        query.pop("channel_binding", None)
        if ssl_mode:
            connect_args["ssl"] = ssl_mode
        url = url.set(query=query)
    return url, connect_args


class Base(DeclarativeBase):
    """Base declarative model with common columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )


database_url, database_connect_args = prepare_async_database_url(
    settings.database_url
)
async_engine = create_async_engine(
    database_url,
    connect_args=database_connect_args,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for async sessions."""
    async with async_session_factory() as session:
        yield session


__all__ = [
    "Base",
    "async_engine",
    "async_session_factory",
    "get_async_session",
    "prepare_async_database_url",
]
