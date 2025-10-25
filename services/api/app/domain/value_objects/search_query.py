"""Search query value object."""
from dataclasses import dataclass

from app.core.constants import MIN_SEARCH_TOP_K, MAX_SEARCH_TOP_K


@dataclass(frozen=True)
class SearchQuery:
    """Immutable search query value object.

    Validates search parameters on creation.
    Being frozen ensures immutability (value object principle).
    """

    text: str
    top_k: int = 5

    def __post_init__(self) -> None:
        """Validate search query parameters."""
        if self.top_k < MIN_SEARCH_TOP_K or self.top_k > MAX_SEARCH_TOP_K:
            raise ValueError(
                f"top_k must be between {MIN_SEARCH_TOP_K} and {MAX_SEARCH_TOP_K}"
            )
