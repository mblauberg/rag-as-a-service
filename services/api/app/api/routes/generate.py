"""Summary generation endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_chunk_repository
from app.api.models import GenerateSummaryRequest, GenerateSummaryResponse
from app.ports.repositories import ChunkRepository
from app.services.generator_client import GeneratorClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/summary", response_model=GenerateSummaryResponse)
async def generate_summary(
    request: GenerateSummaryRequest,
    chunk_repository: ChunkRepository = Depends(get_chunk_repository),
) -> GenerateSummaryResponse:
    """Generate AI summary from search results.

    This endpoint:
    1. Fetches chunk content by IDs from the repository
    2. Formats chunks for the generator service
    3. Calls GeneratorClient.generate_summary()
    4. Returns summary with model attribution

    Args:
        request: Summary generation request with query, chunk IDs, and model
        chunk_repository: Injected chunk repository

    Returns:
        Generated summary and model used

    Raises:
        HTTPException 404: Chunk IDs not found
        HTTPException 503: Generator service unavailable
    """
    # Fetch chunks
    chunks = await chunk_repository.get_chunks_by_ids(request.chunk_ids)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chunks found for provided IDs",
        )

    if len(chunks) != len(request.chunk_ids):
        logger.warning(
            f"Only found {len(chunks)} of {len(request.chunk_ids)} requested chunks"
        )

    # Format chunks for generator
    chunk_data = [
        {
            "text": chunk.content,
            "document_id": str(chunk.document_id),
            "chunk_index": chunk.metadata.get("chunk_index", 0),
        }
        for chunk in chunks
    ]

    # Call generator service
    generator_client = GeneratorClient()
    result = await generator_client.generate_summary(
        query=request.query, chunks=chunk_data, model=request.model
    )

    if not result:
        logger.error(f"Generator service failed for model {request.model}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Summary generation service unavailable",
        )

    return GenerateSummaryResponse(
        summary=result.get("summary", ""),
        model_used=result.get("model_used", request.model),
    )
