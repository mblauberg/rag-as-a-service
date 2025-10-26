"""Tests for KeywordStore port."""
from uuid import UUID, uuid4

import pytest

from app.domain.entities.chunk import Chunk
from app.ports.services import KeywordStore


class MockKeywordStore(KeywordStore):
    """Mock implementation for testing."""

    async def search(
        self, query_text: str, top_k: int, document_id: UUID | None = None
    ) -> list[Chunk]:
        return []


@pytest.mark.asyncio
async def test_keyword_store_port_contract():
    """Test that KeywordStore port has correct interface."""
    store = MockKeywordStore()

    results = await store.search(query_text="test query", top_k=10)

    assert isinstance(results, list)
