"""Abstract base class for model providers."""
from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import Model


class ModelProvider(ABC):
    """Abstract base class for LLM providers (OpenAI, Anthropic, Google)."""

    @abstractmethod
    async def list_models(self) -> List[Model]:
        """
        Return list of available models from this provider.

        Returns:
            List of Model objects with provider-specific metadata
        """
        pass

    @abstractmethod
    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using provider's API.

        Args:
            model: Model identifier (e.g., "llama3.3:70b", "openai:gpt-5")
            prompt: User query or instruction
            context: Retrieved document chunks as context

        Returns:
            Generated summary text

        Raises:
            ValueError: If model not found
            RuntimeError: If generation fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is configured and accessible.

        Returns:
            True if provider can be used, False otherwise
        """
        pass
