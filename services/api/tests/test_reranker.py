import pytest
from app.services.reranker import RerankerService


@pytest.mark.asyncio
async def test_reranker_initializes():
    """Test that reranker service loads the model successfully."""
    reranker = RerankerService()
    assert reranker.model is not None
    assert hasattr(reranker.model, 'predict')


@pytest.mark.asyncio
async def test_reranker_reranks_correctly():
    """Test that reranker ranks relevant docs higher."""
    reranker = RerankerService()

    query = "What is machine learning?"
    candidates = [
        "Machine learning is a subset of artificial intelligence.",
        "I like to eat pizza for dinner.",
        "Deep learning uses neural networks for pattern recognition.",
    ]

    results = reranker.rerank(query, candidates, top_k=3)

    # Should return 3 results
    assert len(results) == 3

    # Each result is (index, score) tuple
    assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    # First result should be index 0 (most relevant)
    assert results[0][0] == 0

    # Last result should be index 1 (least relevant - pizza)
    assert results[2][0] == 1
