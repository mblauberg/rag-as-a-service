"""Health and readiness check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.qdrant_client import qdrant_client
from app.services.embedder_client import embedder_client
from app.models.schemas import HealthResponse, ReadinessResponse, ServiceStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check that validates connectivity to dependencies.

    Args:
        db: Database session

    Returns:
        Readiness status with service details
    """
    services = []

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        services.append(ServiceStatus(
            name="database",
            status="ready",
            details="Connected to PostgreSQL"
        ))
    except Exception as e:
        services.append(ServiceStatus(
            name="database",
            status="not_ready",
            details=f"Database connection failed: {str(e)}"
        ))

    # Check Qdrant
    try:
        if qdrant_client.health_check():
            services.append(ServiceStatus(
                name="qdrant",
                status="ready",
                details="Connected to Qdrant"
            ))
        else:
            services.append(ServiceStatus(
                name="qdrant",
                status="not_ready",
                details="Qdrant health check failed"
            ))
    except Exception as e:
        services.append(ServiceStatus(
            name="qdrant",
            status="not_ready",
            details=f"Qdrant connection failed: {str(e)}"
        ))

    # Check embedder service
    try:
        if await embedder_client.health_check():
            services.append(ServiceStatus(
                name="embedder",
                status="ready",
                details="Connected to embedder service"
            ))
        else:
            services.append(ServiceStatus(
                name="embedder",
                status="not_ready",
                details="Embedder service not responding"
            ))
    except Exception as e:
        services.append(ServiceStatus(
            name="embedder",
            status="not_ready",
            details=f"Embedder connection failed: {str(e)}"
        ))

    # Determine overall status
    all_ready = all(service.status == "ready" for service in services)
    overall_status = "ready" if all_ready else "not_ready"

    return ReadinessResponse(
        status=overall_status,
        services=services
    )
