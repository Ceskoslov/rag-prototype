import hashlib
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.core.docstore import RedisDocStore
from app.core.logging import get_logger
from app.repositories.vectorstore import ChromaCollection, ChromaRepository
from app.schemas.common import Department
from app.services.chunking import ChunkingService

logger = get_logger(__name__)


class IngestionService:
    def __init__(
        self,
        chroma_repo: ChromaRepository,
        docstore: RedisDocStore,
        chunking_service: ChunkingService,
        embedding_model: Embeddings,
    ):
        self.chroma_repo: ChromaRepository = chroma_repo
        self.docstore: RedisDocStore = docstore
        self.chunking_service: ChunkingService = chunking_service
        self.embedding_model: Embeddings = embedding_model

    async def ingest_department(
        self,
        department: Department,
        data_dir: Path,
    ) -> None:
        dept_path = data_dir / department.value

        if not dept_path.exists() or not dept_path.is_dir():
            logger.warning(
                "department_directory_not_found",
                department=department.value,
                path=str(dept_path),
            )
            return

        md_files = list(dept_path.glob("*.md"))

        if not md_files:
            logger.info(
                "no_markdown_files_found",
                department=department.value,
                path=str(dept_path),
            )
            return

        logger.info(
            "ingestion_started",
            department=department.value,
            file_count=len(md_files),
        )

        collection = self.chroma_repo.create_collection(
            department=department.value,
            metadata={"department": department.value},
        )

        total_chunks = 0

        for file_path in md_files:
            await self._ingest_file(
                file_path=file_path,
                department=department,
                collection=collection,
            )
            total_chunks += 1

        logger.info(
            "ingestion_complete",
            department=department.value,
            total_files=len(md_files),
        )

    async def _ingest_file(
        self,
        file_path: Path,
        department: Department,
        collection: ChromaCollection,
    ) -> None:
        content = file_path.read_text()
        file_hash = hashlib.md5(content.encode()).hexdigest()
        hash_key = f"ingested_files:{department.value}:{file_path.name}"

        stored_hash: str | None = None
        if hasattr(self.docstore.client, "get"):
            result = self.docstore.client.get(hash_key)
            stored_hash = result if isinstance(result, str) else None
        else:
            result = await self.docstore.client.get(hash_key)
            stored_hash = result if isinstance(result, str) else None

        if stored_hash == file_hash:
            logger.debug(
                "file_already_ingested",
                filename=file_path.name,
                department=department.value,
            )
            return

        doc = Document(
            page_content=content,
            metadata={
                "department": department.value,
                "source_file": file_path.name,
            },
        )

        chunks = self.chunking_service.chunk_document(doc)

        parent_chunks = [c for c in chunks if c.metadata.get("chunk_type") == "parent"]
        child_chunks = [c for c in chunks if c.metadata.get("chunk_type") == "child"]

        if parent_chunks:
            parent_pairs = [
                (f"{department.value}:{chunk.id}", chunk) for chunk in parent_chunks
            ]
            self.docstore.mset(parent_pairs)

        if child_chunks:
            child_docs: list[dict[str, object]] = [
                {
                    "id": chunk.id,
                    "document": chunk.page_content,
                    "metadata": dict(chunk.metadata),
                }
                for chunk in child_chunks
            ]
            self.chroma_repo.add_documents(collection, child_docs)  # type: ignore[arg-type]

        if hasattr(self.docstore.client, "set"):
            _ = self.docstore.client.set(hash_key, file_hash)
        else:
            _ = await self.docstore.client.set(hash_key, file_hash)

        logger.info(
            "file_processed",
            filename=file_path.name,
            parent_chunks=len(parent_chunks),
            child_chunks=len(child_chunks),
        )
