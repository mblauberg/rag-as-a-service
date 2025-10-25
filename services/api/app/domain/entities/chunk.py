"""Chunk domain entity."""
from dataclasses import dataclass, field
from uuid import UUID
from typing import Optional, List, Dict, Any


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
    embedding_vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    section_title: Optional[str] = None
    section_level: Optional[int] = None
    page_number: Optional[int] = None

    def has_embedding(self) -> bool:
        """Check if chunk has been embedded.

        Returns:
            True if embedding_vector is present, False otherwise
        """
        return self.embedding_vector is not None and len(self.embedding_vector) > 0
