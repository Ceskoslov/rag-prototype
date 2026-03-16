"""Database async engine and session configuration."""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.settings import settings


class Base(DeclarativeBase):
    """Base declarative model with common columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )


async_engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
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


__all__ = ["Base", "async_engine", "async_session_factory", "get_async_session"]
