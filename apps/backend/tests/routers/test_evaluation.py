from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.middleware.auth import verify_api_key
from app.models.conversation import Conversation
from app.models.evaluation import EvaluationResult


@pytest.fixture
def app_with_evaluation_router() -> FastAPI:
    from app.routers import evaluation as evaluation_router

    app = FastAPI(dependencies=[Depends(verify_api_key)])
    app.include_router(evaluation_router.router)
    return app


@pytest.mark.asyncio
async def test_trigger_evaluation_enqueues_job_and_returns_job_id(
    app_with_evaluation_router: FastAPI,
    async_session_factory_test,
) -> None:
    from app.routers import evaluation as evaluation_router

    async def override_get_db():
        async with async_session_factory_test() as session:
            yield session

    app_with_evaluation_router.dependency_overrides[evaluation_router.get_db] = (
        override_get_db
    )

    async with async_session_factory_test() as session:
        session.add(Conversation(session_id="eval-session-1", knowledge_base="it_support"))
        await session.commit()

    with patch("app.routers.evaluation.arq.create_pool") as mock_create_pool:
        mock_pool = AsyncMock()
        mock_job = MagicMock()
        mock_job.job_id = "job-123"
        mock_pool.enqueue_job.return_value = mock_job
        mock_create_pool.return_value = mock_pool

        transport = ASGITransport(app=app_with_evaluation_router)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/evaluation/trigger",
                json={"session_id": "eval-session-1"},
                headers={"X-API-Key": "test-api-key-12345"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == "job-123"
    assert body["session_id"] == "eval-session-1"


@pytest.mark.asyncio
async def test_get_evaluation_results_returns_stored_metrics(
    app_with_evaluation_router: FastAPI,
    async_session_factory_test,
) -> None:
    from app.routers import evaluation as evaluation_router

    async def override_get_db():
        async with async_session_factory_test() as session:
            yield session

    app_with_evaluation_router.dependency_overrides[evaluation_router.get_db] = (
        override_get_db
    )

    async with async_session_factory_test() as session:
        conversation = Conversation(
            session_id="eval-session-2", knowledge_base="it_support"
        )
        session.add(conversation)
        await session.flush()
        session.add(
            EvaluationResult(
                conversation_id=conversation.id,
                faithfulness=0.81,
                answer_relevancy=0.88,
                context_precision=0.77,
                context_recall=0.79,
            )
        )
        await session.commit()

    transport = ASGITransport(app=app_with_evaluation_router)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/evaluation/results/eval-session-2",
            headers={"X-API-Key": "test-api-key-12345"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "eval-session-2"
    assert body["faithfulness"] == pytest.approx(0.81)
    assert body["answer_relevancy"] == pytest.approx(0.88)
    assert body["context_precision"] == pytest.approx(0.77)
    assert body["context_recall"] == pytest.approx(0.79)


@pytest.mark.asyncio
async def test_get_evaluation_status_returns_job_status(
    app_with_evaluation_router: FastAPI,
    async_session_factory_test,
) -> None:
    from app.routers import evaluation as evaluation_router

    async def override_get_db():
        async with async_session_factory_test() as session:
            yield session

    app_with_evaluation_router.dependency_overrides[evaluation_router.get_db] = (
        override_get_db
    )

    async with async_session_factory_test() as session:
        session.add(Conversation(session_id="eval-session-3", knowledge_base="it_support"))
        await session.commit()

    with patch("app.routers.evaluation.arq.create_pool") as mock_create_pool:
        mock_pool = AsyncMock()
        mock_status_job = AsyncMock()
        mock_status_job.status.return_value = "complete"
        mock_create_pool.return_value = mock_pool

        with patch("app.routers.evaluation.Job", return_value=mock_status_job):
            transport = ASGITransport(app=app_with_evaluation_router)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/v1/evaluation/results/eval-session-3/status",
                    headers={"X-API-Key": "test-api-key-12345"},
                )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "eval-session-3"
    assert body["status"] == "complete"


@pytest.mark.asyncio
async def test_get_evaluation_results_404_when_not_found(
    app_with_evaluation_router: FastAPI,
    async_session_factory_test,
) -> None:
    from app.routers import evaluation as evaluation_router

    async def override_get_db():
        async with async_session_factory_test() as session:
            yield session

    app_with_evaluation_router.dependency_overrides[evaluation_router.get_db] = (
        override_get_db
    )

    transport = ASGITransport(app=app_with_evaluation_router)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/evaluation/results/non-existent-session",
            headers={"X-API-Key": "test-api-key-12345"},
        )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
