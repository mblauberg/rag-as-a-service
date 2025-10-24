"""Text chunking service for splitting documents into manageable chunks.

.. deprecated::
    This class is deprecated. Use :class:`app.services.chunking.semantic_chunker.SemanticChunker` instead,
    which provides better semantic coherence using recursive splitting.
"""
import warnings
from typing import List


class ChunkingService:
    """Service for chunking text into smaller segments.

    .. deprecated::
        Use SemanticChunker instead for better semantic coherence.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize chunking service.

        .. deprecated::
            Use SemanticChunker instead.

        Args:
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        warnings.warn(
            "ChunkingService is deprecated. Use SemanticChunker instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text or len(text) == 0:
            return []

        chunks = []
        start = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                sentence_ends = ['. ', '! ', '? ', '\n\n']
                best_break = end

                # Search backwards from end for a good break point
                for i in range(end, max(start + self.chunk_size // 2, start), -1):
                    if any(text[i:i+2].startswith(ending) for ending in sentence_ends):
                        best_break = i + 1
                        break

                end = best_break

            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move to next chunk with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks

    def estimate_token_count(self, text: str) -> int:
        """
        Estimate token count for text.
        Simple approximation: ~4 characters per token.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4


# Global chunking service instance
chunking_service = ChunkingService(chunk_size=512, chunk_overlap=50)
