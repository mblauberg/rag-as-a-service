"""Chunk domain entity."""
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class Chunk:
    """Chunk entity representing a document fragment.

    Contains text content, token count, and optional embedding vector.
    Chunks are the fundamental unit for vector search and RAG.
    """

    id: UUID
    document_id: UUID
    content: str
    tokens: int
    embedding_vector: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    section_title: str | None = None
    section_level: int | None = None
    page_number: int | None = None
    score: float | None = None  # Similarity/relevance score from search/reranking

    def has_embedding(self) -> bool:
        """Check if chunk has been embedded.

        Returns:
            True if embedding_vector is present, False otherwise
        """
        return self.embedding_vector is not None and len(self.embedding_vector) > 0
