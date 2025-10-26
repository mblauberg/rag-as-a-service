"""Models listing endpoint."""
import logging

from fastapi import APIRouter, HTTPException

from app.services.generator_client import GeneratorClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/models")
async def list_models() -> dict[str, list[dict[str, str]]]:
    """
    List available LLM models from Generator service.

    Returns:
        List of available models with metadata
    """
    try:
        generator_client = GeneratorClient()
        models = await generator_client.list_models()

        return {"models": models}

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve model list"
        )
