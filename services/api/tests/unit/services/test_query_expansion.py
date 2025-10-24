"""Tests for Query Expansion Service."""
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.query_expansion import QueryExpansionService


@pytest.mark.asyncio
async def test_query_expansion_generates_alternatives():
    """Test query expansion generates alternative phrasings"""
    # Create mock generator client
    mock_generator = Mock()
    mock_response = Mock()
    mock_response.text = 'kubernetes pod deployment troubleshooting\ncontainer orchestration startup failures'
    mock_generator.generate = AsyncMock(return_value=mock_response)

    expansion_service = QueryExpansionService(mock_generator)

    queries = await expansion_service.expand_query("k8s pod fails")

    # Should return original + 2 alternatives (3 total)
    assert len(queries) == 3
    assert queries[0] == "k8s pod fails"  # Original first
    assert "kubernetes" in queries[1].lower() or "kubernetes" in queries[2].lower()


@pytest.mark.asyncio
async def test_query_expansion_handles_llm_failure():
    """Test query expansion returns original query if LLM fails"""
    # Create mock generator client that raises exception
    mock_generator = Mock()
    mock_generator.generate = AsyncMock(side_effect=Exception("LLM failure"))

    expansion_service = QueryExpansionService(mock_generator)

    queries = await expansion_service.expand_query("test query")

    # Should return at least original query
    assert len(queries) >= 1
    assert queries[0] == "test query"


@pytest.mark.asyncio
async def test_query_expansion_handles_none_response():
    """Test query expansion handles None response from LLM"""
    # Create mock generator client that returns None
    mock_generator = Mock()
    mock_generator.generate = AsyncMock(return_value=None)

    expansion_service = QueryExpansionService(mock_generator)

    queries = await expansion_service.expand_query("test query")

    # Should return only original query
    assert len(queries) == 1
    assert queries[0] == "test query"


@pytest.mark.asyncio
async def test_query_expansion_empty_query():
    """Test query expansion handles empty query string"""
    mock_generator = Mock()
    mock_response = Mock()
    mock_response.text = 'alternative 1\nalternative 2'
    mock_generator.generate = AsyncMock(return_value=mock_response)

    expansion_service = QueryExpansionService(mock_generator)

    queries = await expansion_service.expand_query("")

    # Should return empty string as first element
    assert len(queries) >= 1
    assert queries[0] == ""


@pytest.mark.asyncio
async def test_query_expansion_parse_alternatives_with_prefix():
    """Test parsing alternatives with 'Alternative N:' prefix"""
    mock_generator = Mock()
    mock_response = Mock()
    mock_response.text = '''Alternative 1: kubernetes deployment issues
Alternative 2: k8s pod startup problems'''
    mock_generator.generate = AsyncMock(return_value=mock_response)

    expansion_service = QueryExpansionService(mock_generator)

    queries = await expansion_service.expand_query("k8s deployment fails")

    # Should parse correctly and remove prefixes
    assert len(queries) == 3
    assert queries[0] == "k8s deployment fails"
    assert "kubernetes deployment issues" in queries[1]
    assert "k8s pod startup problems" in queries[2]


@pytest.mark.asyncio
async def test_query_expansion_exactly_two_alternatives():
    """Test that expansion returns exactly 3 queries total"""
    mock_generator = Mock()
    mock_response = Mock()
    # Return more than 2 alternatives (should be limited to 2)
    mock_response.text = '''query alternative one
query alternative two
query alternative three
query alternative four'''
    mock_generator.generate = AsyncMock(return_value=mock_response)

    expansion_service = QueryExpansionService(mock_generator)

    queries = await expansion_service.expand_query("test")

    # Should limit to exactly 3 total (original + 2 alternatives)
    assert len(queries) == 3
    assert queries[0] == "test"
    assert queries[1] == "query alternative one"
    assert queries[2] == "query alternative two"
