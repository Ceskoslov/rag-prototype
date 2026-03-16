from typing import cast
from uuid import uuid4

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


from app.schemas.common import Department


class ChunkingService:
    def __init__(self) -> None:
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
                chunk_size=1000,
                chunk_overlap=200,
            )
        )
        self._child_splitter: RecursiveCharacterTextSplitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=200,
                chunk_overlap=50,
            )
        )

    def chunk_document(self, doc: Document) -> list[Document]:
        metadata = cast(dict[str, object], doc.metadata)
        department = self._normalize_department(metadata.get("department"))
        source_file = self._normalize_optional_str(
            metadata.get("source_file") or metadata.get("source")
        )

        header_docs = self._markdown_splitter.split_text(doc.page_content)
        if not header_docs:
            header_docs = [Document(page_content=doc.page_content, metadata={})]

        parent_docs = self._parent_splitter.split_documents(header_docs)

        chunks: list[Document] = []
        child_index = 0
        for parent_index, parent_doc in enumerate(parent_docs):
            parent_id = f"parent_{uuid4().hex}"
            parent_metadata: dict[str, str | int | None] = {
                "department": department,
                "source_file": source_file,
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
                child_chunk = Document(
                    id=f"child_{uuid4().hex}",
                    page_content=child_doc.page_content,
                    metadata={
                        "department": department,
                        "source_file": source_file,
                        "chunk_type": "child",
                        "chunk_index": child_index,
                        "parent_id": parent_id,
                    },
                )
                chunks.append(child_chunk)
                child_index += 1

        return chunks

    @staticmethod
    def _normalize_department(department: object) -> str | None:
        if department is None:
            return None
        if isinstance(department, Department):
            return department.value
        return str(department)

    @staticmethod
    def _normalize_optional_str(value: object) -> str | None:
        if value is None:
            return None
        return str(value)
