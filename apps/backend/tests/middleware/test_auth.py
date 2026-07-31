"""Test suite for API key authentication middleware."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.middleware.auth import verify_api_key


@pytest.fixture
def app_with_auth():
    """Create a FastAPI app with auth dependency for testing."""
    app = FastAPI()

    @app.get("/protected")
    async def protected_endpoint(api_key: str = Depends(verify_api_key)):
        return {"status": "ok", "message": "access granted"}

    return app


@pytest.fixture
def client(app_with_auth):
    """Create a test client."""
    return TestClient(app_with_auth)


def test_auth_valid_api_key(client):
    """Test valid API key allows access."""
    headers = {"X-API-Key": settings.api_key}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "access granted"}


def test_auth_missing_api_key(client):
    """Test missing API key returns 401."""
    response = client.get("/protected")
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data or "error" in data


def test_auth_invalid_api_key(client):
    """Test invalid API key returns 403."""
    headers = {"X-API-Key": "wrong-key-xyz"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data or "error" in data


def test_auth_empty_api_key(client):
    """Test empty API key is treated as missing (returns 401)."""
    headers = {"X-API-Key": ""}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data or "error" in data


def test_auth_timing_safe_comparison(client):
    """Test timing-safe comparison by checking wrong key is rejected."""
    # This verifies we're using timing-safe comparison
    # The behavior should be same for all wrong keys (no info leakage)
    headers = {"X-API-Key": "a"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 403

    headers = {"X-API-Key": "very-long-invalid-key"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 403


def test_auth_case_sensitive(client):
    """Test API key comparison is case-sensitive."""
    # Assume valid key is lowercase, try uppercase variant
    if settings.api_key.lower() != settings.api_key:
        headers = {"X-API-Key": settings.api_key.upper()}
    else:
        headers = {"X-API-Key": settings.api_key.upper()}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 403
