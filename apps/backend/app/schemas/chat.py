"""Chat request/response schemas and agent trace."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.common import Department


class ChatRequest(BaseModel):
    """Chat request from client."""

    message: str = Field(..., description="User's chat message")
    department: Optional[Department] = Field(
        None, description="Target department (optional)"
    )
    session_id: Optional[str] = Field(
        None, description="Session ID for context tracking"
    )


class AgentTrace(BaseModel):
    """Trace of agent execution during request."""

    supervisor_decision: str = Field(..., description="Supervisor's routing decision")
    agents_invoked: List[str] = Field(
        ..., description="List of agents that were invoked"
    )
    retrieval_sources: List[Dict[str, Any]] = Field(
        ..., description="Sources retrieved from knowledge base"
    )
    iterations: int = Field(..., description="Number of iterations/refinement cycles")


class ChatResponse(BaseModel):
    """Chat response from API."""

    answer: str = Field(..., description="Generated answer")
    department: Department = Field(..., description="Department that handled the query")
    sources: List[str] = Field(..., description="Source documents used")
    confidence: float = Field(..., description="Confidence score for the answer")
    trace: AgentTrace = Field(..., description="Trace of agent execution")
    session_id: Optional[str] = Field(
        None,
        description="Session ID for conversation continuity",
    )


class ChatStreamEvent(BaseModel):
    """Event for streaming chat responses."""

    type: str = Field(..., description="Event type (token, done, error)")
    data: Optional[str] = Field(
        None, description="Event data (token text or error message)"
    )
