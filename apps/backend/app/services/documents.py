from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from app.core.docstore import RedisDocStore
from app.repositories.vectorstore import ChromaRepository
from app.schemas.common import normalize_knowledge_base
from app.services.ingestion import SUPPORTED_EXTENSIONS


class DocumentService:
    def __init__(
        self, data_dir: Path, repository: ChromaRepository, store: RedisDocStore
    ):
        self.data_dir = data_dir.resolve()
        self.repository = repository
        self.store = store

    def file_path(self, knowledge_base: str, source_path: str) -> Path:
        base = self.data_dir / normalize_knowledge_base(knowledge_base)
        relative = Path(source_path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not source_path
            or "\\" in source_path
        ):
            raise ValueError("Invalid document path")
        path = (base / relative).resolve()
        if not path.is_relative_to(base) or not base.resolve().is_relative_to(
            self.data_dir
        ):
            raise ValueError("Document path escapes knowledge base")
        if path.suffix.casefold() not in SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported document format")
        return path

    def list_documents(self, knowledge_base: str) -> list[dict]:
        base = self.data_dir / normalize_knowledge_base(knowledge_base)
        record = self.repository.index_record(knowledge_base)
        manifest = json.loads(record["manifest"]) if record else {"files": {}}
        if not base.exists():
            return []
        items = []
        for file in sorted(base.rglob("*")):
            if not file.is_file() or file.suffix.casefold() not in SUPPORTED_EXTENSIONS:
                continue
            source = file.relative_to(base).as_posix()
            safe = self.file_path(knowledge_base, source)
            items.append(
                {
                    "source_path": source,
                    "size": safe.stat().st_size,
                    "indexed": manifest["files"].get(source)
                    == hashlib.sha256(safe.read_bytes()).hexdigest(),
                }
            )
        return items

    def write(self, knowledge_base: str, source_path: str, content: bytes) -> None:
        path = self.file_path(knowledge_base, source_path)
        lock = self.store.client.lock(
            f"ingest_lock:{normalize_knowledge_base(knowledge_base)}", timeout=60
        )
        if not lock.acquire(blocking=False):
            raise ValueError(
                "Knowledge base is currently indexing; retry after the job finishes"
            )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file:
                file.write(content)
                temporary = file.name
            try:
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        finally:
            lock.release()

    def delete(self, knowledge_base: str, source_path: str) -> None:
        path = self.file_path(knowledge_base, source_path)
        lock = self.store.client.lock(
            f"ingest_lock:{normalize_knowledge_base(knowledge_base)}", timeout=60
        )
        if not lock.acquire(blocking=False):
            raise ValueError(
                "Knowledge base is currently indexing; retry after the job finishes"
            )
        try:
            path.unlink()
        finally:
            lock.release()
