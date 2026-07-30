"""High-level generation service using provider registry."""
import logging
from typing import List, Optional

from app.core.config import settings
from app.models.schemas import (
    ChunkInput,
    GenerateResponse,
    ModelsResponse,
)
from app.providers.registry import ProviderRegistry
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)

# Global registry (initialized in main.py)
provider_registry: ProviderRegistry | None = None


class GenerationService:
    """Service for generating summaries from document chunks."""

    def __init__(self) -> None:
        """Initialize generation service."""
        self.prompt_service = PromptService()

    async def generate_summary(
        self,
        query: str,
        chunks: List[ChunkInput],
        model: Optional[str] = None
    ) -> GenerateResponse:
        """Generate summary from chunks using RAG with specified LLM.

        Args:
            query: Search query
            chunks: Retrieved document chunks
            model: LLM model (defaults to settings.default_model)

        Returns:
            GenerateResponse with summary and metadata
        """
        # Use default model if not specified
        model_to_use = model or settings.default_model

        # Build RAG prompt
        prompt = self.prompt_service.build_rag_prompt(query, chunks)

        # Build context from chunks
        context = "\n\n".join([chunk.text for chunk in chunks])

        # Generate via registry
        if provider_registry is None:
            raise RuntimeError("Provider registry not initialized")
        logger.info(f"Generating with {model_to_use}")
        summary, provider_name = await provider_registry.generate(model_to_use, prompt, context)

        logger.info(f"Generated summary using {provider_name} provider")

        return GenerateResponse(
            summary=summary,
            model_used=model_to_use,
            tokens_used=0  # Token tracking not implemented yet
        )

    async def list_available_models(self) -> ModelsResponse:
        """List all available LLM models from registered providers.

        Queries ProviderRegistry to get models from all configured providers:
        - OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
        - Anthropic: claude-3-5-sonnet, claude-3-opus, claude-3-haiku
        - Google: gemini-1.5-pro, gemini-1.5-flash

        Each provider is registered at service startup based on available
        API keys in environment variables. Providers without API keys are
        skipped automatically.

        Returns:
            ModelsResponse containing list of model strings. Each model
            identifier can be passed to generate_summary() via the model
            parameter.

        Raises:
            RuntimeError: If provider registry not initialized. This indicates
                a startup configuration error in main.py.

        Note:
            Model availability depends on API keys configured. The list is
            dynamic based on environment configuration.

        Example:
            >>> service = GenerationService()
            >>> response = await service.list_available_models()
            >>> print(f"Available models: {response.models}")
        """
        if provider_registry is None:
            raise RuntimeError("Provider registry not initialized")
        models = await provider_registry.list_all_models()
        return ModelsResponse(models=models)
