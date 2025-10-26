"""Tests for FusionService port."""
from uuid import uuid4

import pytest

from app.domain.entities.chunk import Chunk
from app.ports.services import FusionService


class MockFusionService(FusionService):
    """Mock implementation for testing."""

    def fuse(
        self, result_sets: list[list[Chunk]], method: str = "rrf", k: int = 60
    ) -> list[Chunk]:
        return []


def test_fusion_service_port_contract():
    """Test that FusionService port has correct interface."""
    service = MockFusionService()

    chunk = Chunk(id=uuid4(), document_id=uuid4(), content="test", tokens=1)

    results = service.fuse([[chunk]], method="rrf", k=60)

    assert isinstance(results, list)
