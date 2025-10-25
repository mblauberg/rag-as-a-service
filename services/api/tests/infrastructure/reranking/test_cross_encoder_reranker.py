"""Tests for CrossEncoderRerankerImpl."""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
import numpy as np

from app.domain.entities.chunk import Chunk
from app.infrastructure.reranking.cross_encoder_reranker import CrossEncoderRerankerImpl


class TestCrossEncoderRerankerImpl:
    """Test suite for CrossEncoderRerankerImpl."""

    @pytest.fixture
    def mock_cross_encoder(self):
        """Fixture for mocked CrossEncoder."""
        mock_model = MagicMock()
        return mock_model

    @pytest.fixture
    def reranker(self, mock_cross_encoder):
        """Fixture for CrossEncoderRerankerImpl with mocked model."""
        with patch("app.infrastructure.reranking.cross_encoder_reranker.CrossEncoder") as mock_class:
            mock_class.return_value = mock_cross_encoder
            return CrossEncoderRerankerImpl()

    @pytest.fixture
    def sample_chunks(self):
        """Fixture for sample chunks."""
        doc_id = uuid4()
        return [
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="Python is a programming language",
                tokens=6,
                embedding_vector=[0.1, 0.2, 0.3]
            ),
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="The weather is sunny today",
                tokens=5,
                embedding_vector=[0.4, 0.5, 0.6]
            ),
            Chunk(
                id=uuid4(),
                document_id=doc_id,
                content="Python uses indentation for code blocks",
                tokens=6,
                embedding_vector=[0.7, 0.8, 0.9]
            ),
        ]

    @pytest.mark.asyncio
    async def test_rerank_basic_functionality(self, reranker, mock_cross_encoder, sample_chunks):
        """Test basic reranking functionality."""
        query = "Python programming"

        # Mock scores: third chunk (index 2) most relevant, first (index 0) second, second (index 1) least
        mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

        result = await reranker.rerank(query, sample_chunks, top_k=3)

        # Verify predict was called with correct pairs
        mock_cross_encoder.predict.assert_called_once()
        call_args = mock_cross_encoder.predict.call_args[0][0]

        assert len(call_args) == 3
        assert call_args[0] == (query, sample_chunks[0].content)
        assert call_args[1] == (query, sample_chunks[1].content)
        assert call_args[2] == (query, sample_chunks[2].content)

        # Verify results are sorted by score (descending)
        assert len(result) == 3
        assert result[0] == sample_chunks[2]  # Score 0.9
        assert result[1] == sample_chunks[0]  # Score 0.7
        assert result[2] == sample_chunks[1]  # Score 0.3

    @pytest.mark.asyncio
    async def test_rerank_with_top_k(self, reranker, mock_cross_encoder, sample_chunks):
        """Test reranking respects top_k parameter."""
        query = "Python programming"

        # Mock scores
        mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

        result = await reranker.rerank(query, sample_chunks, top_k=2)

        # Verify only top 2 returned
        assert len(result) == 2
        assert result[0] == sample_chunks[2]  # Score 0.9
        assert result[1] == sample_chunks[0]  # Score 0.7

    @pytest.mark.asyncio
    async def test_rerank_top_k_larger_than_chunks(self, reranker, mock_cross_encoder, sample_chunks):
        """Test reranking when top_k is larger than available chunks."""
        query = "Python programming"

        # Mock scores
        mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

        result = await reranker.rerank(query, sample_chunks, top_k=10)

        # Verify all chunks returned (only 3 available)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_rerank_empty_chunks(self, reranker, mock_cross_encoder):
        """Test reranking with empty chunk list."""
        query = "test query"

        result = await reranker.rerank(query, [], top_k=5)

        # Verify empty list returned
        assert result == []

        # Verify model was not called
        mock_cross_encoder.predict.assert_not_called()

    @pytest.mark.asyncio
    async def test_rerank_single_chunk(self, reranker, mock_cross_encoder, sample_chunks):
        """Test reranking with single chunk."""
        query = "test query"
        single_chunk = [sample_chunks[0]]

        # Mock score
        mock_cross_encoder.predict.return_value = np.array([0.8])

        result = await reranker.rerank(query, single_chunk, top_k=1)

        # Verify single chunk returned
        assert len(result) == 1
        assert result[0] == single_chunk[0]

    @pytest.mark.asyncio
    async def test_rerank_chunks_reordered_by_relevance(self, reranker, mock_cross_encoder, sample_chunks):
        """Test that chunks are properly reordered by relevance score."""
        query = "weather forecast"

        # Mock scores: second chunk (weather) most relevant
        mock_cross_encoder.predict.return_value = np.array([0.2, 0.95, 0.1])

        result = await reranker.rerank(query, sample_chunks, top_k=3)

        # Verify weather chunk is first (highest score)
        assert result[0] == sample_chunks[1]
        assert result[0].content == "The weather is sunny today"

        # Verify proper ordering
        assert result[1] == sample_chunks[0]  # Score 0.2
        assert result[2] == sample_chunks[2]  # Score 0.1

    @pytest.mark.asyncio
    async def test_rerank_with_zero_top_k(self, reranker, mock_cross_encoder, sample_chunks):
        """Test reranking with top_k=0."""
        query = "test query"

        # Mock scores
        mock_cross_encoder.predict.return_value = np.array([0.7, 0.3, 0.9])

        result = await reranker.rerank(query, sample_chunks, top_k=0)

        # Verify empty list returned
        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_preserves_chunk_properties(self, reranker, mock_cross_encoder):
        """Test that reranking preserves all chunk properties."""
        doc_id = uuid4()
        chunk_with_metadata = Chunk(
            id=uuid4(),
            document_id=doc_id,
            content="Test content",
            tokens=2,
            embedding_vector=[0.1, 0.2],
            metadata={"source": "test.pdf", "page": 5},
            section_title="Introduction",
            section_level=1,
            page_number=5
        )

        query = "test"
        mock_cross_encoder.predict.return_value = np.array([0.8])

        result = await reranker.rerank(query, [chunk_with_metadata], top_k=1)

        # Verify all properties preserved
        reranked_chunk = result[0]
        assert reranked_chunk.id == chunk_with_metadata.id
        assert reranked_chunk.document_id == chunk_with_metadata.document_id
        assert reranked_chunk.content == chunk_with_metadata.content
        assert reranked_chunk.tokens == chunk_with_metadata.tokens
        assert reranked_chunk.embedding_vector == chunk_with_metadata.embedding_vector
        assert reranked_chunk.metadata == {"source": "test.pdf", "page": 5}
        assert reranked_chunk.section_title == "Introduction"
        assert reranked_chunk.section_level == 1
        assert reranked_chunk.page_number == 5

    def test_initialization_default_model(self):
        """Test initialization with default model."""
        with patch("app.infrastructure.reranking.cross_encoder_reranker.CrossEncoder") as mock_class:
            reranker = CrossEncoderRerankerImpl()

            # Verify default model is used
            mock_class.assert_called_once_with("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def test_initialization_custom_model(self):
        """Test initialization with custom model."""
        with patch("app.infrastructure.reranking.cross_encoder_reranker.CrossEncoder") as mock_class:
            custom_model = "cross-encoder/ms-marco-TinyBERT-L-2-v2"
            reranker = CrossEncoderRerankerImpl(model_name=custom_model)

            # Verify custom model is used
            mock_class.assert_called_once_with(custom_model)

    @pytest.mark.asyncio
    async def test_rerank_handles_identical_scores(self, reranker, mock_cross_encoder, sample_chunks):
        """Test reranking when chunks have identical scores."""
        query = "test query"

        # Mock identical scores
        mock_cross_encoder.predict.return_value = np.array([0.5, 0.5, 0.5])

        result = await reranker.rerank(query, sample_chunks, top_k=2)

        # Verify top_k chunks returned (order may vary for identical scores)
        assert len(result) == 2
        assert all(chunk in sample_chunks for chunk in result)
