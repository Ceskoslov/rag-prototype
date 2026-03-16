"""Seed Service Tests (TDD)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from arq.jobs import JobStatus


@pytest.mark.asyncio
class TestSeedService:
    """Test SeedService seed_all_departments and check_seed_status."""

    async def test_seed_all_departments_enqueues_jobs_when_empty(self) -> None:
        """Test seed_all_departments enqueues jobs for empty collections."""
        from app.services.seed import SeedService
        from app.repositories.vectorstore import ChromaRepository

        mock_chroma_repo = MagicMock()
        mock_chroma_repo._collection_name = ChromaRepository._collection_name
        mock_chroma_repo.get_collection_count.return_value = 0

        mock_pool = AsyncMock()
        mock_job = AsyncMock()
        mock_pool.enqueue.return_value = mock_job

        with patch("app.services.seed.arq.create_pool") as mock_create_pool:
            mock_create_pool.return_value = mock_pool

            service = SeedService(
                chroma_repo=mock_chroma_repo, redis_url="redis://localhost:6379/0"
            )
            result = await service.seed_all_departments()

            assert mock_pool.enqueue.call_count == 4
            assert result == {
                "it_support": "seeded",
                "legal": "seeded",
                "credit_card": "seeded",
                "airport_ground": "seeded",
            }

            mock_pool.close.assert_called_once_with(close_connection=True)

    async def test_seed_all_departments_skips_populated_departments(self) -> None:
        """Test seed_all_departments skips departments with existing documents (idempotent)."""
        from app.services.seed import SeedService
        from app.repositories.vectorstore import ChromaRepository

        mock_chroma_repo = MagicMock()
        mock_chroma_repo._collection_name = ChromaRepository._collection_name

        def mock_get_count(collection_name: str) -> int:
            if collection_name in ["it_support_knowledge_base", "legal_knowledge_base"]:
                return 10
            return 0

        mock_chroma_repo.get_collection_count.side_effect = mock_get_count

        mock_pool = AsyncMock()
        mock_job = AsyncMock()
        mock_pool.enqueue.return_value = mock_job

        with patch("app.services.seed.arq.create_pool") as mock_create_pool:
            mock_create_pool.return_value = mock_pool

            service = SeedService(
                chroma_repo=mock_chroma_repo, redis_url="redis://localhost:6379/0"
            )
            result = await service.seed_all_departments()

            assert mock_pool.enqueue.call_count == 2

            enqueued_depts = [call[0][0] for call in mock_pool.enqueue.call_args_list]
            assert "ingest_department_task" in str(mock_pool.enqueue.call_args_list)
            assert "credit_card" in str(mock_pool.enqueue.call_args_list)
            assert "airport_ground" in str(mock_pool.enqueue.call_args_list)

            assert result == {
                "it_support": "skipped",
                "legal": "skipped",
                "credit_card": "seeded",
                "airport_ground": "seeded",
            }

            mock_pool.close.assert_called_once_with(close_connection=True)

    async def test_check_seed_status_returns_document_counts(self) -> None:
        """Test check_seed_status returns document counts per department."""
        from app.services.seed import SeedService
        from app.repositories.vectorstore import ChromaRepository

        mock_chroma_repo = MagicMock()
        mock_chroma_repo._collection_name = ChromaRepository._collection_name

        def mock_get_count(collection_name: str) -> int:
            counts = {
                "it_support_knowledge_base": 8,
                "legal_knowledge_base": 12,
                "credit_card_knowledge_base": 0,
                "airport_ground_knowledge_base": 12,
            }
            return counts.get(collection_name, 0)

        mock_chroma_repo.get_collection_count.side_effect = mock_get_count

        service = SeedService(
            chroma_repo=mock_chroma_repo, redis_url="redis://localhost:6379/1"
        )
        status = await service.check_seed_status()

        assert status == {
            "it_support": 8,
            "legal": 12,
            "credit_card": 0,
            "airport_ground": 12,
        }

        assert mock_chroma_repo.get_collection_count.call_count == 4

    async def test_seed_all_departments_handles_arq_errors(self) -> None:
        """Test seed_all_departments handles ARQ connection errors gracefully."""
        from app.services.seed import SeedService
        from app.repositories.vectorstore import ChromaRepository

        mock_chroma_repo = MagicMock()
        mock_chroma_repo._collection_name = ChromaRepository._collection_name
        mock_chroma_repo.get_collection_count.return_value = 0

        with patch("app.services.seed.arq.create_pool") as mock_create_pool:
            mock_create_pool.side_effect = Exception("Redis connection failed")

            service = SeedService(
                chroma_repo=mock_chroma_repo, redis_url="redis://localhost:6379/0"
            )

            with pytest.raises(Exception, match="Redis connection failed"):
                await service.seed_all_departments()
