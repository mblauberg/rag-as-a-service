"""Provider registry for managing multiple model providers."""
from typing import Dict, List, Tuple
from app.providers.base import ModelProvider
from app.models.schemas import Model


class ProviderRegistry:
    """Registry for managing and routing between model providers."""

    # Model alias mappings: friendly_name -> (provider, api_model_name)
    MODEL_ALIASES = {
        # OpenAI models
        "gpt-5": ("openai", "gpt-5"),
        "gpt-5-mini": ("openai", "gpt-5-mini"),

        # Anthropic models
        "sonnet-4.5": ("anthropic", "claude-sonnet-4-5-20250929"),
        "opus-4.1": ("anthropic", "claude-opus-4-1-20250805"),
        "haiku-4.5": ("anthropic", "claude-haiku-4-5-20251001"),

        # Google models
        "gemini-flash-2.5": ("google", "gemini-2.5-flash"),
        "gemini-pro-2.5": ("google", "gemini-2.5-pro"),
    }

    def __init__(self) -> None:
        """Initialize empty registry."""
        self.providers: Dict[str, ModelProvider] = {}

    def register(self, name: str, provider: ModelProvider) -> None:
        """
        Register a provider if it's available.

        Args:
            name: Provider identifier (e.g., "openai", "anthropic", "google")
            provider: ModelProvider instance
        """
        if provider.is_available():
            self.providers[name] = provider

    async def list_all_models(self) -> List[Model]:
        """
        Aggregate models from all registered providers.

        Returns:
            Combined list of models from all providers
        """
        models = []
        for provider in self.providers.values():
            provider_models = await provider.list_models()
            models.extend(provider_models)
        return models

    async def generate(self, model_name: str, prompt: str, context: str) -> Tuple[str, str]:
        """
        Route generation request to appropriate provider.

        Args:
            model_name: Full model identifier (e.g., "openai:gpt-5")
            prompt: User query
            context: Retrieved context

        Returns:
            Tuple of (generated_summary, provider_name)

        Raises:
            ValueError: If provider not found
        """
        provider_name = self._extract_provider(model_name)

        if provider_name not in self.providers:
            raise ValueError(f"Provider not found: {provider_name}")

        summary = await self.providers[provider_name].generate(model_name, prompt, context)
        return summary, provider_name

    def _extract_provider(self, model_name: str) -> str:
        """
        Extract provider name from model identifier.

        Args:
            model_name: Full model name (e.g., "openai:gpt-5", "anthropic:claude-3")

        Returns:
            Provider name (defaults to "openai" if no prefix)

        Raises:
            ValueError: If provider cannot be determined
        """
        if ":" in model_name:
            parts = model_name.split(":")
            # Check if first part is a registered provider name
            if parts[0] in self.providers:
                return parts[0]
            # Check if first part is a known API provider name
            if parts[0] in ["openai", "anthropic", "google"]:
                return parts[0]

        # Default to openai for unprefixed models (for backward compatibility)
        return "openai"
