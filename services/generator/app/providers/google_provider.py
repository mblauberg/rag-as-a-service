"""Google Gemini provider implementation."""
import os
from typing import List
import google.generativeai as genai
from app.providers.base import ModelProvider
from app.models.schemas import Model


class GoogleProvider(ModelProvider):
    """Provider for Google Gemini models."""

    # Predefined Gemini models (2025)
    MODELS = [
        {
            "name": "google:gemini-2-5-pro",
            "display_name": "Gemini 2.5 Pro",
            "size": "N/A",
            "description": "2M context, adaptive thinking capabilities",
            "capabilities": ["reasoning", "long-context", "multimodal"]
        },
        {
            "name": "google:gemini-2-5-flash",
            "display_name": "Gemini 2.5 Flash",
            "size": "N/A",
            "description": "Efficient, improved tool use, 54% SWE-Bench",
            "capabilities": ["fast", "tool-use", "reasoning"]
        }
    ]

    def __init__(self):
        """Initialize Google provider with API key from environment."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.api_key = api_key
        else:
            self.api_key = None

    def is_available(self) -> bool:
        """Check if Google API key is configured."""
        return self.api_key is not None

    async def list_models(self) -> List[Model]:
        """
        Return predefined Gemini models.

        Returns:
            List of Gemini Model objects
        """
        from datetime import datetime, timezone

        models = []
        for m in self.MODELS:
            model = Model(
                name=m["name"],
                display_name=m["display_name"],
                provider="google",
                size=m["size"],
                description=m["description"],
                capabilities=m["capabilities"],
                modified_at=datetime.now(timezone.utc).isoformat() + "Z"
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using Google Gemini API.

        Args:
            model: Gemini model name (e.g., "google:gemini-2-5-pro")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary

        Raises:
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise RuntimeError("Google API key not configured")

        # Strip "google:" prefix and convert to API format
        # "google:gemini-2-5-pro" -> "gemini-2.5-pro"
        api_model = model.replace("google:", "").replace("-", ".", 1).replace("-", ".", 1)

        # Construct prompt
        full_prompt = f"""Based on the following context, answer this query: {prompt}

Context:
{context}

Provide a concise, accurate summary."""

        try:
            model_instance = genai.GenerativeModel(api_model)
            response = await model_instance.generate_content_async(
                full_prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 500
                }
            )

            return response.text

        except Exception as e:
            raise RuntimeError(f"Google Gemini generation failed: {str(e)}")
