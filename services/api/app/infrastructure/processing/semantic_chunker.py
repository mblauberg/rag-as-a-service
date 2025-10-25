"""SemanticChunker infrastructure adapter implementation.

This module implements the TextChunker port interface by wrapping
the existing SemanticChunkerV2 implementation.
"""
from typing import List

from app.ports.services import TextChunker
from app.core.exceptions import ChunkingError
from app.services.chunking.semantic_chunker_v2 import SemanticChunkerV2


class SemanticChunkerImpl(TextChunker):
    """Implementation of TextChunker port using SemanticChunkerV2."""

    def __init__(
        self,
        min_chunk_size: int = 128,
        max_chunk_size: int = 512,
        breakpoint_percentile: float = 95.0,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """Initialize the semantic chunker.

        Args:
            min_chunk_size: Minimum tokens per chunk (avoid fragments)
            max_chunk_size: Maximum tokens per chunk (context limit)
            breakpoint_percentile: Percentile for boundary detection (95 = top 5% drops)
            embedding_model: Model for sentence embeddings
        """
        self.chunker = SemanticChunkerV2(
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
            breakpoint_percentile=breakpoint_percentile,
            embedding_model=embedding_model
        )

    async def chunk(self, text: str) -> List[str]:
        """Chunk text into semantic segments.

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks (strings only)

        Raises:
            ChunkingError: If chunking fails
        """
        try:
            # Call the underlying chunker
            chunk_results = await self.chunker.chunk_text(text)

            # Extract only the text from ChunkResult objects
            chunks = [chunk_result.text for chunk_result in chunk_results]

            return chunks

        except Exception as e:
            raise ChunkingError(
                operation="chunk_text",
                original_error=e
            )
