from __future__ import annotations

import re
from collections import defaultdict
from threading import RLock
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from rank_bm25 import BM25L

from app.core.docstore import RedisDocStore
from app.core.embeddings import embedding_signature
from app.core.settings import settings
from app.repositories.vectorstore import ChromaCollection, ChromaRepository
from app.schemas.common import normalize_knowledge_base


def _tokenize(text: str) -> list[str]:
    # Character bigrams keep Chinese/Japanese searchable without a language model.
    runs = re.findall(r"[\u3400-\u9fff\u3040-\u30ff]+|[\w]+", text.casefold())
    tokens = []
    for run in runs:
        if re.search(r"[\u3400-\u9fff\u3040-\u30ff]", run):
            tokens.extend(
                run[index : index + 2] for index in range(max(1, len(run) - 1))
            )
        else:
            tokens.append(run)
    return tokens


class HybridRetriever:
    """Global dense/lexical fusion over versioned knowledge-base snapshots."""

    def __init__(
        self,
        vector_repository: ChromaRepository,
        docstore: RedisDocStore,
        embedding_model: Embeddings,
        reranker: Any = None,
    ) -> None:
        self.vector_repository = vector_repository
        self.docstore = docstore
        self.embedding_model = embedding_model
        self.reranker = reranker
        self._cache: dict[str, tuple[str, BM25L | None, list[Document]]] = {}
        self._lock = RLock()

    def invoke(
        self, query: str, config: dict[str, Any] | None = None
    ) -> list[Document]:
        options = config or {}
        return self.retrieve(
            query,
            options.get("knowledge_base") or options.get("department"),
            int(options.get("k", 5)),
        )

    def retrieve(
        self, query: str, knowledge_base: str | None = None, k: int = 5
    ) -> list[Document]:
        targets = (
            [normalize_knowledge_base(knowledge_base)]
            if knowledge_base
            else self.vector_repository.list_knowledge_bases()
        )
        if not targets:
            return []
        vector = self.embedding_model.embed_query(query)
        dense: list[Document] = []
        lexical: list[tuple[float, Document]] = []
        query_tokens = _tokenize(query)
        for target in targets:
            try:
                collection = self.vector_repository.get_collection(target)
            except ValueError:
                continue
            stored_signature = (collection.metadata or {}).get("embedding_signature")
            if stored_signature and stored_signature != embedding_signature(
                self.embedding_model
            ):
                raise ValueError(
                    f"Embedding configuration changed for {target}; rebuild its index"
                )
            index, documents = self._lexical_snapshot(target, collection)
            for item in self.vector_repository.similarity_search(
                collection, vector, max(20, k * 4)
            ):
                distance = float(item.get("distance") or 0)
                if (
                    settings.dense_max_distance is not None
                    and distance > settings.dense_max_distance
                ):
                    continue
                dense.append(
                    Document(
                        id=str(item["id"]),
                        page_content=str(item["document"]),
                        metadata={
                            **(item.get("metadata") or {}),
                            "knowledge_base": target,
                            "distance": distance,
                        },
                    )
                )
            if index and query_tokens:
                scores = index.get_scores(query_tokens)
                for score, document in zip(scores, documents, strict=True):
                    if set(query_tokens).intersection(_tokenize(document.page_content)):
                        lexical.append((float(score), document))
        dense.sort(key=lambda document: document.metadata["distance"])
        lexical.sort(key=lambda pair: pair[0], reverse=True)
        fused = self._reciprocal_rank_fusion(
            vector_docs=dense,
            lexical_docs=[doc for _, doc in lexical[: max(20, k * 4)]],
        )
        parents = self._resolve_parent_documents(fused[: max(20, k * 4)])
        if self.reranker and parents:
            scores = self.reranker.predict(
                [(query, doc.page_content) for doc in parents]
            )
            for document, score in zip(parents, scores, strict=True):
                document.metadata["rerank_score"] = float(score)
            parents.sort(key=lambda doc: doc.metadata["rerank_score"], reverse=True)
        return parents[:k]

    def invalidate(self, knowledge_base: str) -> None:
        with self._lock:
            self._cache.pop(normalize_knowledge_base(knowledge_base), None)

    def _lexical_snapshot(
        self, knowledge_base: str, collection: ChromaCollection
    ) -> tuple[BM25L | None, list[Document]]:
        with self._lock:
            cached = self._cache.get(knowledge_base)
            if cached is None or cached[0] != collection.name:
                documents = self._load_child_documents(collection)
                corpus = [_tokenize(document.page_content) for document in documents]
                index = BM25L(corpus) if corpus and any(corpus) else None
                cached = (collection.name, index, documents)
                self._cache[knowledge_base] = cached
            return cached[1], cached[2]

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
                key = str(document.id or document.page_content)
                documents[key] = document
                scores[key] += weight / (rank_constant + rank)
        return [
            Document(
                id=documents[key].id,
                page_content=documents[key].page_content,
                metadata={**documents[key].metadata, "retrieval_score": scores[key]},
            )
            for key in sorted(scores, key=lambda key: scores[key], reverse=True)
        ]

    @staticmethod
    def _load_child_documents(collection: ChromaCollection) -> list[Document]:
        results = []
        offset = 0
        while True:
            payload = collection.get(
                include=["documents", "metadatas"], limit=500, offset=offset
            )
            ids = payload.get("ids") or []
            documents = payload.get("documents") or []
            metadatas = payload.get("metadatas") or []
            for doc_id, text, metadata in zip(ids, documents, metadatas, strict=True):
                if (metadata or {}).get("chunk_type") == "child":
                    results.append(
                        Document(id=doc_id, page_content=text, metadata=metadata)
                    )
            if len(ids) < 500:
                return results
            offset += len(ids)

    def _resolve_parent_documents(self, children: list[Document]) -> list[Document]:
        parent_ids = [str(child.metadata.get("parent_id", "")) for child in children]
        parents = self.docstore.mget(parent_ids)
        resolved = []
        seen = set()
        for child, parent_id, parent in zip(children, parent_ids, parents, strict=True):
            selected = parent or child
            key = selected.id or parent_id or selected.page_content
            if key not in seen:
                seen.add(key)
                resolved.append(
                    Document(
                        id=selected.id,
                        page_content=selected.page_content,
                        metadata={
                            **selected.metadata,
                            "retrieval_score": child.metadata.get(
                                "retrieval_score", 0.0
                            ),
                        },
                    )
                )
        return resolved
