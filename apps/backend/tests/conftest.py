"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for pytest-asyncio."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_engine_test():
    """Create test async engine with in-memory SQLite."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session_factory_test(async_engine_test):
    """Create test async session factory."""
    session_factory = async_sessionmaker(
        async_engine_test,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return session_factory
