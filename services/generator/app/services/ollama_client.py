"""Ollama API client wrapper."""
import logging
from typing import Dict, Any, List, Optional
import ollama
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for Ollama API."""

    def __init__(self):
        """Initialize Ollama client."""
        self.client = ollama.AsyncClient(host=settings.ollama_url)
        logger.info(f"Ollama client initialized with URL: {settings.ollama_url}")

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available Ollama models.

        Returns:
            List of model dictionaries with name, size, modified_at
        """
        try:
            response = await self.client.list()
            models = response.get("models", [])
            logger.info(f"Found {len(models)} available models")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama model.

        Args:
            model: Model name (e.g., 'llama3.2')
            prompt: Input prompt
            temperature: Sampling temperature (default from settings)

        Returns:
            Generation response dictionary
        """
        temp = temperature if temperature is not None else settings.temperature

        try:
            response = await self.client.generate(
                model=model,
                prompt=prompt,
                options={"temperature": temp}
            )
            logger.info(f"Generated response with {model}")
            return response
        except Exception as e:
            logger.error(f"Generation failed with {model}: {e}")
            raise

    async def check_health(self) -> bool:
        """
        Check if Ollama service is healthy.

        Returns:
            True if Ollama is reachable, False otherwise
        """
        try:
            await self.client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
