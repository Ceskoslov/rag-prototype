"""API key authentication middleware using FastAPI dependencies."""

import secrets

from fastapi import Header, HTTPException, status

from app.core.settings import settings


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """
    Verify API key from request header using timing-safe comparison.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        The API key if valid

    Raises:
        HTTPException: 401 if key missing, 403 if key invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return x_api_key
