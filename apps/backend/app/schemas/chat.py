"""Chat request/response schemas and RAG trace."""

from typing import Any

from pydantic import AliasChoices, BaseModel, Field

from app.schemas.common import KnowledgeBaseName


class ChatRequest(BaseModel):
    """Chat request from client."""

    message: str = Field(..., min_length=1, max_length=20_000)
    knowledge_base: KnowledgeBaseName | None = Field(
        None,
        description="Optional knowledge-base slug; omit to search every knowledge base",
        validation_alias=AliasChoices("knowledge_base", "department"),
    )
    session_id: str | None = Field(
        None, description="Session ID for context tracking"
    )


class AgentTrace(BaseModel):
    """Observable execution details for one RAG request."""

    knowledge_bases_searched: list[str] = Field(
        default_factory=list,
        description="Knowledge bases considered during retrieval",
    )
    retrieval_sources: list[dict[str, Any]] = Field(
        ..., description="Sources retrieved from knowledge base"
    )
    iterations: int = Field(..., description="Number of iterations/refinement cycles")
    pipeline_steps: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Chat response from API."""

    answer: str = Field(..., description="Generated answer")
    knowledge_bases: list[str] = Field(
        default_factory=list,
        description="Knowledge bases used to answer the query",
    )
    sources: list[str] = Field(..., description="Source documents used")
    confidence: float = Field(..., description="Confidence score for the answer")
    trace: AgentTrace = Field(..., description="Trace of agent execution")
    session_id: str | None = Field(
        None,
        description="Session ID for conversation continuity",
    )


class ChatStreamEvent(BaseModel):
    """Event for streaming chat responses."""

    type: str = Field(..., description="Event type (token, done, error)")
    data: str | None = Field(
        None, description="Event data (token text or error message)"
    )
