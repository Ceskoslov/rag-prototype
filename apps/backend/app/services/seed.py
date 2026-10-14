from __future__ import annotations

from pathlib import Path

import arq
from arq.connections import RedisSettings

from app.core.logging import get_logger
from app.repositories.vectorstore import ChromaRepository
from app.services.ingestion import IngestionService

logger = get_logger(__name__)


class SeedService:
    def __init__(
        self,
        chroma_repo: ChromaRepository,
        redis_url: str,
        data_dir: Path,
        arq_redis_url: str | None = None,
    ) -> None:
        self.chroma_repo = chroma_repo
        self.redis_url = redis_url
        self.data_dir = data_dir
        self.arq_redis_url = arq_redis_url

    async def seed_all_knowledge_bases(self) -> dict[str, str]:
        results: dict[str, str] = {}
        pool = await arq.create_pool(
            RedisSettings.from_dsn(
                self.arq_redis_url or self.redis_url.rsplit("/", 1)[0] + "/1"
            )
        )
        try:
            for name in IngestionService.discover_knowledge_bases(self.data_dir):
                try:
                    count = self.chroma_repo.get_collection(name).count()
                except ValueError:
                    count = 0
                if count > 0:
                    results[name] = "skipped"
                    continue
                await pool.enqueue_job("ingest_knowledge_base_task", name)
                logger.info("seed_enqueued", knowledge_base=name)
                results[name] = "seeded"
        finally:
            await pool.aclose()
        return results

    async def check_seed_status(self) -> dict[str, int]:
        counts = {}
        for name in IngestionService.discover_knowledge_bases(self.data_dir):
            try:
                counts[name] = self.chroma_repo.get_collection(name).count()
            except ValueError:
                counts[name] = 0
        return counts
