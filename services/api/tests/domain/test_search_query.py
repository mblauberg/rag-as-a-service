"""Tests for SearchQuery value object."""
import pytest

from app.domain.value_objects.search_query import SearchQuery


def test_search_query_creation():
    """Test creating a search query."""
    query = SearchQuery(text="test query", top_k=10)

    assert query.text == "test query"
    assert query.top_k == 10


def test_search_query_default_top_k():
    """Test default top_k value."""
    query = SearchQuery(text="test")

    assert query.top_k == 5


def test_search_query_immutable():
    """Test that SearchQuery is immutable."""
    query = SearchQuery(text="test", top_k=5)

    with pytest.raises(Exception):  # dataclass frozen raises on assignment
        query.text = "modified"


def test_search_query_validates_top_k_min():
    """Test top_k minimum validation."""
    with pytest.raises(ValueError, match="top_k must be between 1 and 100"):
        SearchQuery(text="test", top_k=0)


def test_search_query_validates_top_k_max():
    """Test top_k maximum validation."""
    with pytest.raises(ValueError, match="top_k must be between 1 and 100"):
        SearchQuery(text="test", top_k=101)
