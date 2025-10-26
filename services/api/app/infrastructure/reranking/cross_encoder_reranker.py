"""Cross-encoder reranker using Sentence Transformers."""
import numpy as np
from sentence_transformers import CrossEncoder

from app.domain.entities.chunk import Chunk
from app.ports.services import Reranker


class CrossEncoderRerankerImpl(Reranker):
    """Cross-encoder based reranking.

    Uses BERT-based cross-encoder to compute query-document
    relevance scores. More accurate but slower than bi-encoders.

    Recommended for reranking top-50 to top-10.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize cross-encoder model.

        Args:
            model_name: HuggingFace cross-encoder model
                       (default: MS MARCO MiniLM - fast and accurate)
        """
        # Fix for PyTorch meta tensor issue in newer transformers
        self.model = CrossEncoder(model_name, device='cpu')

    async def rerank(self, query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
        """Rerank chunks using cross-encoder scores.

        Creates query-chunk pairs and scores them jointly.
        Much more accurate than cosine similarity.

        Attaches normalized cross-encoder relevance scores (0-1) to chunk.score field.
        Uses min-max normalization to map raw scores to [0, 1] range.
        """
        if not chunks:
            return []

        # Create query-chunk pairs
        pairs = [(query, chunk.content) for chunk in chunks]

        # Score all pairs (batch processing)
        raw_scores = self.model.predict(pairs)

        # Normalize scores to 0-1 range using min-max normalization
        # This ensures top result gets 1.0, worst gets 0.0, rest in between
        min_score = float(np.min(raw_scores))
        max_score = float(np.max(raw_scores))
        score_range = max_score - min_score

        if score_range > 0:
            normalized_scores = [(s - min_score) / score_range for s in raw_scores]
        else:
            # All scores identical - assign 1.0 to all
            normalized_scores = [1.0] * len(raw_scores)

        # Sort by normalized score (descending) and attach scores to chunks
        chunk_scores = list(zip(chunks, normalized_scores))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        # Attach normalized scores to chunks and return top_k
        reranked_chunks = []
        for chunk, score in chunk_scores[:top_k]:
            chunk.score = float(score)
            reranked_chunks.append(chunk)

        return reranked_chunks
