from types import SimpleNamespace
from unittest.mock import AsyncMock

import chromadb
import pytest
from fakeredis import FakeRedis
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.docstore import RedisDocStore
from app.repositories.vectorstore import ChromaRepository
from app.routers import knowledge_bases
from app.services.documents import DocumentService


@pytest.fixture
def document_client(tmp_path):
    service = DocumentService(
        tmp_path / "data",
        ChromaRepository(chromadb.PersistentClient(path=str(tmp_path / "chroma"))),
        RedisDocStore(redis_client=FakeRedis(decode_responses=True)),
    )
    pool = SimpleNamespace(
        enqueue_job=AsyncMock(return_value=SimpleNamespace(job_id="job-1"))
    )
    app = FastAPI()
    app.include_router(knowledge_bases.router)
    app.dependency_overrides[knowledge_bases.get_document_service] = lambda: service
    app.dependency_overrides[knowledge_bases.get_job_pool] = lambda: pool
    return TestClient(app), service, pool


def test_upload_list_download_and_delete(document_client):
    client, _service, pool = document_client
    url = "/api/v1/knowledge-bases/policies/documents/refund.md"
    assert client.put(url, content=b"Refunds within 30 days").status_code == 202
    assert pool.enqueue_job.call_args.args[:2] == (
        "ingest_knowledge_base_task",
        "policies",
    )
    assert client.get(url).content == b"Refunds within 30 days"
    assert (
        client.get("/api/v1/knowledge-bases/policies/documents").json()[0]["indexed"]
        is False
    )
    assert client.delete(url).status_code == 202
    assert client.get(url).status_code == 404


def test_document_service_rejects_path_traversal_and_symlinks(
    document_client, tmp_path
):
    _client, service, _pool = document_client
    with pytest.raises(ValueError, match="Invalid document"):
        service.write("policies", "../outside.md", b"content")
    base = service.data_dir / "policies"
    base.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("secret")
    (base / "link.md").symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        service.file_path("policies", "link.md")


def test_active_indexing_blocks_file_mutation(document_client):
    client, service, _pool = document_client
    lock = service.store.client.lock("ingest_lock:policies", timeout=60)
    lock.acquire(blocking=False)
    assert (
        client.put(
            "/api/v1/knowledge-bases/policies/documents/a.md", content=b"hello"
        ).status_code
        == 409
    )
    lock.release()
