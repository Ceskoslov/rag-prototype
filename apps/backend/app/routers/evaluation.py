from __future__ import annotations

from typing import Any

import arq
from arq.connections import RedisSettings
from arq.jobs import Job
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.settings import settings
from app.middleware.auth import verify_api_key
from app.models.conversation import Conversation
from app.models.evaluation import EvaluationResult
from app.schemas.evaluation import (
    EvaluationResultResponse,
    EvaluationStatusResponse,
    EvaluationTriggerRequest,
    EvaluationTriggerResponse,
)

router = APIRouter(
    prefix="/api/v1/evaluation",
    tags=["evaluation"],
    dependencies=[Depends(verify_api_key)],
)


async def get_db() -> Any:
    async for session in get_async_session():
        yield session


def _arq_redis_url() -> str:
    if settings.arq_redis_url:
        return settings.arq_redis_url
    return settings.redis_url.rsplit("/", 1)[0] + "/1"


@router.post("/trigger", response_model=EvaluationTriggerResponse)
async def trigger_evaluation(
    request: EvaluationTriggerRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationTriggerResponse:
    conversation = (
        await db.execute(
            select(Conversation).where(Conversation.session_id == request.session_id)
        )
    ).scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    pool = None
    try:
        pool = await arq.create_pool(RedisSettings.from_dsn(_arq_redis_url()))
        job = await pool.enqueue_job(
            "evaluate_conversation_task",
            session_id=request.session_id,
            references=request.references,
            _job_id=f"evaluation:{request.session_id}",
        )
        if job is None:
            raise HTTPException(status_code=500, detail="Failed to enqueue evaluation")
        return EvaluationTriggerResponse(
            job_id=str(job.job_id),
            session_id=request.session_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"ARQ enqueue failed: {exc}"
        ) from exc
    finally:
        if pool is not None:
            await pool.close()


@router.get("/results/{session_id}", response_model=EvaluationResultResponse)
async def get_evaluation_results(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResultResponse:
    conversation = (
        await db.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
    ).scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = (
        (
            await db.execute(
                select(EvaluationResult)
                .where(EvaluationResult.conversation_id == conversation.id)
                .order_by(desc(EvaluationResult.id))
            )
        )
        .scalars()
        .first()
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Evaluation result not found")

    return EvaluationResultResponse(
        session_id=session_id,
        faithfulness=float(result.faithfulness),
        answer_relevancy=float(result.answer_relevancy),
        context_precision=float(result.context_precision),
        context_recall=float(result.context_recall)
        if result.context_recall is not None
        else None,
        details=result.details,
        created_at=result.created_at,
    )


@router.get("/results/{session_id}/status", response_model=EvaluationStatusResponse)
async def get_evaluation_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> EvaluationStatusResponse:
    conversation = (
        await db.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
    ).scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    existing = (
        (
            await db.execute(
                select(EvaluationResult)
                .where(EvaluationResult.conversation_id == conversation.id)
                .order_by(desc(EvaluationResult.id))
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return EvaluationStatusResponse(
            session_id=session_id,
            status="complete",
            job_id=f"evaluation:{session_id}",
        )

    pool = None
    try:
        pool = await arq.create_pool(RedisSettings.from_dsn(_arq_redis_url()))
        job = Job(f"evaluation:{session_id}", pool)
        job_status = await job.status()
        status_value = getattr(job_status, "value", str(job_status))
        if status_value in {"queued", "in_progress", "deferred"}:
            mapped = "pending"
        elif status_value == "complete":
            mapped = "complete"
        elif status_value == "not_found":
            mapped = "failed"
        else:
            mapped = status_value
        return EvaluationStatusResponse(
            session_id=session_id,
            status=mapped,
            job_id=f"evaluation:{session_id}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"ARQ status failed: {exc}"
        ) from exc
    finally:
        if pool is not None:
            await pool.close()
