"""Tests for search service schemas."""
import pytest
from uuid import uuid4
from app.models.domain import Chunk
from app.models.schemas import SearchRequest, SearchResponse, SearchMode


class TestChunk:
    """Test Chunk domain model."""

    def test_chunk_creation_minimal(self):
        """Test creating chunk with minimal fields."""
        chunk_id = uuid4()
        doc_id = uuid4()

        chunk = Chunk(
            id=chunk_id,
            document_id=doc_id,
            content="Test content",
            tokens=2
        )

        assert chunk.id == chunk_id
        assert chunk.document_id == doc_id
        assert chunk.content == "Test content"
        assert chunk.tokens == 2
        assert chunk.score is None
        assert chunk.document_title is None

    def test_chunk_with_score(self):
        """Test chunk with relevance score."""
        chunk = Chunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Content",
            tokens=1,
            score=0.95
        )

        assert chunk.score == 0.95

    def test_chunk_with_score_method_immutability(self):
        """Test that with_score creates a new instance and doesn't mutate original."""
        original = Chunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Test content",
            tokens=5,
            score=0.5
        )

        # Create new chunk with different score
        updated = original.with_score(0.95)

        # Verify original is unchanged
        assert original.score == 0.5
        # Verify new chunk has updated score
        assert updated.score == 0.95
        # Verify they are different instances
        assert original is not updated
        # Verify other fields are the same
        assert original.id == updated.id
        assert original.document_id == updated.document_id
        assert original.content == updated.content
        assert original.tokens == updated.tokens


class TestSearchRequest:
    """Test SearchRequest schema."""

    def test_search_request_minimal(self):
        """Test search request with minimal fields."""
        request = SearchRequest(query="test query")

        assert request.query == "test query"
        assert request.top_k == 10  # default
        assert request.mode == SearchMode.HYBRID  # default

    def test_search_request_custom_params(self):
        """Test search request with custom parameters."""
        request = SearchRequest(
            query="test",
            top_k=20,
            mode=SearchMode.VECTOR,
            use_expansion=False,
            use_reranking=False
        )

        assert request.top_k == 20
        assert request.mode == SearchMode.VECTOR
        assert request.use_expansion is False
        assert request.use_reranking is False

    def test_search_request_validates_empty_query(self):
        """Test that empty query is rejected."""
        with pytest.raises(ValueError):
            SearchRequest(query="")

    def test_search_request_validates_whitespace_query(self):
        """Test that whitespace-only query is rejected."""
        with pytest.raises(ValueError):
            SearchRequest(query="   ")


class TestSearchResponse:
    """Test SearchResponse schema."""

    def test_search_response_creation(self):
        """Test creating search response."""
        response = SearchResponse(
            query="test",
            results=[],
            total_results=0
        )

        assert response.query == "test"
        assert response.results == []
        assert response.total_results == 0
