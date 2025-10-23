"""Anthropic Claude provider implementation."""
import os
from typing import List
from anthropic import AsyncAnthropic
from app.providers.base import ModelProvider
from app.models.schemas import Model


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic Claude models."""

    # Predefined Claude models (2025)
    MODELS = [
        {
            "name": "anthropic:claude-opus-4-1",
            "display_name": "Claude Opus 4.1",
            "size": "N/A",
            "description": "Most powerful Claude model, best reasoning",
            "capabilities": ["reasoning", "coding", "analysis", "multimodal"]
        },
        {
            "name": "anthropic:claude-sonnet-4-5",
            "display_name": "Claude Sonnet 4.5",
            "size": "N/A",
            "description": "Best coding model in the world",
            "capabilities": ["coding", "reasoning", "fast"]
        },
        {
            "name": "anthropic:claude-haiku-4-5",
            "display_name": "Claude Haiku 4.5",
            "size": "N/A",
            "description": "Fast and cost-effective",
            "capabilities": ["fast", "efficient", "reasoning"]
        }
    ]

    def __init__(self):
        """Initialize Anthropic provider with API key from environment."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured."""
        return self.client is not None

    async def list_models(self) -> List[Model]:
        """
        Return predefined Claude models.

        Returns:
            List of Claude Model objects
        """
        from datetime import datetime

        models = []
        for m in self.MODELS:
            model = Model(
                name=m["name"],
                display_name=m["display_name"],
                provider="anthropic",
                size=m["size"],
                description=m["description"],
                capabilities=m["capabilities"],
                modified_at=datetime.utcnow().isoformat() + "Z"
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using Anthropic API.

        Args:
            model: Claude model name (e.g., "anthropic:claude-sonnet-4-5")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary

        Raises:
            RuntimeError: If API call fails
        """
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        # Strip "anthropic:" prefix for API call
        api_model = model.replace("anthropic:", "")

        # Construct user message
        user_message = f"""Based on the following context, answer this query: {prompt}

Context:
{context}

Provide a concise, accurate summary."""

        try:
            response = await self.client.messages.create(
                model=api_model,
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {str(e)}")
