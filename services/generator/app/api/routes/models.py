"""Model listing endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ModelsResponse
from app.services.generation_service import GenerationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize generation service
generation_service = GenerationService()


@router.get("/", response_model=ModelsResponse)
async def list_models():
    """
    List available Ollama models.

    Returns:
        List of available models with metadata

    Raises:
        HTTPException: If model listing fails
    """
    try:
        logger.info("Listing available models")
        response = await generation_service.list_available_models()
        logger.info(f"Found {len(response.models)} models")
        return response

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )
