import chromadb
import pytest

from app.core.settings import settings
from app.repositories.vectorstore import ChromaRepository


def test_vectorstore_supports_dynamic_knowledge_bases_and_explicit_embeddings():
    repository = ChromaRepository(client=chromadb.EphemeralClient())
    collection = repository.create_collection("Product Docs")
    repository.upsert_documents(
        collection,
        docs=[
            {
                "id": "one",
                "document": "The refund window is 30 days.",
                "metadata": {
                    "knowledge_base": "product_docs",
                    "source_path": "refunds.md",
                },
            }
        ],
        embeddings=[[1.0, 0.0, 0.0]],
    )

    results = repository.similarity_search(
        collection,
        query_embedding=[1.0, 0.0, 0.0],
        k=3,
    )

    assert repository.list_knowledge_bases() == ["product_docs"]
    assert results[0]["id"] == "one"


def test_vectorstore_creates_chroma_cloud_client(monkeypatch):
    cloud_client = object()
    calls = []

    def fake_cloud_client(**kwargs):
        calls.append(kwargs)
        return cloud_client

    monkeypatch.setattr(chromadb, "CloudClient", fake_cloud_client)
    monkeypatch.setattr(settings, "chroma_provider", "cloud")
    monkeypatch.setattr(settings, "chroma_tenant", "tenant-id")
    monkeypatch.setattr(settings, "chroma_database", "database-name")
    monkeypatch.setattr(settings, "chroma_api_key", "secret")
    monkeypatch.setattr(settings, "chroma_cloud_host", "api.trychroma.com")

    repository = ChromaRepository()

    assert repository.client is cloud_client
    assert calls == [
        {
            "tenant": "tenant-id",
            "database": "database-name",
            "api_key": "secret",
            "cloud_host": "api.trychroma.com",
        }
    ]


def test_vectorstore_requires_all_chroma_cloud_credentials(monkeypatch):
    monkeypatch.setattr(settings, "chroma_provider", "cloud")
    monkeypatch.setattr(settings, "chroma_tenant", None)
    monkeypatch.setattr(settings, "chroma_database", None)
    monkeypatch.setattr(settings, "chroma_api_key", None)

    with pytest.raises(ValueError, match="CHROMA_TENANT"):
        ChromaRepository()
