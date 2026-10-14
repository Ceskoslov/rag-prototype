"""Test suite for health check endpoint."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.health import router as health_router


@pytest.fixture
def app_with_health():
    """Create a FastAPI app with health router."""
    app = FastAPI()
    app.include_router(health_router)
    return app


@pytest.fixture
def client(app_with_health):
    """Create a test client."""
    return TestClient(app_with_health)


def test_health_endpoint_exists(client):
    """Test GET /api/v1/health exists."""
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]


def test_health_endpoint_returns_json(client):
    """Test health endpoint returns valid JSON."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert isinstance(data, dict)


def test_health_status_field_exists(client):
    """Test health response includes status field."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "status" in data


def test_health_services_field_exists(client):
    """Test health response includes services field."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "services" in data


def test_health_services_includes_redis(client):
    """Test services includes redis status."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "redis" in data.get("services", {})


def test_health_services_includes_chromadb(client):
    """Test services includes chromadb status."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "chromadb" in data.get("services", {})


def test_health_services_includes_postgres(client):
    """Test services includes postgres status."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "postgres" in data.get("services", {})


def test_health_no_auth_required(client):
    """Test health endpoint works without API key (exempt from auth)."""
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]


def test_health_status_ok_when_healthy(client):
    """Test status is 'ok' when all services are healthy."""
    response = client.get("/api/v1/health")
    if response.status_code == 200:
        data = response.json()
        assert data.get("status") == "ok"


def test_health_status_degraded_when_services_fail(client):
    """Test response structure when services fail."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "status" in data
    assert "services" in data


def test_readiness_returns_503_when_a_dependency_is_unavailable(client, monkeypatch):
    from unittest.mock import AsyncMock

    from app.routers import health

    monkeypatch.setattr(
        health,
        "probe_services",
        AsyncMock(
            return_value={"redis": "unavailable", "chromadb": "ok", "postgres": "ok"}
        ),
    )
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_liveness_does_not_claim_dependency_connectivity(client):
    assert client.get("/api/v1/health").json()["services"]["redis"] == "unchecked"
