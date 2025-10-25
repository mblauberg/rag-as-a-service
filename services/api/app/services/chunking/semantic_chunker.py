"""
Semantic chunking using LangChain's experimental SemanticChunker.
Uses percentile-based breakpoint detection for adaptive splitting.
"""

from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


class ChunkResult(BaseModel):
    """Result of chunking operation"""
    text: str
    start_index: int
    end_index: int
    token_count: int | None = None
    coherence_score: float | None = None


class SentenceTransformerEmbeddings(Embeddings):
    """Wrapper to make SentenceTransformer compatible with LangChain"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query"""
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()


class SemanticChunker:
    """
    Semantic chunking using percentile-based breakpoint detection.

    Splits text based on semantic similarity between sentences:
    1. Splits into sentences
    2. Embeds each sentence
    3. Calculates similarity between adjacent sentences
    4. Creates boundary when similarity drop exceeds percentile threshold
    """

    def __init__(
        self,
        min_chunk_size: int = 128,
        max_chunk_size: int = 512,
        breakpoint_percentile: float = 95.0,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize semantic chunker.

        Args:
            min_chunk_size: Minimum tokens per chunk (avoid fragments)
            max_chunk_size: Maximum tokens per chunk (context limit)
            breakpoint_percentile: Percentile for boundary detection (95 = top 5% drops)
            embedding_model: Model for sentence embeddings
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.breakpoint_percentile = breakpoint_percentile

        # Initialize embeddings wrapper
        self.embeddings = SentenceTransformerEmbeddings(embedding_model)

        # Initialize LangChain semantic chunker
        self.chunker = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=breakpoint_percentile
        )

    async def chunk_text(self, text: str) -> list[ChunkResult]:
        """
        Chunk text using semantic similarity.

        Args:
            text: Input text to chunk

        Returns:
            List of ChunkResult objects
        """
        # Use LangChain's semantic chunker
        documents = self.chunker.create_documents([text])

        # Convert to ChunkResult format with size constraints
        results = []
        current_index = 0
        accumulated_chunks = []

        for doc in documents:
            chunk_text = doc.page_content.strip()
            token_count = len(chunk_text.split())

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

        # Convert to ChunkResult objects
        for chunk in merged_chunks:
            results.append(ChunkResult(
                text=chunk["text"],
                start_index=chunk["start"],
                end_index=chunk["end"],
                token_count=chunk["tokens"]
            ))

        return results

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
