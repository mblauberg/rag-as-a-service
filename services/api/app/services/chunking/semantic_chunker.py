"""Semantic text chunker using recursive splitting."""
from typing import List, Optional, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.token_counter import TokenCounter


class SemanticChunker:
    """
    Semantic text chunker that respects sentence boundaries and provides overlap.
    Uses recursive splitting to preserve semantic coherence.
    """

    def __init__(
        self,
        chunk_size: int = 400,
        overlap: int = 80,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize semantic chunker.

        Args:
            chunk_size: Target chunk size in tokens (approximate due to char-to-token estimation)
            overlap: Overlap size in tokens (approximate)
            separators: List of separators for recursive splitting

        Note:
            Uses 1:4 character-to-token ratio optimized for English prose.
            Actual token counts may vary by ±10-20% depending on content type:
            - Code-heavy documents: ~1:2 ratio (fewer characters per token)
            - English prose: ~1:4 ratio (average)
            - Non-English text: May vary significantly

            The chunker applies character-based splitting first, then counts
            actual tokens for metadata. This means chunk sizes are approximate
            during splitting but accurately measured after creation.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.token_counter = TokenCounter()

        # Default separators: paragraph -> newline -> sentence -> word
        if separators is None:
            separators = ["\n\n", "\n", ". ", " ", ""]

        # RecursiveCharacterTextSplitter uses character count
        # Rough approximation: 1 token ≈ 4 characters for English text
        char_chunk_size = chunk_size * 4
        char_overlap = overlap * 4

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=char_chunk_size,
            chunk_overlap=char_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        return self.token_counter.count_tokens(text)

    def chunk_text(
        self,
        text: str,
        section_context: Optional[str] = None
    ) -> List[str]:
        """
        Chunk text into semantic segments with optional section context.

        Args:
            text: Text to chunk
            section_context: Optional section path to prepend

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # Split text using recursive splitter
        chunks = self.splitter.split_text(text)

        # Prepend section context if provided
        if section_context:
            chunks = [f"[{section_context}]\n\n{chunk}" for chunk in chunks]

        # Filter out empty chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        return chunks

    def chunk_with_metadata(
        self,
        text: str,
        section_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text and return with metadata.

        Args:
            text: Text to chunk
            section_context: Optional section path

        Returns:
            List of dicts with 'content' and 'tokens' keys
        """
        chunks = self.chunk_text(text, section_context)

        return [
            {
                'content': chunk,
                'tokens': self.count_tokens(chunk)
            }
            for chunk in chunks
        ]
