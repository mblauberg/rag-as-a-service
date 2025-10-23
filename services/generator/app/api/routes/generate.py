"""Generation endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.generation_service import GenerationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize generation service
generation_service = GenerationService()


@router.post("/", response_model=GenerateResponse)
async def generate_summary(request: GenerateRequest):
    """
    Generate summary from document chunks using LLM.

    Args:
        request: Generation request with query, chunks, and model

    Returns:
        Generated summary with metadata

    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"Generating summary for query: {request.query[:50]}...")
        logger.info(f"Using model: {request.model}, chunks: {len(request.chunks)}")

        response = await generation_service.generate_summary(
            query=request.query,
            chunks=request.chunks,
            model=request.model
        )

        return response

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
