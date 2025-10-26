"""Model listing endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ModelsResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """
    List all available models from all providers.

    Returns:
        List of available models with metadata

    Raises:
        HTTPException: If model listing fails
    """
    try:
        # Import here to avoid circular dependency
        from app.main import provider_registry

        logger.info("Listing available models from all providers")
        models = await provider_registry.list_all_models()
        logger.info(f"Found {len(models)} models across {len(provider_registry.providers)} providers")
        return ModelsResponse(models=models)

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )
