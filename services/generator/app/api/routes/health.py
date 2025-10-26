"""Health and readiness check endpoints."""
import logging
from fastapi import APIRouter
from app.models.schemas import HealthResponse, ReadinessResponse
import app.services.generation_service as gen_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint (liveness probe).

    Returns:
        Health status
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check that validates provider availability.

    Returns:
        Readiness status with number of available providers
    """
    # Count available providers from the global registry
    num_providers = len(gen_service.provider_registry.providers) if gen_service.provider_registry else 0

    status = "ready" if num_providers > 0 else "not_ready"

    logger.info(f"Readiness check: {status}, Providers available: {num_providers}")

    return ReadinessResponse(
        status=status,
        providers_available=num_providers
    )
