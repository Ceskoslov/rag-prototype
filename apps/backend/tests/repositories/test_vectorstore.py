from collections.abc import Mapping, Sequence
from typing import Protocol, TypeAlias, cast

import chromadb
import pytest

from app.repositories.vectorstore import ChromaCollection, ChromaRepository


MetadataPrimitive: TypeAlias = str | int | float | bool
MetadataMap: TypeAlias = Mapping[str, MetadataPrimitive]
DocItem: TypeAlias = Mapping[str, object]
BatchTuple: TypeAlias = tuple[list[str], object | None, list[MetadataMap], list[str]]


class SupportsCount(Protocol):
    def count(self) -> int: ...


def test_create_collection_creates_collection() -> None:
    client = chromadb.Client()
    repository = ChromaRepository(client=client)

    collection = repository.create_collection("it_support", metadata={"owner": "qa"})

    assert collection.name == "it_support_knowledge_base"
    assert repository.get_collection("it_support").name == "it_support_knowledge_base"


def test_add_documents_adds_documents_in_batches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = chromadb.Client()
    repository = ChromaRepository(client=client)
    collection = repository.create_collection("legal")

    calls: list[int] = []

    def fake_create_batches(
        *,
        api: object,
        ids: list[str],
        metadatas: list[MetadataMap],
        documents: list[str],
        embeddings: Sequence[object] | None = None,
    ) -> list[BatchTuple]:
        _ = api
        calls.append(len(ids))
        return [
            (
                ids[i : i + 25],
                embeddings[i : i + 25] if embeddings else None,
                metadatas[i : i + 25],
                documents[i : i + 25],
            )
            for i in range(0, len(ids), 25)
        ]

    monkeypatch.setattr(
        "app.repositories.vectorstore.create_batches", fake_create_batches
    )

    docs: list[DocItem] = [
        cast(
            DocItem,
            {"id": f"doc-{i}", "document": f"policy {i}", "metadata": {"idx": i}},
        )
        for i in range(100)
    ]

    repository.add_documents(collection=collection, docs=docs)

    assert calls == [100]
    assert cast(SupportsCount, cast(object, collection)).count() == 100


def test_similarity_search_returns_k_results() -> None:
    client = chromadb.Client()
    repository = ChromaRepository(client=client)
    collection = repository.create_collection("credit_card")

    docs: list[DocItem] = [
        cast(
            DocItem,
            {
                "id": "cc-1",
                "document": "credit card late fee policy details",
                "metadata": {"source": "policy"},
            },
        ),
        cast(
            DocItem,
            {
                "id": "cc-2",
                "document": "card replacement process and shipping",
                "metadata": {"source": "ops"},
            },
        ),
        cast(
            DocItem,
            {
                "id": "cc-3",
                "document": "reward points accrual and redemption",
                "metadata": {"source": "rewards"},
            },
        ),
    ]
    repository.add_documents(collection=collection, docs=docs)

    results = repository.similarity_search(
        collection=collection,
        query="How do late fees work for my card?",
        k=2,
    )

    assert len(results) == 2
    assert all("id" in item and "document" in item for item in results)


def test_delete_collection_removes_collection() -> None:
    client = chromadb.Client()
    repository = ChromaRepository(client=client)
    _ = repository.create_collection("airport_ground")

    repository.delete_collection("airport_ground")

    with pytest.raises(Exception):
        _ = repository.get_collection("airport_ground")


def test_add_documents_uses_create_batches_for_large_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = chromadb.Client()
    repository = ChromaRepository(client=client)

    class FakeCollection:
        name: str = "fake"

        def __init__(self) -> None:
            self.add_calls: list[int] = []

        def add(
            self,
            *,
            ids: Sequence[str],
            metadatas: Sequence[MetadataMap],
            documents: Sequence[str],
            embeddings: object | None = None,
        ) -> None:
            _ = metadatas
            _ = documents
            _ = embeddings
            self.add_calls.append(len(ids))

    collection = FakeCollection()

    observed_batch_sizes: list[int] = []

    def fake_create_batches(
        *,
        api: object,
        ids: list[str],
        metadatas: list[MetadataMap],
        documents: list[str],
        embeddings: Sequence[object] | None = None,
    ) -> list[BatchTuple]:
        _ = api
        max_size = 41666
        batches: list[BatchTuple] = []
        for i in range(0, len(ids), max_size):
            chunk_ids = ids[i : i + max_size]
            observed_batch_sizes.append(len(chunk_ids))
            batches.append(
                (
                    chunk_ids,
                    embeddings[i : i + max_size] if embeddings else None,
                    metadatas[i : i + max_size],
                    documents[i : i + max_size],
                )
            )
        return batches

    monkeypatch.setattr(
        "app.repositories.vectorstore.create_batches", fake_create_batches
    )

    docs: list[DocItem] = [
        cast(DocItem, {"id": f"bulk-{i}", "document": "d", "metadata": {"i": i}})
        for i in range(42000)
    ]

    repository.add_documents(
        collection=cast(ChromaCollection, cast(object, collection)),
        docs=docs,
    )

    assert observed_batch_sizes == [41666, 334]
    assert collection.add_calls == [41666, 334]


def test_production_client_uses_http_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyClient:
        pass

    captured: dict[str, object] = {}

    def fake_http_client(*, host: str, port: int) -> DummyClient:
        captured["host"] = host
        captured["port"] = port
        return DummyClient()

    monkeypatch.setattr(
        "app.repositories.vectorstore.chromadb.HttpClient", fake_http_client
    )
    repository = ChromaRepository()

    assert isinstance(repository.client, DummyClient)
    assert captured == {"host": "chromadb", "port": 8000}
