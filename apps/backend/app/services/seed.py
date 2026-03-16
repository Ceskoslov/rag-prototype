from __future__ import annotations

import arq
from arq.connections import RedisSettings

from app.core.logging import get_logger
from app.repositories.vectorstore import ChromaRepository
from app.schemas.common import Department

logger = get_logger(__name__)


class SeedService:
    chroma_repo: ChromaRepository
    redis_url: str

    def __init__(self, chroma_repo: ChromaRepository, redis_url: str):
        self.chroma_repo = chroma_repo
        self.redis_url = redis_url

    async def seed_all_departments(self) -> dict[str, str]:
        results: dict[str, str] = {}
        arq_redis_url = self.redis_url.rsplit("/", 1)[0] + "/1"

        pool = await arq.create_pool(RedisSettings.from_dsn(arq_redis_url))
        try:
            for department in Department:
                collection_name = self.chroma_repo._collection_name(department.value)
                count = self.chroma_repo.get_collection_count(collection_name)

                if count > 0:
                    logger.info(
                        "seed_department_skipped",
                        department=department.value,
                        count=count,
                    )
                    results[department.value] = "skipped"
                else:
                    await pool.enqueue(
                        "ingest_department_task", department=department.value
                    )
                    logger.info(
                        "seed_department_enqueued",
                        department=department.value,
                    )
                    results[department.value] = "seeded"
        finally:
            await pool.close(close_connection=True)

        return results

    async def check_seed_status(self) -> dict[str, int]:
        status: dict[str, int] = {}
        for department in Department:
            collection_name = self.chroma_repo._collection_name(department.value)
            count = self.chroma_repo.get_collection_count(collection_name)
            status[department.value] = count
        return status
