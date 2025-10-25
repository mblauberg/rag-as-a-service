"""Search query value object."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchQuery:
    """Immutable search query value object.

    Validates search parameters on creation.
    Being frozen ensures immutability (value object principle).
    """

    text: str
    top_k: int = 5

    def __post_init__(self):
        """Validate search query parameters."""
        if self.top_k < 1 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")
