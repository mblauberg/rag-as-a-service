"""High-level generation service using provider registry."""
import logging
from typing import List, Optional
from app.models.schemas import (
    ChunkInput,
    GenerateResponse,
    ModelsResponse,
)
from app.services.prompt_service import PromptService
from app.core.config import settings
from app.providers.registry import ProviderRegistry

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
        """Generate AI summary from retrieved chunks using RAG architecture.

        Implements Retrieval-Augmented Generation (RAG) by combining:
        1. Retrieved document chunks (from search service)
        2. User's original query
        3. Cloud LLM API (OpenAI, Anthropic, Google)

        Process:
        1. Build RAG prompt with chunks and citation markers [1], [2], etc.
        2. Route to appropriate LLM provider based on model name
        3. Generate summary with inline citations
        4. Return summary with metadata (model used, token count)

        The PromptService formats chunks with citation markers, instructing
        the LLM to cite sources when making claims. This provides:
        - Answer attribution to source documents
        - Fact verification capability
        - Transparency in information sources

        Supported providers (via ProviderRegistry):
        - OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
        - Anthropic: claude-3-5-sonnet, claude-3-opus, claude-3-haiku
        - Google: gemini-1.5-pro, gemini-1.5-flash

        Args:
            query: User's original search query (natural language question).
            chunks: Retrieved document chunks to use as context. Each chunk
                contains text and metadata from relevant documents.
            model: LLM model identifier (e.g., "gpt-4o-mini", "claude-3-5-sonnet").
                If None, uses settings.default_model. Must be in format
                recognized by ProviderRegistry.

        Returns:
            GenerateResponse containing:
            - summary: AI-generated answer with inline citations
            - model_used: Actual model identifier used for generation
            - tokens_used: Token count (not implemented yet, returns 0)

        Raises:
            RuntimeError: If provider registry not initialized at startup.
            ValueError: If model name not recognized by any provider.
            httpx.RequestError: If LLM API call fails (network, auth, quota).

        Example:
            >>> service = GenerationService()
            >>> chunks = [ChunkInput(text="RAG combines retrieval...", ...)]
            >>> response = await service.generate_summary(
            ...     query="What is RAG?",
            ...     chunks=chunks,
            ...     model="gpt-4o-mini"
            ... )
            >>> print(response.summary)
            >>> print(f"Generated with {response.model_used}")
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
