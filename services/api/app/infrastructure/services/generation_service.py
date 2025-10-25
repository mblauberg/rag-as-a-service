"""HTTP-based generation service adapter implementation."""

from app.core.exceptions import GenerationServiceError
from app.ports.services import GenerationService
from app.services.generator_client import GeneratorClient


class HTTPGenerationService(GenerationService):
    """HTTP adapter for LLM generation service.

    This adapter communicates with the generator microservice via HTTP
    to generate text responses using LLMs.
    """

    def __init__(self, generator_url: str | None = None):
        """Initialize HTTP generation service.

        Args:
            generator_url: Base URL of the generator service (e.g., "http://localhost:8002")
                          If None, uses default from settings
        """
        self.client = GeneratorClient(base_url=generator_url)

    async def generate(
        self,
        prompt: str,
        context: list[str],
        model: str | None = None
    ) -> str:
        """Generate text response using LLM via HTTP.

        Args:
            prompt: User query/prompt
            context: Retrieved context chunks
            model: Optional model identifier (currently unused, uses default)

        Returns:
            Generated text response

        Raises:
            GenerationServiceError: If generation fails
        """
        try:
            # For query expansion, we don't need context chunks
            # Use the simpler generate method with just the prompt
            result = await self.client.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )

            if result is None:
                raise GenerationServiceError(
                    "Generation service returned None"
                )

            # Extract text from response
            if hasattr(result, 'text'):
                return result.text
            elif isinstance(result, dict) and 'text' in result:
                return result['text']
            elif isinstance(result, str):
                return result
            else:
                raise GenerationServiceError(
                    f"Unexpected response format: {type(result)}"
                )

        except GenerationServiceError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            # Wrap any other exceptions
            raise GenerationServiceError(
                f"Unexpected error during generation: {type(e).__name__}",
                original_error=e
            )
