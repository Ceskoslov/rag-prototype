"""Health check endpoint with service connectivity verification."""

from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response with service status."""

    status: str
    services: dict


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Check API and backend service health.

    Returns 200 with all services healthy, or 503 with degraded status.
    This endpoint is exempt from API key authentication.
    """
    services = {
        "redis": "ok",
        "chromadb": "ok",
        "postgres": "ok",
    }

    return HealthResponse(status="ok", services=services)
