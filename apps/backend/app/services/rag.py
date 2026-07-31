from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.self_rag import create_self_rag_graph


@dataclass(frozen=True)
class RAGResult:
    answer: str
    knowledge_bases_used: list[str]
    sources: list[dict[str, Any]]
    confidence: float
    iterations: int
    pipeline_steps: list[str]


class RAGService:
    """Single, domain-agnostic retrieval and generation pipeline."""

    def __init__(self, llm: BaseChatModel, retriever: Any) -> None:
        self.graph = create_self_rag_graph(llm=llm, retriever=retriever)

    def query(
        self,
        query: str,
        knowledge_base: str | None = None,
    ) -> RAGResult:
        raw = cast(
            dict[str, Any],
            self.graph.invoke(
                {
                    "query": query,
                    "knowledge_base": knowledge_base,
                    "documents": [],
                    "generation": "",
                    "critique_result": "rejected",
                    "confidence": 0.0,
                    "iterations": 0,
                    "node_history": [],
                }
            ),
        )
        documents = cast(list[Document], raw.get("documents") or [])
        sources = self._sources(documents)
        knowledge_bases = sorted(
            {
                str(document.metadata["knowledge_base"])
                for document in documents
                if document.metadata.get("knowledge_base")
            }
        )
        return RAGResult(
            answer=str(raw.get("generation") or "No answer available."),
            knowledge_bases_used=knowledge_bases,
            sources=sources,
            confidence=float(raw.get("confidence", 0.0)),
            iterations=int(raw.get("iterations", 1)),
            pipeline_steps=[str(step) for step in raw.get("node_history", [])],
        )

    @staticmethod
    def _sources(documents: list[Document]) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        seen: set[tuple[str, str, int | None]] = set()
        for document in documents:
            metadata = document.metadata
            source_path = str(
                metadata.get("source_path")
                or metadata.get("source_file")
                or "unknown"
            )
            knowledge_base = str(metadata.get("knowledge_base") or "unknown")
            page_raw = metadata.get("page")
            page = int(page_raw) if isinstance(page_raw, int) else None
            key = (knowledge_base, source_path, page)
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                {
                    "title": source_path,
                    "source_path": source_path,
                    "knowledge_base": knowledge_base,
                    "page": page,
                    "snippet": document.page_content[:280],
                    "score": float(metadata.get("retrieval_score", 0.0)),
                }
            )
        return sources
