import hashlib
from typing import cast

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


class ChunkingService:
    def __init__(
        self,
        parent_chunk_size: int = 1200,
        parent_chunk_overlap: int = 160,
        child_chunk_size: int = 320,
        child_chunk_overlap: int = 64,
    ) -> None:
        parent_chunk_overlap = min(parent_chunk_overlap, parent_chunk_size - 1)
        child_chunk_overlap = min(child_chunk_overlap, child_chunk_size - 1)
        self._markdown_splitter: MarkdownHeaderTextSplitter = (
            MarkdownHeaderTextSplitter(
                headers_to_split_on=[
                    ("#", "header_1"),
                    ("##", "header_2"),
                    ("###", "header_3"),
                    ("####", "header_4"),
                ],
                strip_headers=False,
            )
        )
        self._parent_splitter: RecursiveCharacterTextSplitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=parent_chunk_size,
                chunk_overlap=parent_chunk_overlap,
            )
        )
        self._child_splitter: RecursiveCharacterTextSplitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=child_chunk_size,
                chunk_overlap=child_chunk_overlap,
            )
        )

    def chunk_document(self, doc: Document) -> list[Document]:
        metadata = cast(dict[str, object], doc.metadata)
        knowledge_base = self._normalize_optional_str(
            metadata.get("knowledge_base") or metadata.get("department")
        )
        source_file = self._normalize_optional_str(
            metadata.get("source_file") or metadata.get("source")
        )
        source_path = self._normalize_optional_str(
            metadata.get("source_path") or source_file
        )

        header_docs = self._markdown_splitter.split_text(doc.page_content)
        if not header_docs:
            header_docs = [Document(page_content=doc.page_content, metadata={})]

        parent_docs = self._parent_splitter.split_documents(header_docs)

        chunks: list[Document] = []
        child_index = 0
        for parent_index, parent_doc in enumerate(parent_docs):
            parent_id = self._stable_id(
                "parent",
                knowledge_base,
                source_path,
                str(parent_index),
                parent_doc.page_content,
            )
            parent_metadata: dict[str, object] = {
                **metadata,
                **parent_doc.metadata,
                "knowledge_base": knowledge_base,
                "source_file": source_file,
                "source_path": source_path,
                "chunk_type": "parent",
                "chunk_index": parent_index,
            }
            parent_chunk = Document(
                id=parent_id,
                page_content=parent_doc.page_content,
                metadata=parent_metadata,
            )
            chunks.append(parent_chunk)

            child_docs = self._child_splitter.split_documents([parent_doc])
            for child_doc in child_docs:
                child_id = self._stable_id(
                    "child",
                    knowledge_base,
                    source_path,
                    str(parent_index),
                    str(child_index),
                    child_doc.page_content,
                )
                child_chunk = Document(
                    id=child_id,
                    page_content=child_doc.page_content,
                    metadata={
                        **metadata,
                        **child_doc.metadata,
                        "knowledge_base": knowledge_base,
                        "source_file": source_file,
                        "source_path": source_path,
                        "chunk_type": "child",
                        "chunk_index": child_index,
                        "parent_id": parent_id,
                    },
                )
                chunks.append(child_chunk)
                child_index += 1

        return chunks

    @staticmethod
    def _stable_id(prefix: str, *parts: object) -> str:
        digest = hashlib.sha256(
            "\x1f".join(str(part or "") for part in parts).encode("utf-8")
        ).hexdigest()
        return f"{prefix}_{digest[:32]}"

    @staticmethod
    def _normalize_optional_str(value: object) -> str | None:
        if value is None:
            return None
        return str(value)
