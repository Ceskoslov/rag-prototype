"""Background task implementations for ARQ worker."""

from __future__ import annotations

from typing import Any

from app.core.database import async_session_factory
from app.core.docstore import RedisDocStore
from app.core.embeddings import get_embedding_model
from app.core.logging import get_logger
from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository
from app.services.chunking import ChunkingService
from app.services.evaluation import EvaluationService
from app.services.ingestion import IngestionService

logger = get_logger(__name__)


async def ingest_knowledge_base_task(
    ctx: dict[str, Any],
    knowledge_base: str,
) -> dict[str, Any]:
    logger.info(
        "ingest_task_started",
        knowledge_base=knowledge_base,
        job_id=ctx.get("job_id"),
    )

    try:
        chroma_repo = ChromaRepository()
        docstore = RedisDocStore(redis_url=settings.redis_url)
        chunking_service = ChunkingService()
        embedding_model = get_embedding_model(settings)

        service = IngestionService(
            chroma_repo=chroma_repo,
            docstore=docstore,
            chunking_service=chunking_service,
            embedding_model=embedding_model,
        )

        await service.ingest_knowledge_base(
            knowledge_base=knowledge_base,
            data_dir=settings.data_dir,
        )

        logger.info(
            "ingest_task_completed",
            knowledge_base=knowledge_base,
        )
        return {
            "status": "success",
            "knowledge_base": knowledge_base,
        }
    except Exception as exc:
        logger.error(
            "ingest_task_failed",
            error=str(exc),
            knowledge_base=knowledge_base,
            job_id=ctx.get("job_id"),
        )
        return {
            "status": "failed",
            "error": str(exc),
            "knowledge_base": knowledge_base,
        }


async def evaluate_conversation_task(
    ctx: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    logger.info(
        "evaluate_task_started", session_id=session_id, job_id=ctx.get("job_id")
    )

    try:
        async with async_session_factory() as session:
            service = EvaluationService(session=session)
            result = await service.evaluate_conversation(session_id)

        metrics = {
            "faithfulness": float(result.faithfulness),
            "answer_relevancy": float(result.answer_relevancy),
            "context_precision": float(result.context_precision),
            "context_recall": float(result.context_recall),
        }
        logger.info(
            "evaluate_task_completed",
            session_id=session_id,
            metrics=metrics,
            job_id=ctx.get("job_id"),
        )
        return {
            "status": "success",
            "session_id": session_id,
            "metrics": metrics,
        }
    except Exception as exc:
        logger.error(
            "evaluate_task_failed",
            session_id=session_id,
            error=str(exc),
            job_id=ctx.get("job_id"),
        )
        return {
            "status": "failed",
            "session_id": session_id,
            "error": str(exc),
        }
