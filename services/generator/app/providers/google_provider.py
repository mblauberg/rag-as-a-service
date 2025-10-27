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

    def __init__(self) -> None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.api_key: str | None = api_key
        else:
            self.api_key = None

    def is_available(self) -> bool:
        return self.api_key is not None

    async def list_models(self) -> List[Model]:
        """Get available Gemini models."""
        from datetime import datetime, timezone

        models: List[Model] = []
        for m in self.MODELS:
            model = Model(
                name=str(m["name"]),
                display_name=str(m["display_name"]),
                provider="google",
                size=str(m["size"]),
                description=str(m["description"]),
                capabilities=list(m["capabilities"]),
                modified_at=datetime.now(timezone.utc).isoformat()
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        if not self.api_key:
            raise RuntimeError("Google API key not configured")

        api_model = model.replace("google:", "").replace("-", ".", 1).replace("-", ".", 1)

        try:
            model_instance = genai.GenerativeModel(api_model)
            response = await model_instance.generate_content_async(
                context,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 500
                }
            )

            return str(response.text)

        except Exception as e:
            raise RuntimeError(f"Google Gemini generation failed: {str(e)}")
