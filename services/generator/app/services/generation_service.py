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

logger = logging.getLogger(__name__)

# Global registry (initialized in main.py)
provider_registry = None


class GenerationService:
    """Service for generating summaries from document chunks."""

    def __init__(self):
        """Initialize generation service."""
        self.prompt_service = PromptService()

    async def generate_summary(
        self,
        query: str,
        chunks: List[ChunkInput],
        model: Optional[str] = None
    ) -> GenerateResponse:
        """
        Generate summary from chunks using provider registry.

        Args:
            query: User's search query
            chunks: Retrieved document chunks
            model: Model to use (defaults to settings.default_model)

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
        logger.info(f"Generating with {model_to_use}")
        summary, provider_name = await provider_registry.generate(model_to_use, prompt, context)

        logger.info(f"Generated summary using {provider_name} provider")

        return GenerateResponse(
            summary=summary,
            model_used=model_to_use,
            tokens_used=0  # Token tracking not implemented yet
        )

    async def list_available_models(self) -> ModelsResponse:
        """
        List models from all registered providers.

        Returns:
            ModelsResponse with list of models
        """
        models = await provider_registry.list_all_models()
        return ModelsResponse(models=models)
