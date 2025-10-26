"""Tests for health check endpoints."""
import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy import text


@pytest.mark.asyncio
async def test_health_check(async_client):
    """
    Test basic health check endpoint (liveness probe).

    Verifies the service is running without checking dependencies.
    """
    response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    """
    Test root endpoint returns service information.

    Verifies API name, version, and docs link.
    """
    response = await async_client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert data["message"] == "RAAS API Gateway"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_readiness_check_all_services_healthy(async_client, mock_qdrant_client, mock_embedder_client):
    """
    Test readiness check when all services are healthy.

    Verifies database, Qdrant, and embedder connectivity.
    """
    response = await async_client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ready"
    assert len(data["services"]) == 3

    # Check each service status
    service_statuses = {svc["name"]: svc for svc in data["services"]}

    assert "database" in service_statuses
    assert service_statuses["database"]["status"] == "ready"
    assert "PostgreSQL" in service_statuses["database"]["details"]

    assert "qdrant" in service_statuses
    assert service_statuses["qdrant"]["status"] == "ready"
    assert "Qdrant" in service_statuses["qdrant"]["details"]

    assert "embedder" in service_statuses
    assert service_statuses["embedder"]["status"] == "ready"
    assert "embedder" in service_statuses["embedder"]["details"].lower()


@pytest.mark.asyncio
async def test_readiness_check_database_unavailable(
    async_client,
    db_session,
    mock_qdrant_client,
    mock_embedder_client,
    monkeypatch
):
    """
    Test readiness check when database is unavailable.

    Should report not_ready status with database failure details.
    """
    # Mock database to fail
    async def mock_db_execute(*args, **kwargs):
        raise Exception("Database connection failed")

    monkeypatch.setattr(db_session, "execute", mock_db_execute)

    response = await async_client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_ready"

    # Find database service status
    db_service = next(svc for svc in data["services"] if svc["name"] == "database")
    assert db_service["status"] == "not_ready"
    assert "failed" in db_service["details"].lower()


@pytest.mark.asyncio
async def test_readiness_check_qdrant_unavailable(
    async_client,
    mock_qdrant_client,
    mock_embedder_client
):
    """
    Test readiness check when Qdrant is unavailable.

    Should report not_ready status with Qdrant failure details.
    """
    # Mock Qdrant to fail
    mock_qdrant_client.health_check = AsyncMock(return_value=False)

    response = await async_client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_ready"

    # Find Qdrant service status
    qdrant_service = next(svc for svc in data["services"] if svc["name"] == "qdrant")
    assert qdrant_service["status"] == "not_ready"
    assert "failed" in qdrant_service["details"].lower()


@pytest.mark.asyncio
async def test_readiness_check_qdrant_exception(
    async_client,
    mock_qdrant_client,
    mock_embedder_client
):
    """
    Test readiness check when Qdrant raises exception.

    Should handle exception gracefully and report not_ready.
    """
    # Mock Qdrant to raise exception
    mock_qdrant_client.health_check = AsyncMock(side_effect=Exception("Connection timeout"))

    response = await async_client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_ready"

    # Find Qdrant service status
    qdrant_service = next(svc for svc in data["services"] if svc["name"] == "qdrant")
    assert qdrant_service["status"] == "not_ready"
    assert "timeout" in qdrant_service["details"].lower()


@pytest.mark.asyncio
async def test_readiness_check_embedder_unavailable(
    async_client,
    mock_qdrant_client,
    mock_embedder_client,
    monkeypatch
):
    """
    Test readiness check when embedder service is unavailable.

    Should report not_ready status with embedder failure details.
    """
    # Mock embedder health check to fail
    error_response = Mock()
    error_response.status_code = 500

    async def mock_get(*args, **kwargs):
        return error_response

    # Create mock client that returns error
    mock_http_client = AsyncMock()
    mock_http_client.get = mock_get
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=None)

    # Patch httpx.AsyncClient to return our mock
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: mock_http_client)

    response = await async_client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_ready"

    # Find embedder service status
    embedder_service = next(svc for svc in data["services"] if svc["name"] == "embedder")
    assert embedder_service["status"] == "not_ready"
    assert "not responding" in embedder_service["details"].lower()


@pytest.mark.asyncio
async def test_readiness_check_embedder_exception(
    async_client,
    mock_qdrant_client,
    mock_embedder_client,
    monkeypatch
):
    """
    Test readiness check when embedder service raises exception.

    Should handle exception gracefully and report not_ready.
    """
    # Create mock client that raises exception
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=Exception("Connection refused"))
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=None)

    # Patch httpx.AsyncClient to return our mock
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: mock_http_client)

    response = await async_client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_ready"

    # Find embedder service status
    embedder_service = next(svc for svc in data["services"] if svc["name"] == "embedder")
    assert embedder_service["status"] == "not_ready"
    assert "refused" in embedder_service["details"].lower()


@pytest.mark.asyncio
async def test_readiness_check_multiple_services_down(
    async_client,
    mock_qdrant_client,
    mock_embedder_client,
    db_session,
    monkeypatch
):
    """
    Test readiness check when multiple services are down.

    Should report not_ready with details for each failed service.
    """
    # Mock database to fail
    async def mock_db_execute(*args, **kwargs):
        raise Exception("Database unavailable")

    monkeypatch.setattr(db_session, "execute", mock_db_execute)

    # Mock Qdrant to fail
    mock_qdrant_client.health_check = AsyncMock(return_value=False)

    # Create mock HTTP client that raises exception
    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=Exception("Embedder down"))
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=None)

    # Patch httpx.AsyncClient to return our mock
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: mock_http_client)

    response = await async_client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_ready"

    # Verify all services report not_ready
    for service in data["services"]:
        assert service["status"] == "not_ready"
        assert service["details"] is not None
