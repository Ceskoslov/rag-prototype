from langchain_core.documents import Document

from app.services.chunking import ChunkingService


def test_chunking_is_deterministic_and_preserves_generic_metadata():
    service = ChunkingService(parent_chunk_size=80, child_chunk_size=40)
    document = Document(
        page_content="# Guide\n" + ("Reusable knowledge. " * 20),
        metadata={
            "knowledge_base": "product_docs",
            "source_path": "guide.md",
        },
    )

    first = service.chunk_document(document)
    second = service.chunk_document(document)

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert all(
        chunk.metadata["knowledge_base"] == "product_docs" for chunk in first
    )
    assert any(chunk.metadata["chunk_type"] == "parent" for chunk in first)
    assert any(chunk.metadata["chunk_type"] == "child" for chunk in first)
