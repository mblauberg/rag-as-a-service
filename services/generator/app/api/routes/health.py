"""Health and readiness check endpoints."""
import logging
from fastapi import APIRouter
from app.models.schemas import HealthResponse, ReadinessResponse
from app.services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Ollama client for health checks
ollama_client = OllamaClient()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint (liveness probe).

    Returns:
        Health status
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check that validates Ollama connectivity.

    Returns:
        Readiness status with Ollama connection details
    """
    # Check Ollama connectivity
    ollama_connected = await ollama_client.check_health()

    status = "ready" if ollama_connected else "not_ready"

    logger.info(f"Readiness check: {status}, Ollama connected: {ollama_connected}")

    return ReadinessResponse(
        status=status,
        ollama_connected=ollama_connected
    )
