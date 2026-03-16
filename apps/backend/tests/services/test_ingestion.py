"""Tests for the document ingestion service (TDD RED phase)."""

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fakeredis import FakeRedis
from langchain_core.documents import Document

from app.schemas.common import Department
from app.services.ingestion import IngestionService


@pytest.fixture
def fake_redis():
    """Provide a fake Redis client for testing."""
    return FakeRedis(decode_responses=True)


@pytest.fixture
def mock_chroma_repo():
    """Mock ChromaDB repository."""
    repo = Mock()
    repo.create_collection = Mock(return_value=Mock(name="it_support_knowledge_base"))
    repo.add_documents = Mock()
    return repo


@pytest.fixture
def mock_docstore(fake_redis):
    """Mock RedisDocStore."""
    store = Mock()
    store.client = fake_redis
    store.mset = Mock()
    store._make_key = lambda key: f"docstore:{key}"
    return store


@pytest.fixture
def mock_chunking_service():
    """Mock ChunkingService."""
    service = Mock()

    def chunk_document(doc: Document) -> list[Document]:
        """Mock chunking: returns 1 parent + 2 child chunks."""
        parent_id = "parent_test123"
        return [
            Document(
                id=parent_id,
                page_content="Parent chunk content",
                metadata={
                    "department": doc.metadata.get("department"),
                    "source_file": doc.metadata.get("source_file"),
                    "chunk_type": "parent",
                    "chunk_index": 0,
                },
            ),
            Document(
                id="child_test456",
                page_content="Child chunk 1",
                metadata={
                    "department": doc.metadata.get("department"),
                    "source_file": doc.metadata.get("source_file"),
                    "chunk_type": "child",
                    "chunk_index": 0,
                    "parent_id": parent_id,
                },
            ),
            Document(
                id="child_test789",
                page_content="Child chunk 2",
                metadata={
                    "department": doc.metadata.get("department"),
                    "source_file": doc.metadata.get("source_file"),
                    "chunk_type": "child",
                    "chunk_index": 1,
                    "parent_id": parent_id,
                },
            ),
        ]

    service.chunk_document = Mock(side_effect=chunk_document)
    return service


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model."""
    return Mock()


@pytest.fixture
def ingestion_service(
    mock_chroma_repo,
    mock_docstore,
    mock_chunking_service,
    mock_embedding_model,
):
    """Create IngestionService with mocked dependencies."""
    return IngestionService(
        chroma_repo=mock_chroma_repo,
        docstore=mock_docstore,
        chunking_service=mock_chunking_service,
        embedding_model=mock_embedding_model,
    )


@pytest.fixture
def sample_markdown_file(tmp_path: Path) -> Path:
    """Create a sample markdown file for testing."""
    content = """---
department: IT Support
last_updated: 2026-01-15
category: Connectivity
audience: All Employees
---

# VPN Setup Guide

## Installation Steps
Download the VPN client from the internal portal.

