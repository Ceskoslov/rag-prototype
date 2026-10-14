"""Separate process liveness from dependency readiness."""

import asyncio

import redis.asyncio as redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]


@router.get("/health")
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        services={
            "api": "ok",
            "redis": "unchecked",
            "chromadb": "unchecked",
            "postgres": "unchecked",
        },
    )


async def probe_services() -> dict[str, str]:
    async def postgres():
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))

    async def redis_probe():
        client = redis.from_url(
            settings.redis_url, socket_connect_timeout=2, socket_timeout=2
        )
        try:
            await client.ping()
        finally:
            await client.aclose()

    async def chroma():
        await asyncio.to_thread(lambda: ChromaRepository().client.heartbeat())

    async def check(name, probe):
        try:
            await asyncio.wait_for(probe(), timeout=3)
            return name, "ok"
        except Exception:
            return name, "unavailable"

    return dict(
        await asyncio.gather(
            *(
                check(name, probe)
                for name, probe in [
                    ("postgres", postgres),
                    ("redis", redis_probe),
                    ("chromadb", chroma),
                ]
            )
        )
    )


@router.get("/ready")
async def readiness():
    services = await probe_services()
    healthy = all(value == "ok" for value in services.values())
    return JSONResponse(
        {"status": "ok" if healthy else "degraded", "services": services},
        status_code=200 if healthy else 503,
    )
