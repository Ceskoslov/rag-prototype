"""Common type definitions and enums."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class Department(str, Enum):
    """Department enum with 4 required values."""

    IT_SUPPORT = "it_support"
    LEGAL = "legal"
    CREDIT_CARD = "credit_card"
    AIRPORT_GROUND = "airport_ground"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    detail: Optional[str] = Field(None, description="Additional error details")
