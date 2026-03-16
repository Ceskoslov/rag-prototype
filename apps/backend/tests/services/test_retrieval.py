from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, cast

import chromadb
import pytest
from fakeredis import FakeRedis
from langchain_core.documents import Document

from app.core.docstore import RedisDocStore
from app.repositories.vectorstore import ChromaCollection, ChromaRepository
from app.schemas.common import Department
from app.services.retrieval import HybridRetriever


@pytest.fixture
def vector_repository() -> ChromaRepository:
    client = chromadb.Client()
    repository = ChromaRepository(client=client)

    it_collection = repository.create_collection(Department.IT_SUPPORT.value)
    legal_collection = repository.create_collection(Department.LEGAL.value)

    repository.add_documents(
        it_collection,
        [
            {
                "id": "it-child-1",
                "document": "VPN password reset requires identity verification",
                "metadata": {
                    "department": Department.IT_SUPPORT.value,
                    "chunk_type": "child",
                    "parent_id": "it-parent-1",
                },
            },
            {
                "id": "it-child-2",
                "document": "Reset MFA tokens from employee self-service portal",
                "metadata": {
                    "department": Department.IT_SUPPORT.value,
                    "chunk_type": "child",
                    "parent_id": "it-parent-2",
                },
            },
        ],
    )

    repository.add_documents(
        legal_collection,
        [
            {
                "id": "legal-child-1",
                "document": "Contract indemnification clauses and limitations",
                "metadata": {
                    "department": Department.LEGAL.value,
                    "chunk_type": "child",
                    "parent_id": "legal-parent-1",
                },
            }
        ],
    )
    return repository


@pytest.fixture
def docstore() -> RedisDocStore:
    fake_redis = FakeRedis(decode_responses=True)
    store = RedisDocStore(redis_client=fake_redis, prefix="docstore:test")
    store.mset(
        [
            (
                "it-parent-1",
                Document(
                    page_content="Parent IT runbook for VPN password reset.",
                    metadata={
                        "department": Department.IT_SUPPORT.value,
                        "chunk_type": "parent",
                    },
                ),
            ),
            (
                "it-parent-2",
                Document(
                    page_content="Parent IT runbook for MFA reset process.",
                    metadata={
                        "department": Department.IT_SUPPORT.value,
                        "chunk_type": "parent",
                    },
                ),
            ),
            (
                "legal-parent-1",
                Document(
                    page_content="Parent legal guidance for indemnification review.",
                    metadata={
                        "department": Department.LEGAL.value,
                        "chunk_type": "parent",
                    },
                ),
            ),
        ]
    )
    return store


def _fake_similarity_factory() -> Callable[..., list[dict[str, object | None]]]:
    def _fake_similarity_search(
        collection: ChromaCollection, query: str, k: int = 4
    ) -> list[dict[str, object | None]]:
        _ = query
        if collection.name == "it_support_knowledge_base":
            results = [
                {
                    "id": "it-child-2",
                    "document": "Reset MFA tokens from employee self-service portal",
                    "metadata": {
                        "department": Department.IT_SUPPORT.value,
                        "chunk_type": "child",
                        "parent_id": "it-parent-2",
                    },
                    "distance": 0.1,
                },
                {
                    "id": "it-child-1",
                    "document": "VPN password reset requires identity verification",
                    "metadata": {
                        "department": Department.IT_SUPPORT.value,
                        "chunk_type": "child",
                        "parent_id": "it-parent-1",
                    },
                    "distance": 0.2,
                },
            ]
            return cast(list[dict[str, object | None]], results[:k])
        results = [
            {
                "id": "legal-child-1",
                "document": "Contract indemnification clauses and limitations",
                "metadata": {
                    "department": Department.LEGAL.value,
                    "chunk_type": "child",
                    "parent_id": "legal-parent-1",
                },
                "distance": 0.1,
            }
        ]
        return cast(list[dict[str, object | None]], results[:k])

    return _fake_similarity_search


