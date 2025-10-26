"""OpenAI provider implementation."""
import os
from typing import List
from openai import AsyncOpenAI
from app.providers.base import ModelProvider
from app.models.schemas import Model


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

    def __init__(self):
        """Initialize OpenAI provider with API key from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return self.client is not None

    async def list_models(self) -> List[Model]:
        """
        Return predefined OpenAI models.

        Returns:
            List of OpenAI Model objects
        """
        from datetime import datetime, timezone

        models = []
        for m in self.MODELS:
            model = Model(
                name=m["name"],
                display_name=m["display_name"],
                provider="openai",
                size=m["size"],
                description=m["description"],
                capabilities=m["capabilities"],
                modified_at=datetime.now(timezone.utc).isoformat() + "Z"
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using OpenAI API.

        Args:
            model: OpenAI model name (e.g., "openai:gpt-5")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary

        Raises:
            RuntimeError: If API call fails
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Strip "openai:" prefix for API call
        api_model = model.replace("openai:", "")

        # Construct messages
        system_message = "You are a helpful assistant that summarizes document search results."
        user_message = f"""Based on the following context, answer this query: {prompt}

Context:
{context}

Provide a concise, accurate summary."""

        try:
            response = await self.client.chat.completions.create(
                model=api_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_completion_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")
