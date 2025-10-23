"""High-level generation service combining Ollama and prompt services."""
import logging
from typing import List, Optional
from app.models.schemas import (
    ChunkInput,
    GenerateResponse,
    ModelsResponse,
    Model
)
from app.services.ollama_client import OllamaClient
from app.services.prompt_service import PromptService
from app.core.config import settings

logger = logging.getLogger(__name__)


class GenerationService:
    """Service for generating summaries from document chunks."""

    def __init__(self):
        """Initialize generation service."""
        self.ollama_client = OllamaClient()
        self.prompt_service = PromptService()

    async def generate_summary(
        self,
        query: str,
        chunks: List[ChunkInput],
        model: Optional[str] = None
    ) -> GenerateResponse:
        """
        Generate summary from chunks using LLM.

        Args:
            query: User's search query
            chunks: Retrieved document chunks
            model: Ollama model to use (defaults to settings.default_model)

        Returns:
            GenerateResponse with summary and metadata
        """
        # Use default model if not specified
        model_to_use = model or settings.default_model

        # Build RAG prompt
        prompt = self.prompt_service.build_rag_prompt(query, chunks)

        # Generate with Ollama
        logger.info(f"Generating summary with {model_to_use}")
        ollama_response = await self.ollama_client.generate(
            model=model_to_use,
            prompt=prompt
        )

        # Extract summary
        summary = ollama_response["response"].strip()

        # Estimate tokens used
        prompt_tokens = ollama_response.get("prompt_eval_count", 0)
        completion_tokens = ollama_response.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens

        logger.info(f"Generated summary with {total_tokens} tokens")

        return GenerateResponse(
            summary=summary,
            model_used=model_to_use,
            tokens_used=total_tokens
        )

    async def list_available_models(self) -> ModelsResponse:
        """
        List available Ollama models.

        Returns:
            ModelsResponse with list of models
        """
        raw_models = await self.ollama_client.list_models()

        # Convert to Model objects
        models = []
        for model in raw_models:
            # Convert size to human-readable format
            size_bytes = model.get("size", 0)
            size_gb = size_bytes / (1024 ** 3)
            size_str = f"{size_gb:.1f}GB" if size_gb >= 1 else f"{size_bytes / (1024 ** 2):.0f}MB"

            models.append(Model(
                name=model["name"],
                display_name=model["name"],
                provider="ollama",
                size=size_str,
                modified_at=model.get("modified_at", "")
            ))

        return ModelsResponse(models=models)
