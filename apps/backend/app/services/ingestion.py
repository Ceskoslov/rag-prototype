from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from pypdf import PdfReader

from app.core.docstore import RedisDocStore
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
    ) -> None:
        self.chroma_repo = chroma_repo
        self.docstore = docstore
        self.chunking_service = chunking_service
        self.embedding_model = embedding_model

    @staticmethod
    def discover_knowledge_bases(data_dir: Path) -> list[str]:
        if not data_dir.exists():
            return []
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
        for knowledge_base in self.discover_knowledge_bases(data_dir):
            results[knowledge_base] = await self.ingest_knowledge_base(
                knowledge_base=knowledge_base,
                data_dir=data_dir,
            )
        return results

    async def ingest_knowledge_base(
        self,
        knowledge_base: str,
        data_dir: Path,
    ) -> int:
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
        collection = self.chroma_repo.create_collection(
            knowledge_base=normalized,
            metadata={"knowledge_base": normalized},
        )
        processed = 0
        for file_path in files:
            changed = await self._ingest_file(
                file_path=file_path,
                base_path=base_path,
                knowledge_base=normalized,
                collection=collection,
            )
            processed += int(changed)

        logger.info(
            "ingestion_complete",
            knowledge_base=normalized,
            discovered_files=len(files),
            processed_files=processed,
        )
        return processed

    async def _ingest_file(
        self,
        *,
        file_path: Path,
        base_path: Path,
        knowledge_base: str,
        collection: ChromaCollection,
    ) -> bool:
        file_bytes = file_path.read_bytes()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        source_path = file_path.relative_to(base_path).as_posix()
        hash_key = f"ingested_files:{knowledge_base}:{source_path}"
        if self.docstore.client.get(hash_key) == file_hash:
            return False

        source_documents = self._load_file(
            file_path=file_path,
            knowledge_base=knowledge_base,
            source_path=source_path,
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

        self.chroma_repo.delete_by_source(collection, source_path)
        if parent_chunks:
            self.docstore.mset(
                [(str(chunk.id), chunk) for chunk in parent_chunks if chunk.id]
            )
        if child_chunks:
            embeddings = self.embedding_model.embed_documents(
                [chunk.page_content for chunk in child_chunks]
            )
            self.chroma_repo.upsert_documents(
                collection=collection,
                docs=[
                    {
                        "id": chunk.id,
                        "document": chunk.page_content,
                        "metadata": dict(chunk.metadata),
                    }
                    for chunk in child_chunks
                ],
                embeddings=embeddings,
            )

        self.docstore.client.set(hash_key, file_hash)
        logger.info(
            "file_ingested",
            knowledge_base=knowledge_base,
            source_path=source_path,
            parent_chunks=len(parent_chunks),
            child_chunks=len(child_chunks),
        )
        return True

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
            return [
                Document(
                    page_content=page.extract_text() or "",
                    metadata={**base_metadata, "page": page_number},
                )
                for page_number, page in enumerate(reader.pages, start=1)
                if page.extract_text()
            ]

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

        return [Document(page_content=text, metadata=base_metadata)] if text.strip() else []
