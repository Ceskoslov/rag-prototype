"""Document and ingestion schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.schemas.common import Department


class DocumentMetadata(BaseModel):
    """Metadata for a document."""

    source: str = Field(..., description="Source document filename")
    department: Department = Field(
        ..., description="Department this document belongs to"
    )
    last_updated: Optional[str] = Field(None, description="Last update date")


class DocumentChunk(BaseModel):
    """A chunk of a document (for RAG retrieval)."""

    id: str = Field(..., description="Unique chunk ID")
    content: str = Field(..., description="Chunk content text")
    metadata: Optional[DocumentMetadata] = Field(None, description="Chunk metadata")


class IngestionRequest(BaseModel):
    """Request to ingest a document."""

    department: Department = Field(..., description="Target department")
    file_path: str = Field(..., description="Path to document file")


class IngestionResult(BaseModel):
    """Result of document ingestion."""

    department: Department = Field(..., description="Department that was updated")
    file_path: str = Field(..., description="Ingested file path")
    chunks_created: int = Field(..., description="Number of chunks created")
    status: str = Field(..., description="Ingestion status (success/failed)")
    error_message: Optional[str] = Field(None, description="Error message if failed")
