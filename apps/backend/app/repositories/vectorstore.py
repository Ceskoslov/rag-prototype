from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, cast
from urllib.parse import urlparse

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import Include, Metadata

from app.core.settings import settings
from app.schemas.common import normalize_knowledge_base


class ChromaCollection(Protocol):
    @property
    def name(self) -> str: ...

    def upsert(
        self,
        ids: Sequence[str],
        embeddings: Sequence[Sequence[float]] | None = None,
        metadatas: Sequence[Metadata] | None = None,
        documents: Sequence[str] | None = None,
    ) -> None: ...

    def query(
        self,
        query_embeddings: Sequence[Sequence[float]] | None = None,
        n_results: int = 10,
        where: object | None = None,
        include: Include | None = None,
    ) -> Mapping[str, object]: ...

    def delete(
        self,
        ids: Sequence[str] | None = None,
        where: object | None = None,
    ) -> None: ...

    def get(
        self,
        include: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Mapping[str, object]: ...

    def count(self) -> int: ...


class ChromaRepository:
    """Small Chroma adapter with application-owned embeddings.

    Embeddings are calculated by the configured provider and sent explicitly on
    both writes and queries. This prevents Chroma's server-side default model
    from silently diverging from ``EMBEDDING_PROVIDER``.
    """

    _PREFIX = "kb_"
    _LEGACY_SUFFIX = "_knowledge_base"

    def __init__(self, client: ClientAPI | None = None) -> None:
        if client is not None:
            self.client = client
            return

        provider = settings.chroma_provider.casefold()
        if provider == "cloud":
            required = {
                "CHROMA_TENANT": settings.chroma_tenant,
                "CHROMA_DATABASE": settings.chroma_database,
                "CHROMA_API_KEY": settings.chroma_api_key,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(
                    f"Missing Chroma Cloud settings: {', '.join(missing)}"
                )
            self.client = chromadb.CloudClient(
                tenant=settings.chroma_tenant,
                database=settings.chroma_database,
                api_key=settings.chroma_api_key,
                cloud_host=settings.chroma_cloud_host,
            )
            return
        if provider != "http":
            raise ValueError("CHROMA_PROVIDER must be one of: http, cloud")

        parsed = urlparse(settings.chroma_api_url)
        self.client = chromadb.HttpClient(
            host=parsed.hostname or "localhost",
            port=parsed.port or 8000,
            ssl=parsed.scheme == "https",
        )

    @classmethod
    def _collection_name(cls, knowledge_base: str) -> str:
        return f"{cls._PREFIX}{normalize_knowledge_base(knowledge_base)}"

    @classmethod
    def _knowledge_base_from_collection(cls, collection_name: str) -> str | None:
        if collection_name.startswith(cls._PREFIX):
            return collection_name.removeprefix(cls._PREFIX)
        if collection_name.endswith(cls._LEGACY_SUFFIX):
            return collection_name.removesuffix(cls._LEGACY_SUFFIX)
        return None

    def create_collection(
        self,
        knowledge_base: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChromaCollection:
        normalized = normalize_knowledge_base(knowledge_base)
        collection_metadata: dict[str, Any] = {
            "knowledge_base": normalized,
            "hnsw:space": "cosine",
            **(metadata or {}),
        }
        return cast(
            ChromaCollection,
            self.client.get_or_create_collection(
                name=self._collection_name(normalized),
                metadata=collection_metadata,
                embedding_function=None,
            ),
        )

    def get_collection(self, knowledge_base: str) -> ChromaCollection:
        normalized = normalize_knowledge_base(knowledge_base)
        candidates = [
            self._collection_name(normalized),
            f"{normalized}{self._LEGACY_SUFFIX}",
        ]
        for name in candidates:
            try:
                return cast(
                    ChromaCollection,
                    self.client.get_collection(name=name, embedding_function=None),
                )
            except Exception:
                continue
        raise ValueError(f"Unknown knowledge base: {normalized}")

    def list_knowledge_bases(self) -> list[str]:
        names: list[str] = []
        for collection in self.client.list_collections():
            raw_name = collection if isinstance(collection, str) else collection.name
            name = self._knowledge_base_from_collection(str(raw_name))
            if name and name not in names:
                names.append(name)
        return sorted(names)

    def upsert_documents(
        self,
        collection: ChromaCollection,
        docs: Sequence[Mapping[str, object]],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if not docs:
            return
        if len(docs) != len(embeddings):
            raise ValueError("document and embedding counts must match")

        collection.upsert(
            ids=[str(doc["id"]) for doc in docs],
            embeddings=embeddings,
            documents=[str(doc["document"]) for doc in docs],
            metadatas=[cast(Metadata, doc.get("metadata", {})) for doc in docs],
        )

    def delete_by_source(
        self,
        collection: ChromaCollection,
        source_path: str,
    ) -> None:
        collection.delete(where={"source_path": source_path})

    def similarity_search(
        self,
        collection: ChromaCollection,
        query_embedding: Sequence[float],
        k: int = 5,
    ) -> list[dict[str, object | None]]:
        available = collection.count()
        if available == 0:
            return []
        query_result = collection.query(
            query_embeddings=[list(query_embedding)],
            n_results=min(k, available),
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        ids_nested = cast(list[list[str]], query_result.get("ids") or [])
        documents_nested = cast(
            list[list[str]] | None, query_result.get("documents")
        )
        metadatas_nested = cast(
            list[list[Mapping[str, Any] | None]] | None,
            query_result.get("metadatas"),
        )
        distances_nested = cast(
            list[list[float]] | None, query_result.get("distances")
        )

        ids = ids_nested[0] if ids_nested else []
        documents = documents_nested[0] if documents_nested else []
        metadatas = metadatas_nested[0] if metadatas_nested else []
        distances = distances_nested[0] if distances_nested else []

        return [
            {
                "id": doc_id,
                "document": documents[index] if index < len(documents) else "",
                "metadata": metadatas[index] if index < len(metadatas) else {},
                "distance": distances[index] if index < len(distances) else None,
            }
            for index, doc_id in enumerate(ids)
        ]

    def delete_collection(self, knowledge_base: str) -> None:
        self.client.delete_collection(name=self._collection_name(knowledge_base))

    def get_collection_count(self, collection_name: str) -> int:
        try:
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=None,
            )
            return collection.count()
        except Exception:
            return 0
