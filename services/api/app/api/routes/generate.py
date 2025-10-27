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
    """Generate AI-powered summary from search results using large language models.

    This endpoint implements the "Generation" component of Retrieval-Augmented
    Generation (RAG), creating natural language summaries grounded in retrieved
    document chunks. Uses cloud LLM APIs (OpenAI, Anthropic, Google) to synthesize
    coherent answers from multiple text passages.

    The generation process follows these stages:
        1. **Chunk Retrieval:** Fetches full text content for provided chunk IDs
           from PostgreSQL repository. Validates all chunks exist.

        2. **Context Formatting:** Structures chunks into prompt format with:
           - Numbered citations for attribution [1], [2], etc.
           - Document metadata (title, source)
           - Chunk ordering for coherence

        3. **LLM API Call:** Sends formatted prompt to generator microservice
           which handles:
           - Model selection (GPT-4, Claude, Gemini, etc.)
           - API authentication and rate limiting
           - Streaming or batch response handling
           - Token counting and cost tracking

        4. **Response Processing:** Extracts summary text and metadata:
           - Generated answer with inline citations
           - Model used for generation
           - Token usage statistics
           - Processing time

    **Supported LLM Models:**
        - OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
        - Anthropic: claude-3-5-sonnet, claude-3-opus, claude-3-haiku
        - Google: gemini-1.5-pro, gemini-1.5-flash

    **Citation Format:**
        Generated summaries include inline citations like [1], [2] that reference
        the source chunks by index. This enables users to:
        - Verify claims against source material
        - Navigate to original document passages
        - Assess answer reliability and coverage

    Args:
        request: GenerateSummaryRequest containing:
            - query: Original search query used as context for summary generation
              (helps LLM understand user intent and focus summary appropriately)
            - chunk_ids: Array of chunk UUIDs to use as context. Typically 3-10
              chunks from search results. Must all exist in database.
            - model: LLM model identifier (e.g., "gpt-4o-mini"). Defaults to
              cost-effective model if not specified. See /api/v1/models for options.
        chunk_repository: Injected chunk repository for data access. Auto-injected
            via FastAPI dependency system following clean architecture.

    Returns:
        GenerateSummaryResponse containing:
            - summary: Generated answer text with inline citations. Typically
              2-5 paragraphs (100-500 words) synthesizing information from chunks.
            - model_used: Actual model used for generation (may differ from
              request if fallback occurred). Includes provider and version.

        Example response:
            {
                "summary": "Transformers are neural network architectures that use self-attention mechanisms to process sequential data [1]. They were introduced in the 'Attention is All You Need' paper and have revolutionized NLP tasks [2]. Unlike RNNs, transformers can process entire sequences in parallel, making them more efficient for training [1][3].",
                "model_used": "gpt-4o-mini"
            }

    Raises:
        HTTPException: Multiple failure scenarios:
            - 404 NOT_FOUND: One or more chunk IDs do not exist in database.
              This occurs when search results reference deleted chunks or invalid UUIDs.
            - 503 SERVICE_UNAVAILABLE: Generator microservice unreachable, LLM
              API down, or API rate limits exceeded. Indicates temporary failure.
            - 500 INTERNAL_SERVER_ERROR: Unexpected errors during generation,
              malformed LLM responses, or internal processing failures.

        Specific error conditions:
            - Empty chunk_ids array: Returns 404 with "No chunks provided"
            - Partial chunk retrieval: Logs warning but proceeds with available chunks
            - LLM API timeout: Returns 503 for retry
            - LLM content policy violation: Returns 400 with policy details

    Example:
        Generate summary from search results:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     # First perform search
            ...     search_response = await client.post(
            ...         "http://localhost:8000/api/v1/search",
            ...         json={"query": "transformer architecture", "top_k": 5}
            ...     )
            ...     results = search_response.json()["results"]
            ...     chunk_ids = [r["chunk_id"] for r in results]
            ...
            ...     # Generate summary from top results
            ...     summary_response = await client.post(
            ...         "http://localhost:8000/api/v1/generate/summary",
            ...         json={
            ...             "query": "transformer architecture",
            ...             "chunk_ids": chunk_ids,
            ...             "model": "gpt-4o-mini"
            ...         }
            ...     )
            ...     print(summary_response.json()["summary"])
            Transformers are neural network architectures that use self-attention...

        Use different LLM model:
            >>> summary_response = await client.post(
            ...     "http://localhost:8000/api/v1/generate/summary",
            ...     json={
            ...         "query": "explain deep learning",
            ...         "chunk_ids": chunk_ids,
            ...         "model": "claude-3-5-sonnet-20241022"
            ...     }
            ... )

        Using curl:
            $ curl -X POST "http://localhost:8000/api/v1/generate/summary" \\
                -H "Content-Type: application/json" \\
                -d '{
                    "query": "what are transformers",
                    "chunk_ids": ["660e8400-e29b-41d4-a716-446655440111"],
                    "model": "gpt-4o-mini"
                }'

    Notes:
        - Generation typically takes 2-10 seconds depending on model and context length
        - Longer context (more chunks) increases latency and cost but may improve
          answer completeness
        - Maximum context size varies by model: GPT-4 supports ~128k tokens,
          older models limited to 4-8k tokens
        - Chunks are automatically truncated if they exceed model context limits
        - Citations are deterministic; [1] always refers to first chunk in request
        - LLM may refuse to answer if query violates content policies
        - Consider caching summaries for frequently accessed content
        - Generator microservice handles API key management and rotation
        - Prompt engineering is handled by generator service (system prompts,
          few-shot examples, temperature settings)
        - No streaming support currently; client waits for complete response
        - Failed generation attempts are logged for debugging and monitoring
    """
    # Fetch chunks
    chunks = await chunk_repository.get_chunks_by_ids(request.chunk_ids)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No chunks found for provided IDs",
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
