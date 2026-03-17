from __future__ import annotations

from typing import Any, cast

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers.ensemble import EnsembleRetriever
from rank_bm25 import BM25Okapi

from app.core.docstore import RedisDocStore
from app.repositories.vectorstore import ChromaCollection, ChromaRepository
from app.schemas.common import Department


def _tokenize(text: str) -> list[str]:
    return [token for token in text.lower().split() if token]


class _VectorChildRetriever(BaseRetriever):
    repository: ChromaRepository
    department: Department
    k: int = 5

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        _ = run_manager
        collection = self.repository.get_collection(self.department.value)
        items = self.repository.similarity_search(
            collection=collection, query=query, k=self.k
        )

        docs: list[Document] = []
        for item in items:
            metadata = cast(dict[str, Any], item.get("metadata") or {})
            doc = Document(
                id=cast(str | None, item.get("id")),
                page_content=str(item.get("document") or ""),
                metadata=metadata,
            )
            docs.append(doc)
        return docs


class _BM25ChildRetriever(BaseRetriever):
    index: BM25Okapi
    documents: list[Document]
    k: int = 5

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        _ = run_manager
        if not self.documents:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = self.index.get_scores(query_tokens)
        ranked_indices = sorted(
            range(len(scores)), key=lambda idx: float(scores[idx]), reverse=True
        )

        results: list[Document] = []
        for idx in ranked_indices:
            if float(scores[idx]) <= 0:
                continue
            results.append(self.documents[idx])
            if len(results) >= self.k:
                break
        return results


class HybridRetriever:
    def __init__(
        self, vector_repository: ChromaRepository, docstore: RedisDocStore
    ) -> None:
        self.vector_repository = vector_repository
        self.docstore = docstore
        self._bm25_indexes: dict[Department, BM25Okapi] = {}
        self._bm25_documents: dict[Department, list[Document]] = {}

    def invoke(
        self, query: str, config: dict[str, Any] | None = None
    ) -> list[Document]:
        department_str = (config or {}).get("department", "it_support")
        k = (config or {}).get("k", 5)
        try:
            department = Department(department_str)
        except ValueError:
            department = Department.IT_SUPPORT
        return self.retrieve(query, department, k=k)

    def retrieve(
        self, query: str, department: Department, k: int = 5
    ) -> list[Document]:
        if department not in self._bm25_indexes:
            self._build_bm25_index(department)

        vector_retriever = _VectorChildRetriever(
            repository=self.vector_repository,
            department=department,
            k=k,
        )

        bm25_docs = self._bm25_documents.get(department, [])
        child_results: list[Document]

        if not bm25_docs:
            child_results = vector_retriever.invoke(query)
        else:
            bm25_retriever = _BM25ChildRetriever(
                index=self._bm25_indexes[department],
                documents=bm25_docs,
                k=k,
            )

            ensemble = EnsembleRetriever(
                retrievers=[bm25_retriever, vector_retriever],
                weights=[0.4, 0.6],
            )
            child_results = cast(list[Document], ensemble.invoke(query))

            if not child_results:
                child_results = vector_retriever.invoke(query)

        return self._resolve_parent_documents(
            child_documents=child_results,
            department=department,
            k=k,
        )

    def _build_bm25_index(self, department: Department) -> None:
        collection = self.vector_repository.get_collection(department.value)
        docs = self._load_department_child_documents(collection=collection)
        tokenized_corpus = [_tokenize(doc.page_content) for doc in docs]

        if not tokenized_corpus:
            self._bm25_indexes[department] = BM25Okapi([[]])
            self._bm25_documents[department] = []
            return

        self._bm25_indexes[department] = BM25Okapi(tokenized_corpus)
        self._bm25_documents[department] = docs

    def _load_department_child_documents(
        self, collection: ChromaCollection
    ) -> list[Document]:
        raw_collection = cast(Any, collection)
        if not hasattr(raw_collection, "get"):
            return []

        payload = cast(
            dict[str, Any],
            raw_collection.get(include=["documents", "metadatas"]),
        )
        ids = cast(list[str], payload.get("ids") or [])
        documents = cast(list[str], payload.get("documents") or [])
        metadatas = cast(list[dict[str, Any] | None], payload.get("metadatas") or [])

        results: list[Document] = []
        for idx, doc_id in enumerate(ids):
            metadata = cast(
                dict[str, Any], metadatas[idx] if idx < len(metadatas) else {}
            )
            if metadata.get("chunk_type") != "child":
                continue

            page_content = documents[idx] if idx < len(documents) else ""
            results.append(
                Document(
                    id=doc_id,
                    page_content=page_content,
                    metadata=metadata,
                )
            )
        return results

    def _resolve_parent_documents(
        self,
        child_documents: list[Document],
        department: Department,
        k: int,
    ) -> list[Document]:
        resolved: list[Document] = []
        seen_parent_ids: set[str] = set()
        department_value = department.value

        for child in child_documents:
            metadata = cast(dict[str, Any], child.metadata)
            parent_id_raw = metadata.get("parent_id")
            parent_id = str(parent_id_raw) if parent_id_raw is not None else None

            if parent_id is None:
                if self._document_matches_department(child, department_value):
                    resolved.append(child)
            elif parent_id not in seen_parent_ids:
                seen_parent_ids.add(parent_id)
                parent_doc = self.docstore.mget([parent_id])[0]
                if parent_doc is None:
                    if self._document_matches_department(child, department_value):
                        resolved.append(child)
                elif self._document_matches_department(parent_doc, department_value):
                    resolved.append(parent_doc)

            if len(resolved) >= k:
                break

        return resolved[:k]

    @staticmethod
    def _document_matches_department(doc: Document, department_value: str) -> bool:
        metadata = cast(dict[str, Any], doc.metadata)
        doc_department = metadata.get("department")
        if doc_department is None:
            return True
        return str(doc_department) == department_value
