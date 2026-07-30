"""OpenAI provider implementation."""
import os
from typing import List

from openai import AsyncOpenAI

from app.models.schemas import Model
from app.providers.base import ModelProvider


class OpenAIProvider(ModelProvider):
    """Provider for OpenAI models (GPT-5, GPT-5 Mini, GPT-4o, GPT-4o Mini)."""

    # Predefined OpenAI models (2025)
    MODELS = [
        {
            "name": "openai:gpt-5",
            "display_name": "GPT-5",
            "size": "N/A",
            "description": "Best intelligence, coding/math excellence, 94.6% AIME",
            "capabilities": ["reasoning", "coding", "creative", "multimodal"]
        },
        {
            "name": "openai:gpt-5-mini",
            "display_name": "GPT-5 Mini",
            "size": "N/A",
            "description": "Balanced performance and cost",
            "capabilities": ["reasoning", "coding", "fast"]
        },
        {
            "name": "openai:gpt-4o",
            "display_name": "GPT-4o",
            "size": "N/A",
            "description": "Fast multimodal model, excellent for vision and text",
            "capabilities": ["reasoning", "coding", "multimodal", "fast"]
        },
        {
            "name": "openai:gpt-4o-mini",
            "display_name": "GPT-4o Mini",
            "size": "N/A",
            "description": "Cost-effective, fast responses",
            "capabilities": ["reasoning", "coding", "fast", "cost-effective"]
        }
    ]

    def __init__(self) -> None:
        """Initialize provider with OpenAI API key."""
        api_key = os.getenv("OPENAI_API_KEY")
        self.client: AsyncOpenAI | None = AsyncOpenAI(api_key=api_key) if api_key else None

    def is_available(self) -> bool:
        return self.client is not None

    async def list_models(self) -> List[Model]:
        """List predefined OpenAI models."""
        from datetime import datetime, timezone

        models: List[Model] = []
        for m in self.MODELS:
            model = Model(
                name=str(m["name"]),
                display_name=str(m["display_name"]),
                provider="openai",
                size=str(m["size"]),
                description=str(m["description"]),
                capabilities=list(m["capabilities"]),
                modified_at=datetime.now(timezone.utc).isoformat()
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """Call OpenAI API to generate summary."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        api_model = model.replace("openai:", "")
        system_message = "You are a helpful assistant that summarizes document search results."

        try:
            response = await self.client.chat.completions.create(
                model=api_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": context}
                ],
                max_completion_tokens=500
            )

            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("OpenAI returned empty response")
            return content

        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")
