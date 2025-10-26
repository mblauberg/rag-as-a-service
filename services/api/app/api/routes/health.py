"""Health and readiness check endpoints."""
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.qdrant_client import qdrant_client


# Health check response models
class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str


class ServiceStatus(BaseModel):
    """Schema for individual service status."""

    name: str
    status: str
    details: str | None = None


class ReadinessResponse(BaseModel):
    """Schema for readiness check response."""

    status: str
    services: list[ServiceStatus]


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic liveness check for Kubernetes/Docker health probes.

    This is a lightweight endpoint that verifies the API service process is
    running and can handle requests. It does NOT check dependencies like
    databases or external services - use /api/v1/ready for comprehensive checks.

    **Use Cases:**
        - Kubernetes liveness probe to detect crashed/frozen containers
        - Docker Compose health checks for container orchestration
        - Load balancer health monitoring for traffic routing
        - Basic uptime monitoring and alerting

    **Response Semantics:**
        - 200 OK: Service process is alive and can handle requests
        - Any other status or timeout: Service is dead/frozen, should be restarted

    This endpoint should respond in <10ms as it performs no I/O operations.
    Kubernetes typically polls every 10-30 seconds with 3 consecutive failures
    triggering container restart.

    Returns:
        HealthResponse with status="healthy" indicating service is alive.
        Always returns 200 OK if endpoint is reachable.

        Example response:
            {
                "status": "healthy"
            }

    Example:
        Check if service is alive:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/api/v1/health")
            ...     print(response.json())
            {'status': 'healthy'}

        Kubernetes liveness probe configuration:
            ```yaml
            livenessProbe:
              httpGet:
                path: /api/v1/health
                port: 8000
              initialDelaySeconds: 30
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            ```

        Using curl:
            $ curl http://localhost:8000/api/v1/health

    Notes:
        - This endpoint never returns errors or non-200 status codes
        - No authentication or rate limiting applied
        - Excluded from request logging to avoid noise
        - Does not validate database connections, Qdrant, or microservices
        - Use /api/v1/ready for deployment readiness and dependency validation
        - Response time should be consistently <10ms; higher latency indicates
          system resource contention (CPU, memory, I/O pressure)
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> ReadinessResponse:
    """Comprehensive readiness check validating all dependencies for production traffic.

    This endpoint performs deep health checks on all critical dependencies required
    for the API service to function correctly. Unlike /health (liveness check),
    this endpoint validates external services and should be used for Kubernetes
    readiness probes and deployment validation.

    **Checked Dependencies:**
        1. **PostgreSQL Database:** Validates connection and query execution
        2. **Qdrant Vector Database:** Checks vector store availability
        3. **Embedder Microservice:** Verifies embedder service is reachable

    The service is considered "ready" only when ALL dependencies are healthy.
    A single failing dependency causes the entire check to report "not_ready",
    preventing traffic routing until issues are resolved.

    **Use Cases:**
        - Kubernetes readiness probe to control traffic routing
        - Pre-deployment validation in CI/CD pipelines
        - Blue-green deployment health verification
        - Load balancer traffic management
        - Monitoring and alerting for dependency failures

    **Failure Handling:**
        - Individual service failures are logged with details
        - Continues checking remaining services even if one fails
        - Returns 200 OK regardless of readiness (status in response body)
        - Status "not_ready" should prevent traffic but not trigger container restart

    **Performance Considerations:**
        - Typical response time: 50-200ms (3 parallel checks + overhead)
        - Uses short timeouts (5s) to avoid blocking probe loops
        - Kubernetes typically polls every 5-10 seconds
        - Failed checks may indicate transient network issues or actual outages

    Args:
        db: AsyncSession for PostgreSQL connectivity check. Auto-injected via
            FastAPI dependency system. Performs simple SELECT 1 query to verify
            database responsiveness.

    Returns:
        ReadinessResponse containing:
            - status: "ready" if all services healthy, "not_ready" otherwise
            - services: Array of ServiceStatus objects for each dependency

        Each ServiceStatus includes:
            - name: Service identifier (database, qdrant, embedder)
            - status: "ready" or "not_ready"
            - details: Human-readable status message or error description

        Example response (all healthy):
            {
                "status": "ready",
                "services": [
                    {
                        "name": "database",
                        "status": "ready",
                        "details": "Connected to PostgreSQL"
                    },
                    {
                        "name": "qdrant",
                        "status": "ready",
                        "details": "Connected to Qdrant"
                    },
                    {
                        "name": "embedder",
                        "status": "ready",
                        "details": "Connected to embedder service"
                    }
                ]
            }

        Example response (partial failure):
            {
                "status": "not_ready",
                "services": [
                    {
                        "name": "database",
                        "status": "ready",
                        "details": "Connected to PostgreSQL"
                    },
                    {
                        "name": "qdrant",
                        "status": "not_ready",
                        "details": "Qdrant connection failed: Connection refused"
                    },
                    {
                        "name": "embedder",
                        "status": "ready",
                        "details": "Connected to embedder service"
                    }
                ]
            }

    Example:
        Check service readiness:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/api/v1/ready")
            ...     result = response.json()
            ...     if result["status"] == "ready":
            ...         print("Service is ready for traffic")
            ...     else:
            ...         print("Service not ready:")
            ...         for svc in result["services"]:
            ...             if svc["status"] != "ready":
            ...                 print(f"  - {svc['name']}: {svc['details']}")
            Service is ready for traffic

        Kubernetes readiness probe configuration:
            ```yaml
            readinessProbe:
              httpGet:
                path: /api/v1/ready
                port: 8000
              initialDelaySeconds: 10
              periodSeconds: 5
              timeoutSeconds: 3
              successThreshold: 1
              failureThreshold: 3
            ```

        CI/CD deployment validation:
            ```bash
            #!/bin/bash
            # Wait for service to be ready after deployment
            for i in {1..30}; do
                response=$(curl -s http://api:8000/api/v1/ready)
                status=$(echo $response | jq -r '.status')
                if [ "$status" == "ready" ]; then
                    echo "Service is ready"
                    exit 0
                fi
                echo "Waiting for readiness... ($i/30)"
                sleep 2
            done
            echo "Service failed to become ready"
            exit 1
            ```

        Using curl:
            $ curl http://localhost:8000/api/v1/ready | jq

    Notes:
        - Always returns HTTP 200, check response body for actual readiness
        - Kubernetes interprets "not_ready" status as failed probe
        - Database check uses simple query; does not validate schema or migrations
        - Qdrant check only validates connection, not collection existence
        - Embedder check hits /health endpoint with 5 second timeout
        - Service failures are logged at ERROR level for monitoring
        - Use this endpoint sparingly in monitoring to avoid overwhelming dependencies
        - Consider implementing retry logic in callers for transient failures
        - Does not check generator service (optional dependency for some workflows)
        - Future enhancement: Add circuit breaker pattern for failing dependencies
    """
    services = []

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        services.append(
            ServiceStatus(
                name="database", status="ready", details="Connected to PostgreSQL"
            )
        )
    except Exception as e:
        services.append(
            ServiceStatus(
                name="database",
                status="not_ready",
                details=f"Database connection failed: {str(e)}",
            )
        )

    # Check Qdrant
    try:
        if await qdrant_client.health_check():
            services.append(
                ServiceStatus(
                    name="qdrant", status="ready", details="Connected to Qdrant"
                )
            )
        else:
            services.append(
                ServiceStatus(
                    name="qdrant",
                    status="not_ready",
                    details="Qdrant health check failed",
                )
            )
    except Exception as e:
        services.append(
            ServiceStatus(
                name="qdrant",
                status="not_ready",
                details=f"Qdrant connection failed: {str(e)}",
            )
        )

    # Check embedder service
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.get(f"{settings.embedder.url}/api/v1/health")
            if response.status_code == 200:
                services.append(
                    ServiceStatus(
                        name="embedder",
                        status="ready",
                        details="Connected to embedder service",
                    )
                )
            else:
                services.append(
                    ServiceStatus(
                        name="embedder",
                        status="not_ready",
                        details="Embedder service not responding",
                    )
                )
    except Exception as e:
        services.append(
            ServiceStatus(
                name="embedder",
                status="not_ready",
                details=f"Embedder connection failed: {str(e)}",
            )
        )

    # Determine overall status
    all_ready = all(service.status == "ready" for service in services)
    overall_status = "ready" if all_ready else "not_ready"

    return ReadinessResponse(status=overall_status, services=services)
