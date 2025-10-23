"""Ollama provider implementation."""
from typing import List
import ollama
from app.providers.base import ModelProvider
from app.models.schemas import Model


class OllamaProvider(ModelProvider):
    """Provider for locally-hosted Ollama models."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API endpoint
        """
        # Create a simple wrapper that mimics OllamaClient interface
        self.base_url = base_url
        self.client = type('OllamaClient', (), {
            'check_health': self._check_health,
            'list_models': self._list_models_internal,
            'generate': self._generate_internal
        })()

    def is_available(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            # Simple sync check - try to connect to Ollama
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            # If Ollama is not available, return False
            # This allows the provider to gracefully not register
            return False

    async def list_models(self) -> List[Model]:
        """
        List available Ollama models with enhanced schema.

        Returns:
            List of Model objects with Ollama-specific metadata
        """
        ollama_models = await self.client.list_models()

        models = []
        for om in ollama_models:
            model = Model(
                name=om["name"],
                display_name=self._format_display_name(om["name"]),
                provider="ollama",
                size=om.get("size", "Unknown"),
                description=self._generate_description(om["name"]),
                capabilities=["local", "offline"],
                modified_at=om.get("modified_at", "")
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using Ollama.

        Args:
            model: Ollama model name (e.g., "llama3.3:70b")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary
        """
        return await self.client.generate(model=model, prompt=prompt, context=context)

    async def _check_health(self) -> bool:
        """Internal health check implementation."""
        try:
            client = ollama.AsyncClient(host=self.base_url)
            await client.list()
            return True
        except Exception:
            return False

    async def _list_models_internal(self):
        """Internal list models implementation."""
        client = ollama.AsyncClient(host=self.base_url)
        response = await client.list()
        return response.get("models", [])

    async def _generate_internal(self, model: str, prompt: str, context: str) -> str:
        """Internal generate implementation."""
        client = ollama.AsyncClient(host=self.base_url)
        full_prompt = f"Based on the following context, answer this query: {prompt}\n\nContext:\n{context}"
        response = await client.generate(model=model, prompt=full_prompt)
        return response.get("response", "")

    def _format_display_name(self, name: str) -> str:
        """
        Format Ollama model name for display.

        Args:
            name: Raw model name (e.g., "llama3.3:70b")

        Returns:
            Formatted name (e.g., "Llama 3.3 70B")
        """
        # "llama3.3:70b" -> "Llama 3.3 70B"
        parts = name.split(":")
        # Replace model names with capitalized versions, adding space before version number
        model_name = parts[0]
        if model_name.startswith("llama"):
            model_name = model_name.replace("llama", "Llama ")
        elif model_name.startswith("qwen"):
            model_name = model_name.replace("qwen", "Qwen ")

        size = parts[1].upper() if len(parts) > 1 else ""
        if size:
            return f"{model_name} {size}".strip()
        return model_name.strip()

    def _generate_description(self, name: str) -> str:
        """
        Generate description based on model name.

        Args:
            name: Model name

        Returns:
            Description string
        """
        name_lower = name.lower()

        if "llama" in name_lower:
            if "70b" in name_lower or "405b" in name_lower:
                return "Large local model, excellent reasoning and coding"
            else:
                return "Fast local model, good for general queries"
        elif "qwen" in name_lower:
            return "Multilingual local model, strong reasoning"
        else:
            return "Local Ollama model"
