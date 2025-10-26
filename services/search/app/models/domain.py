"""Domain models for search service."""
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class Chunk:
    """Chunk domain entity.

    Represents a text chunk with optional metadata and relevance score.
    """

    id: UUID
    document_id: UUID
    content: str
    tokens: int
    score: Optional[float] = None
    document_title: Optional[str] = None
    document_filename: Optional[str] = None
    chunk_index: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    def with_score(self, score: float) -> "Chunk":
        """Create new chunk with updated score."""
        from dataclasses import replace
        return replace(self, score=score)
