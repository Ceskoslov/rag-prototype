"""Document and ingestion schemas."""


from pydantic import BaseModel, Field

from app.schemas.common import KnowledgeBaseName


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    source: str = Field(..., description="Source document filename")
    knowledge_base: KnowledgeBaseName = Field(
        ..., description="Knowledge base this document belongs to"
    )
    last_updated: str | None = Field(None, description="Last update date")


class DocumentChunk(BaseModel):
    """A chunk of a document (for RAG retrieval)."""

    id: str = Field(..., description="Unique chunk ID")
    content: str = Field(..., description="Chunk content text")
    metadata: DocumentMetadata | None = Field(None, description="Chunk metadata")


class IngestionRequest(BaseModel):
    """Request to ingest a document."""

    knowledge_base: KnowledgeBaseName = Field(..., description="Target knowledge base")
    file_path: str = Field(..., description="Path to document file")


class IngestionResult(BaseModel):
    """Result of document ingestion."""

    knowledge_base: KnowledgeBaseName = Field(
        ..., description="Knowledge base that was updated"
    )
    file_path: str = Field(..., description="Ingested file path")
    chunks_created: int = Field(..., description="Number of chunks created")
    status: str = Field(..., description="Ingestion status (success/failed)")
    error_message: str | None = Field(None, description="Error message if failed")
