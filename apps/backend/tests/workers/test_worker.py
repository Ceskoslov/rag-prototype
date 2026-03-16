"""ARQ Worker and Background Task Tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from arq import ArqRedis
from arq.connections import RedisSettings


class TestWorkerSettings:
    """Test ARQ WorkerSettings configuration."""

    def test_worker_settings_configured(self) -> None:
        from app.workers.worker import WorkerSettings

        assert WorkerSettings.max_jobs == 5
        assert WorkerSettings.job_timeout == 300
        assert WorkerSettings.keep_result == 3600
        assert isinstance(WorkerSettings.redis_settings, RedisSettings)

    def test_worker_registers_functions(self) -> None:
        from app.workers.worker import WorkerSettings

        function_names = [f.__name__ for f in WorkerSettings.functions]
        assert "ingest_department_task" in function_names
        assert "evaluate_conversation_task" in function_names
        assert len(function_names) >= 2


@pytest.mark.asyncio
class TestIngestDepartmentTask:
    """Test ingest_department_task background task."""

    async def test_ingest_department_task_calls_service(self) -> None:
        from app.workers.tasks import ingest_department_task

        mock_service = AsyncMock()
        mock_service.ingest_department.return_value = None

        with patch("app.workers.tasks.ChromaRepository"):
            with patch("app.workers.tasks.RedisDocStore"):
                with patch("app.workers.tasks.ChunkingService"):
                    with patch("app.workers.tasks.get_embedding_model"):
                        with patch("app.workers.tasks.IngestionService") as MockService:
                            MockService.return_value = mock_service

                            ctx: dict[str, Any] = {"job_id": "test-job-123"}
                            result = await ingest_department_task(ctx, "it_support")

                            assert result["status"] == "success"
                            assert result["department"] == "it_support"

                            mock_service.ingest_department.assert_called_once()

    async def test_ingest_department_task_invalid_department(self) -> None:
        from app.workers.tasks import ingest_department_task

        ctx: dict[str, Any] = {"job_id": "test-job-456"}
        result = await ingest_department_task(ctx, "invalid_dept")

        assert result["status"] == "failed"
        assert "Invalid department" in result["error"]

    async def test_ingest_department_task_handles_errors(self) -> None:
        from app.workers.tasks import ingest_department_task

        mock_service = AsyncMock()
        mock_service.ingest_department.side_effect = Exception("Connection failed")

        with patch("app.workers.tasks.ChromaRepository"):
            with patch("app.workers.tasks.RedisDocStore"):
                with patch("app.workers.tasks.ChunkingService"):
                    with patch("app.workers.tasks.get_embedding_model"):
                        with patch("app.workers.tasks.IngestionService") as MockService:
                            MockService.return_value = mock_service

                            ctx: dict[str, Any] = {"job_id": "test-job-789"}
                            result = await ingest_department_task(ctx, "it_support")

                            assert result["status"] == "failed"
                            assert "Connection failed" in result["error"]
                            assert result["department"] == "it_support"


@pytest.mark.asyncio
class TestEvaluateConversationTask:
    """Test evaluate_conversation_task background task."""

    async def test_evaluate_conversation_task_placeholder(self) -> None:
        from app.workers.tasks import evaluate_conversation_task

        ctx: dict[str, Any] = {"job_id": "eval-job-001"}
        result = await evaluate_conversation_task(ctx, "session-123")

        assert result["status"] == "not_implemented"
        assert result["session_id"] == "session-123"
        assert "not yet implemented" in result["message"].lower()


@pytest.mark.asyncio
class TestWorkerLifecycle:
    """Test ARQ worker startup/shutdown hooks."""

    async def test_worker_startup_hook(self) -> None:
        from app.workers.worker import WorkerSettings

        ctx: dict[str, Any] = {}
        await WorkerSettings.on_startup(ctx)

    async def test_worker_shutdown_hook(self) -> None:
        from app.workers.worker import WorkerSettings

        ctx: dict[str, Any] = {}
        await WorkerSettings.on_shutdown(ctx)
