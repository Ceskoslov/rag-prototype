"""ARQ Worker configuration and settings."""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from arq.connections import RedisSettings

from app.core.settings import settings
from app.workers.tasks import evaluate_conversation_task, ingest_knowledge_base_task

logger = logging.getLogger(__name__)


class WorkerSettings:
    functions: ClassVar[list] = [
        ingest_knowledge_base_task,
        evaluate_conversation_task,
    ]

    redis_settings: RedisSettings = RedisSettings.from_dsn(
        settings.arq_redis_url or f"{settings.redis_url.rstrip('/0')}/1"
    )

    max_jobs: int = 5
    job_timeout: int = 300
    keep_result: int = 3600

    @staticmethod
    async def on_startup(ctx: dict[str, Any]) -> None:
        logger.info(
            "ARQ worker started",
            extra={"functions": [f.__name__ for f in WorkerSettings.functions]},
        )

    @staticmethod
    async def on_shutdown(ctx: dict[str, Any]) -> None:
        logger.info("ARQ worker shutting down")
