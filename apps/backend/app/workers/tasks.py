"""Background task implementations for ARQ worker."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.database import async_session_factory
from app.core.docstore import RedisDocStore
from app.core.embeddings import get_embedding_model
from app.core.logging import get_logger
from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository
from app.schemas.common import Department
from app.services.chunking import ChunkingService
from app.services.evaluation import EvaluationService
from app.services.ingestion import IngestionService

logger = get_logger(__name__)


async def ingest_department_task(
    ctx: dict[str, Any],
    department: str,
) -> dict[str, Any]:
    logger.info("ingest_task_started", department=department, job_id=ctx.get("job_id"))

    try:
        dept_enum = Department(department)
    except ValueError:
        error_msg = f"Invalid department: {department}"
        logger.error("ingest_task_failed", error=error_msg, department=department)
        return {"status": "failed", "error": error_msg}

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

        data_dir = Path("data")
        await service.ingest_department(department=dept_enum, data_dir=data_dir)

        logger.info(
            "ingest_task_completed",
            department=department,
        )
        return {
            "status": "success",
            "department": department,
        }
    except Exception as exc:
        logger.error(
            "ingest_task_failed",
            error=str(exc),
            department=department,
            job_id=ctx.get("job_id"),
        )
        return {"status": "failed", "error": str(exc), "department": department}


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
