"""
Semantic chunking using Chonkie's SemanticChunker.
Modern, fast, and Python 3.13 compatible semantic text splitting.
"""

from chonkie import SemanticChunker as ChonkieSemanticChunker
from chonkie.embeddings import AutoEmbeddings
from pydantic import BaseModel


class ChunkResult(BaseModel):
    """Result of chunking operation"""
    text: str
    start_index: int
    end_index: int
    token_count: int | None = None
    coherence_score: float | None = None


class SemanticChunker:
    """
    Semantic chunking using Chonkie's semantic similarity detection.

    Splits text based on semantic similarity between sentences:
    - Fast and lightweight implementation
    - Python 3.13 compatible
    - Production-ready performance
    """

    def __init__(
        self,
        min_chunk_size: int = 128,
        max_chunk_size: int = 512,
        breakpoint_percentile: float = 95.0,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        overlap_ratio: float = 0.1
    ):
        """
        Initialize semantic chunker.

        Args:
            min_chunk_size: Minimum tokens per chunk (avoid fragments)
            max_chunk_size: Maximum tokens per chunk (context limit)
            breakpoint_percentile: Percentile for boundary detection (95 = top 5% drops)
            embedding_model: Model for sentence embeddings
            overlap_ratio: Fraction of chunk size to overlap (0.0-0.5)
                          0.1 = 10% overlap (recommended for context preservation)
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.breakpoint_percentile = breakpoint_percentile
        self.embedding_model = embedding_model
        self.overlap_ratio = overlap_ratio

        # Initialize Chonkie embeddings
        self.embeddings = AutoEmbeddings.get_embeddings(model=embedding_model)

        # Initialize Chonkie semantic chunker
        self.chunker = ChonkieSemanticChunker(
            embedding_model=self.embeddings,
            chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
            threshold=breakpoint_percentile / 100.0  # Convert percentile to 0-1 range
        )

    async def chunk_text(self, text: str) -> list[ChunkResult]:
        """
        Chunk text using semantic similarity.

        Args:
            text: Input text to chunk

        Returns:
            List of ChunkResult objects
        """
        # Use Chonkie's semantic chunker
        chunks = self.chunker.chunk(text)

        # Convert to ChunkResult format
        results = []
        current_index = 0
        accumulated_chunks = []

        for chunk in chunks:
            chunk_text = chunk.text.strip()
            token_count = chunk.token_count if hasattr(chunk, 'token_count') else len(chunk_text.split())

            # Accumulate all chunks first
            accumulated_chunks.append({
                "text": chunk_text,
                "tokens": token_count,
                "start": current_index,
                "end": current_index + len(chunk_text)
            })
            current_index += len(chunk_text)

        # Now process accumulated chunks with size constraints
        # Strategy: Merge VERY small fragments (< 10% of min), preserve semantic boundaries otherwise
        merged_chunks = []
        very_small_threshold = max(5, self.min_chunk_size * 0.1)  # Chunks smaller than this are fragments

        buffer_chunks = []
        buffer_tokens = 0

        for i, chunk in enumerate(accumulated_chunks):
            # Skip empty chunks
            if chunk["tokens"] == 0:
                continue

            # If chunk is too large, save buffer and truncate this chunk
            if chunk["tokens"] > self.max_chunk_size:
                # Save accumulated buffer first
                if buffer_chunks:
                    merged_text = " ".join(c["text"] for c in buffer_chunks)
                    merged_chunks.append({
                        "text": merged_text,
                        "tokens": buffer_tokens,
                        "start": buffer_chunks[0]["start"],
                        "end": buffer_chunks[-1]["end"]
                    })
                    buffer_chunks = []
                    buffer_tokens = 0

                # Truncate large chunk
                words = chunk["text"].split()
                split_text = " ".join(words[:self.max_chunk_size])
                merged_chunks.append({
                    "text": split_text,
                    "tokens": self.max_chunk_size,
                    "start": chunk["start"],
                    "end": chunk["start"] + len(split_text)
                })

            # Chunk is a tiny fragment - always merge with neighbors
            elif chunk["tokens"] < very_small_threshold:
                buffer_chunks.append(chunk)
                buffer_tokens += chunk["tokens"]

                # Save buffer if it's large enough or this is the last chunk
                if buffer_tokens >= self.min_chunk_size or i == len(accumulated_chunks) - 1:
                    merged_text = " ".join(c["text"] for c in buffer_chunks)
                    merged_chunks.append({
                        "text": merged_text,
                        "tokens": buffer_tokens,
                        "start": buffer_chunks[0]["start"],
                        "end": buffer_chunks[-1]["end"]
                    })
                    buffer_chunks = []
                    buffer_tokens = 0

            # Chunk is reasonable size - try to merge with buffer or save separately
            else:
                # If we have buffered fragments, try to merge them with this chunk
                if buffer_chunks:
                    # If buffer + current chunk is under max, merge them
                    if (buffer_tokens + chunk["tokens"]) <= self.max_chunk_size:
                        buffer_chunks.append(chunk)
                        buffer_tokens += chunk["tokens"]
                        merged_text = " ".join(c["text"] for c in buffer_chunks)
                        merged_chunks.append({
                            "text": merged_text,
                            "tokens": buffer_tokens,
                            "start": buffer_chunks[0]["start"],
                            "end": buffer_chunks[-1]["end"]
                        })
                        buffer_chunks = []
                        buffer_tokens = 0
                    else:
                        # Can't merge, save buffer and this chunk separately
                        merged_text = " ".join(c["text"] for c in buffer_chunks)
                        merged_chunks.append({
                            "text": merged_text,
                            "tokens": buffer_tokens,
                            "start": buffer_chunks[0]["start"],
                            "end": buffer_chunks[-1]["end"]
                        })
                        buffer_chunks = []
                        buffer_tokens = 0
                        merged_chunks.append(chunk)
                else:
                    # No buffer, save chunk as-is (respecting semantic boundary)
                    merged_chunks.append(chunk)

        # Save any remaining buffer
        # Try to merge with last chunk if buffer is too small
        if buffer_chunks:
            if buffer_tokens < self.min_chunk_size and merged_chunks:
                # Merge with last chunk if possible
                last_chunk = merged_chunks[-1]
                if (last_chunk["tokens"] + buffer_tokens) <= self.max_chunk_size:
                    # Merge buffer into last chunk
                    merged_text = last_chunk["text"] + " " + " ".join(c["text"] for c in buffer_chunks)
                    merged_chunks[-1] = {
                        "text": merged_text,
                        "tokens": last_chunk["tokens"] + buffer_tokens,
                        "start": last_chunk["start"],
                        "end": buffer_chunks[-1]["end"]
                    }
                else:
                    # Can't merge, save buffer as-is
                    merged_text = " ".join(c["text"] for c in buffer_chunks)
                    merged_chunks.append({
                        "text": merged_text,
                        "tokens": buffer_tokens,
                        "start": buffer_chunks[0]["start"],
                        "end": buffer_chunks[-1]["end"]
                    })
            else:
                # Buffer is big enough, save as-is
                merged_text = " ".join(c["text"] for c in buffer_chunks)
                merged_chunks.append({
                    "text": merged_text,
                    "tokens": buffer_tokens,
                    "start": buffer_chunks[0]["start"],
                    "end": buffer_chunks[-1]["end"]
                })

        # Apply overlap if enabled
        if self.overlap_ratio > 0.0 and len(merged_chunks) > 1:
            merged_chunks = self._apply_overlap(merged_chunks)

        # Convert to ChunkResult objects
        for chunk in merged_chunks:
            results.append(ChunkResult(
                text=chunk["text"],
                start_index=chunk["start"],
                end_index=chunk["end"],
                token_count=chunk["tokens"]
            ))

        return results

    def _apply_overlap(self, chunks: list[dict]) -> list[dict]:
        """
        Apply overlap between adjacent chunks for context preservation.

        Creates overlap chunks between each pair of adjacent chunks,
        containing text from the end of one chunk and beginning of the next.

        Args:
            chunks: List of chunk dictionaries with 'text', 'tokens', 'start', 'end'

        Returns:
            List of chunks with overlap chunks inserted between base chunks
        """
        overlapping_chunks = []
        overlap_tokens = int(self.max_chunk_size * self.overlap_ratio)

        for i, chunk in enumerate(chunks):
            # Add current chunk
            overlapping_chunks.append(chunk)

            # Add overlap chunk between this and next (if exists)
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]

                # Create overlap from end of current chunk + start of next chunk
                curr_words = chunk["text"].split()
                next_words = next_chunk["text"].split()

                # Take last N words from current and first N words from next
                # where N is half of overlap_tokens (so total is ~overlap_tokens)
                half_overlap = overlap_tokens // 2

                overlap_from_curr = curr_words[-half_overlap:] if len(curr_words) > half_overlap else curr_words
                overlap_from_next = next_words[:half_overlap] if len(next_words) > half_overlap else next_words

                # Combine to create overlap text
                overlap_text = " ".join(overlap_from_curr + overlap_from_next)
                overlap_token_count = len(overlap_from_curr) + len(overlap_from_next)

                # Calculate approximate character positions for overlap chunk
                # Position it at the boundary between the two chunks
                overlap_start = chunk["end"] - len(" ".join(overlap_from_curr))
                overlap_end = next_chunk["start"] + len(" ".join(overlap_from_next))

                overlap_chunk = {
                    "text": overlap_text,
                    "tokens": overlap_token_count,
                    "start": overlap_start,
                    "end": overlap_end
                }

                overlapping_chunks.append(overlap_chunk)

        return overlapping_chunks

    async def chunk_document(
        self,
        text: str,
        metadata: dict | None = None
    ) -> list[dict]:
        """
        Chunk document and return with metadata (API-compatible format).

        Args:
            text: Document text
            metadata: Optional metadata to attach to chunks

        Returns:
            List of chunk dictionaries
        """
        chunks = await self.chunk_text(text)

        result = []
        for i, chunk in enumerate(chunks):
            chunk_dict = {
                "text": chunk.text,
                "chunk_index": i,
                "token_count": chunk.token_count,
                "start_char": chunk.start_index,
                "end_char": chunk.end_index,
            }

            if metadata:
                chunk_dict.update(metadata)

            result.append(chunk_dict)

        return result
