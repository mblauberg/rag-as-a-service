import pytest
from app.services.reranker import RerankerService


@pytest.mark.asyncio
async def test_reranker_initializes():
    """Test that reranker service loads the model successfully."""
    reranker = RerankerService()
    assert reranker.model is not None
    assert hasattr(reranker.model, 'predict')
