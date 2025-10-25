"""Cross-encoder reranking service for improving retrieval precision."""
import logging

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class RerankerService:
    """Reranks search results using cross-encoder for better precision."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Initialize reranker with cross-encoder model.

        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Reranker model loaded successfully")

    def rerank(
        self,
        query: str,
        candidates: list[str],
        top_k: int = 10
    ) -> list[tuple[int, float]]:
        """
        Rerank candidate documents and return top-K with scores.

        Args:
            query: Search query string
            candidates: List of candidate document texts
            top_k: Number of top results to return

        Returns:
            List of (index, score) tuples sorted by score descending
        """
        if not candidates:
            return []

        # Create query-document pairs
        pairs = [(query, candidate) for candidate in candidates]

        # Score all pairs
        scores = self.model.predict(pairs)

        # Sort by score descending and return top-K
        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked[:top_k]
