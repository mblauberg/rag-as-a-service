"""Models listing endpoint."""
import logging

from fastapi import APIRouter, HTTPException, status

from app.api.models import ModelsListResponse
from app.core.exceptions import GenerationServiceError
from app.services.generator_client import GeneratorClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/models",
    response_model=ModelsListResponse,
    summary="List available LLM models",
    description="""
    List all available LLM models for summary generation with capabilities.

    **Model Categories:**
    - Flagship: Highest quality, premium pricing (GPT-4, Claude Opus)
    - Balanced: Good quality/cost ratio (GPT-4o-mini, Claude Sonnet)
    - Fast: Lower latency, economical (GPT-3.5, Claude Haiku)
    - Open Source: Self-hosted via Ollama (Llama 3, Mistral)
    """,
    responses={
        200: {
            "description": "List of available models retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "models": [
                            {
                                "model_id": "gpt-4o-mini",
                                "display_name": "GPT-4 Omni Mini",
                                "provider": "openai",
                                "max_tokens": 128000,
                                "supports_streaming": True,
                                "cost_per_1k_tokens": 0.0002,
                                "recommended": True,
                                "description": "Fast and affordable model, good for most tasks"
                            },
                            {
                                "model_id": "claude-3-5-sonnet-20241022",
                                "display_name": "Claude 3.5 Sonnet",
                                "provider": "anthropic",
                                "max_tokens": 200000,
                                "supports_streaming": True,
                                "cost_per_1k_tokens": 0.003,
                                "recommended": True,
                                "description": "Excellent reasoning and long context"
                            },
                            {
                                "model_id": "gemini-1.5-flash",
                                "display_name": "Gemini 1.5 Flash",
                                "provider": "google",
                                "max_tokens": 1000000,
                                "supports_streaming": True,
                                "cost_per_1k_tokens": 0.0001,
                                "recommended": False,
                                "description": "Very fast and economical"
                            },
                            {
                                "model_id": "llama-3.1-8b",
                                "display_name": "Llama 3.1 8B",
                                "provider": "ollama",
                                "max_tokens": 128000,
                                "supports_streaming": True,
                                "cost_per_1k_tokens": 0.0,
                                "recommended": False,
                                "description": "Open source, requires local deployment"
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Generator service unavailable",
            "content": {
                "application/json": {
                    "examples": {
                        "service_down": {
                            "summary": "Generator microservice unavailable",
                            "value": {
                                "detail": "Generator service unavailable: Connection timeout"
                            }
                        },
                        "network_error": {
                            "summary": "Network connection failure",
                            "value": {
                                "detail": "Generator service unavailable: Cannot reach service endpoint"
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during model catalog retrieval",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to retrieve model list"
                    }
                }
            }
        }
    }
)
async def list_models() -> ModelsListResponse:
    """List all available LLM models for summary generation with capabilities.

    Queries the generator microservice to retrieve the complete catalog of
    supported large language models. Returns model metadata including provider,
    capabilities, context limits, and cost information to help clients select
    appropriate models for their use case.

    This endpoint serves as a discovery mechanism, enabling:
        - Dynamic model selection in UI dropdowns
        - Cost-aware model routing (balance quality vs. cost)
        - Context length validation (match query size to model limits)
        - Provider-specific feature detection (streaming, function calling, etc.)

    **Model Categories:**
        - **Flagship Models:** Highest quality, largest context, premium pricing
          (e.g., GPT-4, Claude Opus, Gemini Pro)
        - **Balanced Models:** Good quality/cost ratio, standard context
          (e.g., GPT-4o-mini, Claude Sonnet, Gemini Flash)
        - **Fast Models:** Lower latency, smaller context, economical
          (e.g., GPT-3.5 Turbo, Claude Haiku)
        - **Open Source:** Self-hosted via Ollama, no API costs, variable quality
          (e.g., Llama 3, Mistral, Phi-3)

    **Typical Model Metadata:**
        - model_id: Unique identifier for API calls (e.g., "gpt-4o-mini")
        - display_name: Human-readable name for UI (e.g., "GPT-4 Omni Mini")
        - provider: API provider (openai, anthropic, google, ollama)
        - max_tokens: Maximum context window size
        - supports_streaming: Whether streaming responses available
        - cost_per_1k_tokens: Approximate pricing (prompt + completion)
        - recommended: Whether this is a recommended default model

    Returns:
        ModelsListResponse containing:
            - models: Array of model metadata objects

        Example response:
            {
                "models": [
                    {
                        "model_id": "gpt-4o-mini",
                        "display_name": "GPT-4 Omni Mini",
                        "provider": "openai",
                        "max_tokens": 128000,
                        "supports_streaming": true,
                        "cost_per_1k_tokens": 0.0002,
                        "recommended": true,
                        "description": "Fast and affordable model, good for most tasks"
                    },
                    {
                        "model_id": "claude-3-5-sonnet-20241022",
                        "display_name": "Claude 3.5 Sonnet",
                        "provider": "anthropic",
                        "max_tokens": 200000,
                        "supports_streaming": true,
                        "cost_per_1k_tokens": 0.003,
                        "recommended": true,
                        "description": "Excellent reasoning and long context"
                    },
                    {
                        "model_id": "gemini-1.5-flash",
                        "display_name": "Gemini 1.5 Flash",
                        "provider": "google",
                        "max_tokens": 1000000,
                        "supports_streaming": true,
                        "cost_per_1k_tokens": 0.0001,
                        "recommended": false,
                        "description": "Very fast and economical"
                    }
                ]
            }

    Raises:
        HTTPException: Service communication failures:
            - 503 SERVICE_UNAVAILABLE: Generator microservice is unreachable,
              down for maintenance, or experiencing issues. This is a temporary
              error; clients should retry with exponential backoff.
            - 500 INTERNAL_SERVER_ERROR: Unexpected errors during model catalog
              retrieval or malformed responses from generator service.

        Specific error conditions:
            - GenerationServiceError: Generator service connection failures or
              API errors, converted to 503 status
            - Network timeouts: 503 with retry recommendation
            - Malformed model catalog: 500 with error details logged

    Example:
        Fetch available models:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/api/v1/models")
            ...     models = response.json()["models"]
            ...     for model in models:
            ...         print(f"{model['display_name']}: ${model['cost_per_1k_tokens']}")
            GPT-4 Omni Mini: $0.0002
            Claude 3.5 Sonnet: $0.003
            Gemini 1.5 Flash: $0.0001

        Select recommended models:
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/api/v1/models")
            ...     models = response.json()["models"]
            ...     recommended = [m for m in models if m.get("recommended", False)]
            ...     print(f"Recommended models: {[m['model_id'] for m in recommended]}")
            Recommended models: ['gpt-4o-mini', 'claude-3-5-sonnet-20241022']

        Find models with large context:
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/api/v1/models")
            ...     models = response.json()["models"]
            ...     large_context = [m for m in models if m["max_tokens"] >= 100000]
            ...     for model in large_context:
            ...         print(f"{model['model_id']}: {model['max_tokens']} tokens")
            gpt-4o-mini: 128000 tokens
            claude-3-5-sonnet-20241022: 200000 tokens
            gemini-1.5-flash: 1000000 tokens

        Using curl:
            $ curl http://localhost:8000/api/v1/models | jq '.models[].model_id'

    Notes:
        - Model availability depends on generator service configuration and API keys
        - Costs are approximate and may vary based on actual usage patterns
        - Some models may be temporarily unavailable due to provider rate limits
        - Open source models (Ollama) require local deployment and have no API costs
        - Model catalog is cached in generator service; updates require service restart
        - Context limits include both prompt and completion tokens
        - Streaming support enables real-time response generation in UI
        - Recommended models balance quality, cost, and reliability
        - Model IDs must be used exactly as returned in subsequent /generate/summary calls
        - Provider rate limits and quotas are enforced at generator service layer
        - Consider implementing client-side caching (5-10 minute TTL) to reduce load
        - Model capabilities and pricing subject to change by providers
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
        ) from e
    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model list"
        ) from e
