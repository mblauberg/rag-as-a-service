"""Models listing endpoint."""
import logging

from fastapi import APIRouter, HTTPException, status

from app.api.models import ModelsListResponse
from app.core.exceptions import GenerationServiceError
from app.services.generator_client import GeneratorClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/models", response_model=ModelsListResponse)
async def list_models() -> ModelsListResponse:
    """
    List available LLM models from Generator service.

    Returns:
        List of available models with metadata
    """
    try:
        generator_client = GeneratorClient()
        models = await generator_client.list_models()

        return ModelsListResponse(models=models)  # type: ignore[arg-type]

    except GenerationServiceError as e:
        logger.error(f"Generation service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Generator service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model list"
        )
