"""Domain models for search service."""
from dataclasses import dataclass, field
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
    score: float | None = None
    document_title: str | None = None
    document_filename: str | None = None
    chunk_index: int | None = None
    metadata: dict | None = field(default_factory=dict)

    def with_score(self, score: float) -> "Chunk":
        """Create new chunk with updated score."""
        self.score = score
        return self
