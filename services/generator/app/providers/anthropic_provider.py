"""Anthropic Claude provider implementation."""
import os
from typing import List

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock

from app.models.schemas import Model
from app.providers.base import ModelProvider


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

    def __init__(self) -> None:
        """Initialize with API key from environment."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client: AsyncAnthropic | None = AsyncAnthropic(api_key=api_key) if api_key else None

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return self.client is not None

    async def list_models(self) -> List[Model]:
        """Return predefined Claude models."""
        from datetime import datetime, timezone

        models: List[Model] = []
        for m in self.MODELS:
            model = Model(
                name=str(m["name"]),
                display_name=str(m["display_name"]),
                provider="anthropic",
                size=str(m["size"]),
                description=str(m["description"]),
                capabilities=list(m["capabilities"]),
                modified_at=datetime.now(timezone.utc).isoformat()
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """Generate summary using Anthropic API."""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        api_model = model.replace("anthropic:", "")

        try:
            response = await self.client.messages.create(
                model=api_model,
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": context}
                ]
            )

            for block in response.content:
                if isinstance(block, TextBlock):
                    return block.text
            raise RuntimeError("No text content in response")

        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {str(e)}")