## Configuration
Enter the server address when prompted.
"""
    dept_dir = tmp_path / "it_support"
    dept_dir.mkdir()
    file_path = dept_dir / "vpn-setup.md"
    file_path.write_text(content)
    return file_path


@pytest.mark.asyncio
async def test_ingest_department_processes_all_md_files(
    ingestion_service: IngestionService,
    tmp_path: Path,
):
    """Test that ingest_department processes all .md files in directory."""
    # Create test department directory with 2 markdown files
    dept_dir = tmp_path / "it_support"
    dept_dir.mkdir()

    file1 = dept_dir / "vpn-setup.md"
    file1.write_text("# VPN Setup\nContent 1")

    file2 = dept_dir / "password-reset.md"
    file2.write_text("# Password Reset\nContent 2")

    # Ingest the department
    await ingestion_service.ingest_department(
        department=Department.IT_SUPPORT,
        data_dir=tmp_path,
    )

    # Assert: chunking service called 2 times (once per file)
    assert ingestion_service.chunking_service.chunk_document.call_count == 2

    # Assert: ChromaDB add_documents called at least once
    assert ingestion_service.chroma_repo.add_documents.call_count >= 1


@pytest.mark.asyncio
async def test_child_chunks_stored_in_chromadb(
    ingestion_service: IngestionService,
    sample_markdown_file: Path,
):
    """Test that child chunks are stored in ChromaDB with correct metadata."""
    dept_dir = sample_markdown_file.parent

    await ingestion_service.ingest_department(
        department=Department.IT_SUPPORT,
        data_dir=dept_dir.parent,
    )

    ingestion_service.chroma_repo.add_documents.assert_called()
    call_args = ingestion_service.chroma_repo.add_documents.call_args

    docs = call_args[0][1]

    child_docs = [d for d in docs if d["metadata"]["chunk_type"] == "child"]
    assert len(child_docs) >= 2

    for doc in child_docs:
        assert doc["metadata"]["department"] == "it_support"
        assert doc["metadata"]["source_file"] == "vpn-setup.md"
        assert "parent_id" in doc["metadata"]


@pytest.mark.asyncio
async def test_parent_chunks_stored_in_redis(
    ingestion_service: IngestionService,
    sample_markdown_file: Path,
):
    """Test that parent chunks are stored in Redis docstore."""
    dept_dir = sample_markdown_file.parent

    await ingestion_service.ingest_department(
        department=Department.IT_SUPPORT,
        data_dir=dept_dir.parent,
    )

    ingestion_service.docstore.mset.assert_called()
    call_args = ingestion_service.docstore.mset.call_args

    key_value_pairs = call_args[0][0]

    assert len(key_value_pairs) >= 1

    for key, doc in key_value_pairs:
        assert "it_support" in key
        assert doc.metadata["chunk_type"] == "parent"


@pytest.mark.asyncio
async def test_idempotent_ingestion_no_duplicates(
    ingestion_service: IngestionService,
    sample_markdown_file: Path,
    fake_redis,
):
    """Test that re-ingesting the same file doesn't create duplicates."""
    dept_dir = sample_markdown_file.parent

    ingestion_service.docstore.client = fake_redis

    content = sample_markdown_file.read_text()
    file_hash = hashlib.md5(content.encode()).hexdigest()

    await ingestion_service.ingest_department(
        department=Department.IT_SUPPORT,
        data_dir=dept_dir.parent,
    )

    first_call_count = ingestion_service.chroma_repo.add_documents.call_count

    hash_key = f"ingested_files:it_support:vpn-setup.md"
    fake_redis.set(hash_key, file_hash)

    await ingestion_service.ingest_department(
        department=Department.IT_SUPPORT,
        data_dir=dept_dir.parent,
    )

    second_call_count = ingestion_service.chroma_repo.add_documents.call_count

    assert second_call_count == first_call_count


@pytest.mark.asyncio
async def test_metadata_correctness(
    ingestion_service: IngestionService,
    sample_markdown_file: Path,
):
    """Test that all chunks have correct metadata fields."""
    dept_dir = sample_markdown_file.parent

    await ingestion_service.ingest_department(
        department=Department.IT_SUPPORT,
        data_dir=dept_dir.parent,
    )

    call_args = ingestion_service.chroma_repo.add_documents.call_args
    docs = call_args[0][1]

    for doc in docs:
        metadata = doc["metadata"]

        assert "department" in metadata
        assert "source_file" in metadata
        assert "chunk_type" in metadata
        assert "chunk_index" in metadata

        if metadata["chunk_type"] == "child":
            assert "parent_id" in metadata


@pytest.mark.asyncio
async def test_empty_directory_no_errors(
    ingestion_service: IngestionService,
    tmp_path: Path,
):
    """Test that ingesting an empty directory doesn't raise errors."""
    dept_dir = tmp_path / "it_support"
    dept_dir.mkdir()

    await ingestion_service.ingest_department(
        department=Department.IT_SUPPORT,
        data_dir=tmp_path,
    )

    assert ingestion_service.chroma_repo.add_documents.call_count == 0
