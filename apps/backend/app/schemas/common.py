"""Common API types."""

import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

_KNOWLEDGE_BASE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")


def normalize_knowledge_base(value: str) -> str:
    """Normalize and validate a user-configurable knowledge-base slug."""

    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    if not _KNOWLEDGE_BASE_PATTERN.fullmatch(normalized):
        raise ValueError(
            "knowledge base must start with a letter or number and contain only "
            "lowercase letters, numbers, underscores, or hyphens"
        )
    return normalized


KnowledgeBaseName = Annotated[str, AfterValidator(normalize_knowledge_base)]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    detail: str | None = Field(None, description="Additional error details")
