"""Generation endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize prompt service for building context
prompt_service = PromptService()


@router.post("/", response_model=GenerateResponse)
async def generate_summary(request: GenerateRequest):
    """
    Generate summary from document chunks using specified model via provider registry.

    Args:
        request: Generation request with query, chunks, and model

    Returns:
        Generated summary with metadata

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Import here to avoid circular dependency
        from app.main import provider_registry

        logger.info(f"Generating summary for query: {request.query[:50]}...")
        logger.info(f"Using model: {request.model}, chunks: {len(request.chunks)}")

        # Build context from chunks
        context = prompt_service.build_rag_prompt(request.query, request.chunks)

        # Use registry to route to appropriate provider
        summary, provider_used = await provider_registry.generate(
            model_name=request.model,
            prompt=request.query,
            context=context
        )

        logger.info(f"Generated summary using {provider_used} provider")

        # Estimate tokens used (rough approximation: 1 token ≈ 4 characters)
        tokens_estimate = (len(request.query) + len(context) + len(summary)) // 4

        return GenerateResponse(
            summary=summary,
            model_used=request.model,
            tokens_used=tokens_estimate
        )

    except ValueError as e:
        logger.error(f"Provider not found: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}"
        )
