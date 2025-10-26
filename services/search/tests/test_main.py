"""Tests for FastAPI application."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


@pytest.fixture
def mock_orchestrator():
    """Mock search orchestrator."""
    orchestrator = MagicMock()
    orchestrator.search = AsyncMock(return_value=[])
    return orchestrator


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_search_endpoint_requires_query():
    """Test search endpoint validates query."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/search", json={})

    assert response.status_code == 422  # Validation error
