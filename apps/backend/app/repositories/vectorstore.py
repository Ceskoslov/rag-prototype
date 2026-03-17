from collections.abc import Mapping, Sequence
from typing import Protocol, cast

import chromadb
from chromadb.api import BaseAPI, ClientAPI
from chromadb.api.types import IncludeEnum, Metadata
from chromadb.utils.batch_utils import create_batches

from app.core.settings import settings


class ChromaCollection(Protocol):
    @property
    def name(self) -> str: ...

    def add(
        self,
        ids: Sequence[str],
        embeddings: object | None = None,
        metadatas: Sequence[Metadata] | None = None,
        documents: Sequence[str] | None = None,
        images: object | None = None,
        uris: object | None = None,
    ) -> None: ...

    def query(
        self,
        query_embeddings: object | None = None,
        query_texts: str | list[str] | None = None,
        query_images: object | None = None,
        query_uris: object | None = None,
        n_results: int = 10,
        where: object | None = None,
        where_document: object | None = None,
        include: list[IncludeEnum] | None = None,
    ) -> Mapping[str, object]: ...

    def count(self) -> int: ...


class ChromaRepository:
    write_policy: str = (
        "Writes must go through ARQ worker (single writer, no concurrent writes)."
    )

    def __init__(self, client: ClientAPI | None = None) -> None:
        if client is None:
            chroma_url = settings.chroma_api_url
            if chroma_url.startswith("http://"):
                host = chroma_url.replace("http://", "").split(":")[0]
                port_str = chroma_url.split(":")[-1].rstrip("/")
                port = int(port_str) if port_str.isdigit() else 8000
            else:
                host = "localhost"
                port = 8000
            self.client: ClientAPI = chromadb.HttpClient(host=host, port=port)
            return
        self.client = client

    @staticmethod
    def _collection_name(department: str) -> str:
        normalized = department.strip().lower().replace(" ", "_")
        return f"{normalized}_knowledge_base"

    def create_collection(
        self, department: str, metadata: dict[str, object] | None = None
    ) -> ChromaCollection:
        return cast(
            ChromaCollection,
            cast(
                object,
                self.client.get_or_create_collection(
                    name=self._collection_name(department),
                    metadata=metadata,
                ),
            ),
        )

    def get_collection(self, department: str) -> ChromaCollection:
        return cast(
            ChromaCollection,
            cast(
                object,
                self.client.get_collection(name=self._collection_name(department)),
            ),
        )

    def add_documents(
        self,
        collection: ChromaCollection,
        docs: Sequence[Mapping[str, object]],
    ) -> None:
        if not docs:
            return

        ids = [str(doc["id"]) for doc in docs]
        documents = [str(doc["document"]) for doc in docs]
        metadatas = [cast(Metadata, doc.get("metadata", {})) for doc in docs]

        batches = create_batches(
            api=cast(BaseAPI, self.client),
            ids=ids,
            metadatas=metadatas,
            documents=documents,
        )

        for batch_ids, batch_embeddings, batch_metadatas, batch_documents in batches:
            if batch_embeddings:
                collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    documents=batch_documents,
                )
                continue
            collection.add(
                ids=batch_ids,
                metadatas=batch_metadatas,
                documents=batch_documents,
            )

    def similarity_search(
        self, collection: ChromaCollection, query: str, k: int = 4
    ) -> list[dict[str, object | None]]:
        query_result = collection.query(
            query_texts=[query],
            n_results=k,
            include=[
                IncludeEnum.documents,
                IncludeEnum.metadatas,
                IncludeEnum.distances,
            ],
        )

        ids_nested = cast(list[list[str]], query_result["ids"])
        documents_nested = cast(list[list[str]] | None, query_result["documents"])
        metadatas_nested = cast(
            list[list[Mapping[str, Metadata] | None]] | None,
            query_result["metadatas"],
        )
        distances_nested = cast(list[list[float]] | None, query_result["distances"])

        ids = ids_nested[0] if ids_nested else []
        documents = documents_nested[0] if documents_nested else []
        metadatas = metadatas_nested[0] if metadatas_nested else []
        distances = distances_nested[0] if distances_nested else []

        return [
            {
                "id": ids[index],
                "document": documents[index],
                "metadata": metadatas[index] if index < len(metadatas) else None,
                "distance": distances[index] if index < len(distances) else None,
            }
            for index in range(len(ids))
        ]

    def delete_collection(self, department: str) -> None:
        _ = self.client.delete_collection(name=self._collection_name(department))

    def get_collection_count(self, collection_name: str) -> int:
        try:
            collection = cast(
                ChromaCollection,
                cast(
                    object,
                    self.client.get_collection(name=collection_name),
                ),
            )
            return collection.count()
        except Exception:
            return 0
