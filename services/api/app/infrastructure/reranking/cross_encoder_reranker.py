"""Cross-encoder reranker using Sentence Transformers."""
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
        self.model = CrossEncoder(model_name)

    async def rerank(self, query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
        """Rerank chunks using cross-encoder scores.

        Creates query-chunk pairs and scores them jointly.
        Much more accurate than cosine similarity.
        """
        if not chunks:
            return []

        # Create query-chunk pairs
        pairs = [(query, chunk.content) for chunk in chunks]

        # Score all pairs (batch processing)
        scores = self.model.predict(pairs)

        # Sort by score (descending)
        chunk_scores = list(zip(chunks, scores))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        # Return top_k
        return [chunk for chunk, _ in chunk_scores[:top_k]]