def test_retrieve_returns_ranked_parent_documents(
    vector_repository: ChromaRepository,
    docstore: RedisDocStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vector_repository,
        "similarity_search",
        _fake_similarity_factory(),
    )

    retriever = HybridRetriever(vector_repository=vector_repository, docstore=docstore)

    results = retriever.retrieve(
        "vpn password reset", department=Department.IT_SUPPORT, k=2
    )

    assert len(results) == 2
    assert all("Parent IT runbook" in doc.page_content for doc in results)


def test_retrieve_uses_ensemble_retriever_rrf_weights(
    vector_repository: ChromaRepository,
    docstore: RedisDocStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vector_repository,
        "similarity_search",
        _fake_similarity_factory(),
    )

    captured_weights: list[float] = []

    class SupportsInvoke(Protocol):
        def invoke(self, query: str) -> list[Document]: ...

    class FakeEnsembleRetriever:
        retrievers: list[SupportsInvoke]

        def __init__(self, *, retrievers: list[object], weights: list[float]) -> None:
            self.retrievers = cast(list[SupportsInvoke], retrievers)
            captured_weights.extend(weights)

        def invoke(self, query: str) -> list[Document]:
            _ = query
            docs: list[Document] = []
            for retriever in self.retrievers:
                docs.extend(retriever.invoke(query))
            return docs

    monkeypatch.setattr(
        "app.services.retrieval.EnsembleRetriever",
        FakeEnsembleRetriever,
    )

    retriever = HybridRetriever(vector_repository=vector_repository, docstore=docstore)
    _ = retriever.retrieve("vpn password", department=Department.IT_SUPPORT, k=2)

    assert captured_weights == [0.4, 0.6]


def test_per_department_isolation(
    vector_repository: ChromaRepository,
    docstore: RedisDocStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vector_repository,
        "similarity_search",
        _fake_similarity_factory(),
    )

    retriever = HybridRetriever(vector_repository=vector_repository, docstore=docstore)
    it_results = retriever.retrieve(
        "password reset", department=Department.IT_SUPPORT, k=3
    )

    assert len(it_results) > 0
    assert all(
        cast(str, doc.metadata.get("department")) == Department.IT_SUPPORT.value
        for doc in it_results
    )


def test_fallback_to_vector_only_when_bm25_has_no_hits(
    vector_repository: ChromaRepository,
    docstore: RedisDocStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vector_repository,
        "similarity_search",
        _fake_similarity_factory(),
    )

    retriever = HybridRetriever(vector_repository=vector_repository, docstore=docstore)

    results = retriever.retrieve(
        "nonexistent-hybrid-term", department=Department.IT_SUPPORT, k=1
    )

    assert len(results) == 1
    assert "Parent IT runbook" in results[0].page_content


def test_k_parameter_limits_results(
    vector_repository: ChromaRepository,
    docstore: RedisDocStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vector_repository,
        "similarity_search",
        _fake_similarity_factory(),
    )

    retriever = HybridRetriever(vector_repository=vector_repository, docstore=docstore)
    results = retriever.retrieve(
        "password reset", department=Department.IT_SUPPORT, k=1
    )

    assert len(results) == 1


def test_bm25_indexes_built_lazily_per_department(
    vector_repository: ChromaRepository,
    docstore: RedisDocStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vector_repository,
        "similarity_search",
        _fake_similarity_factory(),
    )
    retriever = HybridRetriever(vector_repository=vector_repository, docstore=docstore)

    call_count = 0
    original_builder = retriever._build_bm25_index  # type: ignore[attr-defined]

    def counting_builder(department: Department) -> None:
        nonlocal call_count
        call_count += 1
        original_builder(department)

    monkeypatch.setattr(retriever, "_build_bm25_index", counting_builder)

    _ = retriever.retrieve("vpn", department=Department.IT_SUPPORT, k=1)
    _ = retriever.retrieve("mfa", department=Department.IT_SUPPORT, k=1)
    _ = retriever.retrieve("contract", department=Department.LEGAL, k=1)

    assert call_count == 2
