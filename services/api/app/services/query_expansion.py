"""
Query expansion using LLM to generate alternative query phrasings.

Improves recall by:
- Expanding abbreviations (k8s → kubernetes)
- Adding synonyms and related terms
- Clarifying vague terminology
"""
import logging
from typing import List

logger = logging.getLogger(__name__)


class QueryExpansionService:
    """
    Generate alternative query phrasings using LLM.

    Returns 3 queries total: original + 2 alternatives
    """

    def __init__(self, generator_client):
        """
        Initialize query expansion service.

        Args:
            generator_client: GeneratorClient instance for LLM calls
        """
        self.generator_client = generator_client

    async def expand_query(self, query: str) -> List[str]:
        """
        Generate alternative query phrasings.

        Args:
            query: Original user query

        Returns:
            List of 3 queries: [original, alternative_1, alternative_2]
        """
        prompt = f"""Given this search query, generate 2 alternative phrasings that:
- Add technical synonyms and related terms
- Expand abbreviations (e.g., k8s → kubernetes)
- Clarify vague terms
- Keep the same search intent

Query: "{query}"

Output format (one per line):
Alternative 1:
Alternative 2:"""

        try:
            # Call generator service
            response = await self.generator_client.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.3  # Low temp for consistency
            )

            # Check if response is None or doesn't have text
            if response is None:
                logger.warning("Query expansion: LLM returned None")
                return [query]

            # Parse alternatives
            response_text = response.text if hasattr(response, 'text') else str(response)
            alternatives = self._parse_alternatives(response_text)

            # Return: original + alternatives (ensure exactly 3 total)
            return [query] + alternatives[:2]

        except Exception as e:
            # Fallback: return original query if LLM fails
            logger.error(f"Query expansion failed: {e}")
            return [query]

    def _parse_alternatives(self, response: str) -> List[str]:
        """
        Parse LLM response to extract alternative queries.

        Expected format:
        Alternative 1: <query>
        Alternative 2: <query>

        Also handles formats without "Alternative:" prefix.

        Args:
            response: LLM response text

        Returns:
            List of alternative query strings
        """
        lines = response.strip().split('\n')
        alternatives = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Remove "Alternative N:" prefix if present
            if line.lower().startswith("alternative"):
                # Find the colon separator
                if ":" in line:
                    # Remove prefix and colon, extract the actual query
                    line = line.split(":", 1)[1].strip()
                    # If there's content after the colon, use it
                    if line:
                        alternatives.append(line)
                # If no colon, skip this line - it's just a header
                continue

            # This line doesn't start with "alternative", so it's content
            alternatives.append(line)

        return alternatives
