from __future__ import annotations

from collections import defaultdict
from typing import Any, cast

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from rank_bm25 import BM25Okapi

from app.core.docstore import RedisDocStore
from app.repositories.vectorstore import ChromaCollection, ChromaRepository
from app.schemas.common import normalize_knowledge_base


def _tokenize(text: str) -> list[str]:
    return [token for token in text.casefold().split() if token]


class HybridRetriever:
    """Hybrid dense + lexical retriever for any number of knowledge bases."""

    def __init__(
        self,
        vector_repository: ChromaRepository,
        docstore: RedisDocStore,
        embedding_model: Embeddings,
    ) -> None:
        self.vector_repository = vector_repository
        self.docstore = docstore
        self.embedding_model = embedding_model
        self._bm25_indexes: dict[str, BM25Okapi] = {}
        self._bm25_documents: dict[str, list[Document]] = {}

    def invoke(
        self,
        query: str,
        config: dict[str, Any] | None = None,
    ) -> list[Document]:
        options = config or {}
        knowledge_base = options.get("knowledge_base") or options.get("department")
        return self.retrieve(
            query=query,
            knowledge_base=str(knowledge_base) if knowledge_base else None,
            k=int(options.get("k", 5)),
        )

    def retrieve(
        self,
        query: str,
        knowledge_base: str | None = None,
        k: int = 5,
    ) -> list[Document]:
        if knowledge_base:
            targets = [normalize_knowledge_base(knowledge_base)]
        else:
            targets = self.vector_repository.list_knowledge_bases()

        if not targets:
            return []

        query_embedding = self.embedding_model.embed_query(query)
        candidates: list[Document] = []
        per_base_k = max(k, 5)
        for target in targets:
            candidates.extend(
                self._retrieve_from_knowledge_base(
                    query=query,
                    query_embedding=query_embedding,
                    knowledge_base=target,
                    k=per_base_k,
                )
            )

        candidates.sort(
            key=lambda doc: float(doc.metadata.get("retrieval_score", 0.0)),
            reverse=True,
        )
        return candidates[:k]

    def invalidate(self, knowledge_base: str) -> None:
        normalized = normalize_knowledge_base(knowledge_base)
        self._bm25_indexes.pop(normalized, None)
        self._bm25_documents.pop(normalized, None)

    def _retrieve_from_knowledge_base(
        self,
        *,
        query: str,
        query_embedding: list[float],
        knowledge_base: str,
        k: int,
    ) -> list[Document]:
        try:
            collection = self.vector_repository.get_collection(knowledge_base)
        except ValueError:
            return []

        if knowledge_base not in self._bm25_indexes:
            self._build_bm25_index(knowledge_base, collection)

        vector_items = self.vector_repository.similarity_search(
            collection=collection,
            query_embedding=query_embedding,
            k=k,
        )
        vector_docs = [
            Document(
                id=cast(str | None, item.get("id")),
                page_content=str(item.get("document") or ""),
                metadata={
                    **cast(dict[str, Any], item.get("metadata") or {}),
                    "knowledge_base": knowledge_base,
                },
            )
            for item in vector_items
        ]
        lexical_docs = self._bm25_search(query, knowledge_base, k)
        fused = self._reciprocal_rank_fusion(
            vector_docs=vector_docs,
            lexical_docs=lexical_docs,
        )
        return self._resolve_parent_documents(fused, knowledge_base, k)

    def _bm25_search(
        self,
        query: str,
        knowledge_base: str,
        k: int,
    ) -> list[Document]:
        documents = self._bm25_documents.get(knowledge_base, [])
        query_tokens = _tokenize(query)
        if not documents or not query_tokens:
            return []

        scores = self._bm25_indexes[knowledge_base].get_scores(query_tokens)
        ranked = sorted(
            range(len(scores)),
            key=lambda index: float(scores[index]),
            reverse=True,
        )
        return [
            documents[index]
            for index in ranked
            if float(scores[index]) > 0
        ][:k]

    @staticmethod
    def _reciprocal_rank_fusion(
        *,
        vector_docs: list[Document],
        lexical_docs: list[Document],
        rank_constant: int = 60,
    ) -> list[Document]:
        documents: dict[str, Document] = {}
        scores: defaultdict[str, float] = defaultdict(float)
        for weight, ranking in ((0.65, vector_docs), (0.35, lexical_docs)):
            for rank, document in enumerate(ranking, start=1):
                key = str(document.id or hash(document.page_content))
                documents[key] = document
                scores[key] += weight / (rank_constant + rank)

        fused: list[Document] = []
        for key in sorted(scores, key=scores.get, reverse=True):
            document = documents[key]
            fused.append(
                Document(
                    id=document.id,
                    page_content=document.page_content,
                    metadata={**document.metadata, "retrieval_score": scores[key]},
                )
            )
        return fused

    def _build_bm25_index(
        self,
        knowledge_base: str,
        collection: ChromaCollection,
    ) -> None:
        documents = self._load_child_documents(collection)
        corpus = [_tokenize(document.page_content) for document in documents]
        self._bm25_documents[knowledge_base] = documents
        self._bm25_indexes[knowledge_base] = BM25Okapi(corpus or [[]])

    @staticmethod
    def _load_child_documents(collection: ChromaCollection) -> list[Document]:
        payload = collection.get(include=["documents", "metadatas"])
        ids = cast(list[str], payload.get("ids") or [])
        documents = cast(list[str], payload.get("documents") or [])
        metadatas = cast(list[dict[str, Any] | None], payload.get("metadatas") or [])
        results: list[Document] = []
        for index, doc_id in enumerate(ids):
            metadata = dict(metadatas[index] or {}) if index < len(metadatas) else {}
            if metadata.get("chunk_type") != "child":
                continue
            results.append(
                Document(
                    id=doc_id,
                    page_content=documents[index] if index < len(documents) else "",
                    metadata=metadata,
                )
            )
        return results

    def _resolve_parent_documents(
        self,
        child_documents: list[Document],
        knowledge_base: str,
        k: int,
    ) -> list[Document]:
        resolved: list[Document] = []
        seen: set[str] = set()
        for child in child_documents:
            parent_id = child.metadata.get("parent_id")
            document = (
                self.docstore.mget([str(parent_id)])[0]
                if parent_id is not None
                else None
            )
            selected = document or child
            key = str(selected.id or parent_id or hash(selected.page_content))
            if key in seen:
                continue
            seen.add(key)
            resolved.append(
                Document(
                    id=selected.id,
                    page_content=selected.page_content,
                    metadata={
                        **selected.metadata,
                        "knowledge_base": knowledge_base,
                        "retrieval_score": child.metadata.get(
                            "retrieval_score", 0.0
                        ),
                    },
                )
            )
            if len(resolved) >= k:
                break
        return resolved
