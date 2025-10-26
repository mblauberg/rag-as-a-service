"""LLM-based query expansion for improved retrieval."""
import logging

from app.core.exceptions import GenerationServiceError
from app.ports.services import GenerationService, QueryAugmenter

logger = logging.getLogger(__name__)


class LLMQueryAugmenterImpl(QueryAugmenter):
    """LLM-based query expansion using generation service.

    Generates 2-3 alternative phrasings of the user's query
    to improve retrieval coverage. This addresses the
    "vocabulary mismatch" problem where users and documents
    use different terms for the same concept.
    """

    def __init__(self, generation_service: GenerationService):
        """Initialize with LLM generation service."""
        self.generation_service = generation_service

    async def expand(
        self, query: str, num_variants: int = 2, method: str = "llm"
    ) -> list[str]:
        """Expand query using LLM to generate variants.

        Uses a carefully crafted prompt to generate semantically
        equivalent but lexically different queries.

        Args:
            query: Original query
            num_variants: Number of variants to generate (default 2)
            method: Expansion method (only "llm" supported)

        Returns:
            List containing original + variant queries

        Raises:
            ValueError: If method is not "llm"
        """
        if method != "llm":
            raise ValueError(f"Unsupported expansion method: {method}")

        try:
            # Craft expansion prompt
            prompt = self._build_expansion_prompt(query, num_variants)

            # Generate variants via LLM
            # Note: GenerationService.generate requires context parameter,
            # but we pass empty list since we don't need context for query expansion
            response = await self.generation_service.generate(prompt=prompt, context=[])

            # Parse response into list of queries
            variants = self._parse_variants(response)

            # Always include original query first
            expanded = [query] + variants[:num_variants]

            logger.info(f"Expanded query into {len(expanded)} variants: {expanded}")

            return expanded

        except GenerationServiceError as e:
            # Graceful degradation: return original query on error
            logger.warning(f"Query expansion failed: {e}, using original query")
            return [query]
        except Exception as e:
            # Graceful degradation for any other error
            logger.warning(f"Query expansion failed: {e}, using original query")
            return [query]

    def _build_expansion_prompt(self, query: str, num_variants: int) -> str:
        """Build prompt for query expansion.

        Args:
            query: Original search query
            num_variants: Number of alternative phrasings to generate

        Returns:
            Formatted prompt for the LLM
        """
        return f"""Generate {num_variants} alternative phrasings of this search query.
The alternatives should be semantically equivalent but use different words.

Original query: {query}

Alternative phrasings (one per line, no numbering):"""

    def _parse_variants(self, response: str) -> list[str]:
        """Parse LLM response into list of query variants.

        Args:
            response: Raw LLM response text

        Returns:
            List of parsed query variants
        """
        lines = response.strip().split("\n")

        # Clean up each line
        variants = []
        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Remove numbering if present (1., 2., etc.)
            if line and line[0].isdigit():
                parts = line.split(".", 1)
                if len(parts) > 1:
                    line = parts[1].strip()

            # Remove quotes if present
            line = line.strip('"').strip("'")

            # Remove markdown formatting if present (**, *, etc.)
            line = line.replace("**", "").replace("*", "")

            if line:
                variants.append(line)

        return variants
