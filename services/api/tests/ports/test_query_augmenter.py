"""Tests for QueryAugmenter port."""
import pytest

from app.ports.services import QueryAugmenter


class MockQueryAugmenter(QueryAugmenter):
    """Mock implementation for testing."""

    async def expand(
        self,
        query: str,
        num_variants: int = 2,
        method: str = "llm"
    ) -> list[str]:
        """Return original query plus mock variants."""
        return [query] + [f"variant_{i}" for i in range(num_variants)]


@pytest.mark.asyncio
async def test_query_augmenter_port_contract():
    """Test that QueryAugmenter port has correct interface."""
    augmenter = MockQueryAugmenter()

    results = await augmenter.expand(
        query="test query",
        num_variants=2,
        method="llm"
    )

    assert isinstance(results, list)
    assert len(results) == 3
    assert results[0] == "test query"


@pytest.mark.asyncio
async def test_query_augmenter_returns_original_query():
    """Test that expand always includes original query."""
    augmenter = MockQueryAugmenter()

    results = await augmenter.expand("original query")

    # Should always include original query
    assert "original query" in results


@pytest.mark.asyncio
async def test_query_augmenter_respects_num_variants():
    """Test that expand respects num_variants parameter."""
    augmenter = MockQueryAugmenter()

    # Test with 0 variants (just original)
    results = await augmenter.expand("test", num_variants=0)
    assert len(results) == 1
    assert results[0] == "test"

    # Test with 3 variants
    results = await augmenter.expand("test", num_variants=3)
    assert len(results) == 4  # original + 3 variants


@pytest.mark.asyncio
async def test_query_augmenter_method_parameter():
    """Test that expand accepts method parameter."""
    augmenter = MockQueryAugmenter()

    # Should accept "llm" method
    results = await augmenter.expand("test", method="llm")
    assert isinstance(results, list)

    # Should accept other methods (contract test, doesn't validate behavior)
    results = await augmenter.expand("test", method="synonyms")
    assert isinstance(results, list)
