from __future__ import annotations

import asyncio
import csv
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from pypdf import PdfReader

from app.core.docstore import RedisDocStore
from app.core.embeddings import embedding_signature
from app.core.logging import get_logger
from app.repositories.vectorstore import ChromaCollection, ChromaRepository
from app.schemas.common import normalize_knowledge_base
from app.services.chunking import ChunkingService

logger = get_logger(__name__)
SUPPORTED_EXTENSIONS = {
    ".csv",
    ".htm",
    ".html",
    ".json",
    ".md",
    ".pdf",
    ".rst",
    ".txt",
}


class IngestionService:
    """Discover and ingest arbitrary knowledge-base directories."""

    def __init__(
        self,
        chroma_repo: ChromaRepository,
        docstore: RedisDocStore,
        chunking_service: ChunkingService,
        embedding_model: Embeddings,
        progress=None,
    ) -> None:
        self.chroma_repo = chroma_repo
        self.docstore = docstore
        self.chunking_service = chunking_service
        self.embedding_model = embedding_model
        self.progress = progress

    @staticmethod
    def discover_knowledge_bases(data_dir: Path) -> list[str]:
        if not data_dir.exists():
            return []
        for path in data_dir.iterdir():
            if path.is_dir() and normalize_knowledge_base(path.name) != path.name:
                raise ValueError(
                    f"Rename knowledge-base directory to its canonical slug: {path.name}"
                )
        return sorted(
            normalize_knowledge_base(path.name)
            for path in data_dir.iterdir()
            if path.is_dir()
            and any(
                file.is_file() and file.suffix.casefold() in SUPPORTED_EXTENSIONS
                for file in path.rglob("*")
            )
        )

    async def ingest_all(self, data_dir: Path) -> dict[str, int]:
        results: dict[str, int] = {}
        targets = sorted(
            set(self.discover_knowledge_bases(data_dir))
            | {
                name
                for name in self.chroma_repo.list_knowledge_bases()
                if (data_dir / name).is_dir()
            }
        )
        for knowledge_base in targets:
            results[knowledge_base] = await self.ingest_knowledge_base(
                knowledge_base=knowledge_base,
                data_dir=data_dir,
            )
        for name in self.chroma_repo.list_knowledge_bases():
            if not (data_dir / name).is_dir():
                record = self.chroma_repo.index_record(name)
                if record:
                    for key in self.docstore.yield_keys(
                        prefix=str(record["collection"]) + ":"
                    ):
                        self.docstore.client.expire(self.docstore._make_key(key), 600)
                self.chroma_repo.delete_collection(name)
        return results

    async def ingest_knowledge_base(
        self,
        knowledge_base: str,
        data_dir: Path,
    ) -> int:
        return await asyncio.to_thread(
            self._ingest_knowledge_base, knowledge_base, data_dir
        )

    def _ingest_knowledge_base(self, knowledge_base: str, data_dir: Path) -> int:
        normalized = normalize_knowledge_base(knowledge_base)
        base_path = data_dir / normalized
        if not base_path.is_dir():
            raise FileNotFoundError(
                f"knowledge-base directory does not exist: {base_path}"
            )

        files = sorted(
            file
            for file in base_path.rglob("*")
            if file.is_file() and file.suffix.casefold() in SUPPORTED_EXTENSIONS
        )
        # One writer per knowledge base; queries continue using the active index.
        lock = self.docstore.client.lock(
            f"ingest_lock:{normalized}", timeout=3600, blocking_timeout=0
        )
        if not lock.acquire(blocking=False):
            raise ValueError("Knowledge base is already being indexed")
        try:
            manifest = json.dumps(
                {
                    "files": {
                        file.relative_to(base_path).as_posix(): hashlib.sha256(
                            file.read_bytes()
                        ).hexdigest()
                        for file in files
                    },
                    "embedding": embedding_signature(self.embedding_model),
                    "chunking": self.chunking_service.signature,
                },
                sort_keys=True,
            )
            previous = self.chroma_repo.index_record(normalized)
            if previous and previous.get("manifest") == manifest:
                return 0
            staging = self.chroma_repo.create_staging_collection(
                normalized,
                {
                    "embedding_signature": embedding_signature(self.embedding_model),
                },
            )
            parent_ids: list[str] = []
            try:
                for file_index, file_path in enumerate(files):
                    if self.progress:
                        self.progress(file_index, len(files))
                    parent_ids.extend(
                        self._ingest_file(
                            file_path=file_path,
                            base_path=base_path,
                            knowledge_base=normalized,
                            collection=staging,
                        )
                    )
                self.chroma_repo.activate_index(normalized, staging, manifest)
                if self.progress:
                    self.progress(len(files), len(files))
            except Exception:
                self.chroma_repo.client.delete_collection(staging.name)
                self.docstore.mdelete(parent_ids)
                raise
            if previous:
                # Grace period lets in-flight readers finish against their old snapshot.
                for key in self.docstore.yield_keys(
                    prefix=str(previous["collection"]) + ":"
                ):
                    self.docstore.client.expire(self.docstore._make_key(key), 600)
            self.chroma_repo.garbage_collect(normalized)
            logger.info(
                "ingestion_complete",
                knowledge_base=normalized,
                files=len(files),
                index_version=staging.name,
            )
            return len(files)
        finally:
            lock.release()

    def _ingest_file(
        self,
        *,
        file_path: Path,
        base_path: Path,
        knowledge_base: str,
        collection: ChromaCollection,
    ) -> list[str]:
        source_documents = self._load_file(
            file_path=file_path,
            knowledge_base=knowledge_base,
            source_path=file_path.relative_to(base_path).as_posix(),
        )
        if not source_documents:
            raise ValueError(
                f"No extractable text in {file_path.name}; scanned PDFs require OCR"
            )
        chunks = [
            chunk
            for document in source_documents
            for chunk in self.chunking_service.chunk_document(document)
        ]
        parent_chunks = [
            chunk for chunk in chunks if chunk.metadata.get("chunk_type") == "parent"
        ]
        child_chunks = [
            chunk for chunk in chunks if chunk.metadata.get("chunk_type") == "child"
        ]
        for parent in parent_chunks:
            parent.metadata["index_version"] = collection.name
            parent.id = f"{collection.name}:{parent.id}"
        for child in child_chunks:
            child.metadata["index_version"] = collection.name
            child.metadata["parent_id"] = (
                f"{collection.name}:{child.metadata['parent_id']}"
            )
        # Embed before storing parents; failed batches leave the active snapshot intact.
        for offset in range(0, len(child_chunks), 64):
            batch = child_chunks[offset : offset + 64]
            vectors = self.embedding_model.embed_documents(
                [chunk.page_content for chunk in batch]
            )
            self.chroma_repo.upsert_documents(
                collection,
                [
                    {
                        "id": chunk.id,
                        "document": chunk.page_content,
                        "metadata": dict(chunk.metadata),
                    }
                    for chunk in batch
                ],
                vectors,
            )
        self.docstore.mset([(str(chunk.id), chunk) for chunk in parent_chunks])
        return [str(chunk.id) for chunk in parent_chunks]

    @staticmethod
    def _load_file(
        *,
        file_path: Path,
        knowledge_base: str,
        source_path: str,
    ) -> list[Document]:
        suffix = file_path.suffix.casefold()
        base_metadata = {
            "knowledge_base": knowledge_base,
            "source_file": file_path.name,
            "source_path": source_path,
            "file_type": suffix.removeprefix("."),
        }

        if suffix == ".pdf":
            reader = PdfReader(str(file_path))
            documents = []
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={**base_metadata, "page": page_number},
                        )
                    )
            return documents

        text = file_path.read_text(encoding="utf-8", errors="replace")
        if suffix in {".html", ".htm"}:
            text = BeautifulSoup(text, "html.parser").get_text("\n", strip=True)
        elif suffix == ".json":
            text = json.dumps(
                json.loads(text),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        elif suffix == ".csv":
            rows = list(csv.DictReader(text.splitlines()))
            text = "\n\n".join(
                "\n".join(f"{key}: {value}" for key, value in row.items())
                for row in rows
            )

        return (
            [Document(page_content=text, metadata=base_metadata)]
            if text.strip()
            else []
        )
