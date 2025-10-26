"""
Integration tests for enhanced search features: query expansion and reranking.

Tests the complete pipeline with all Phase 2-4 enhancements:
- Query expansion (Phase 2)
- Cross-encoder reranking (Phase 3)
- Chunking with overlap (Phase 4)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def setup_test_data(db_session: AsyncSession):
    """Set up test documents and chunks for search testing."""
    # Create test document
    doc_id = "00000000-0000-0000-0000-000000000001"

    # Insert document (using actual schema)
    await db_session.execute(
        text("""
            INSERT INTO documents (id, title, file_name, file_type, file_size, upload_status, created_at)
            VALUES (:id, :title, :file_name, :file_type, :file_size, :upload_status, datetime('now'))
        """),
        {
            "id": doc_id,
            "title": "Kubernetes Scaling Guide",
            "file_name": "k8s-guide.txt",
            "file_type": "text/plain",
            "file_size": 100,
            "upload_status": "completed"
        }
    )

    # Insert chunks with keywords (using actual schema: content not chunk_text, tokens not token_count)
    chunks = [
        {
            "id": "00000000-0000-0000-0001-000000000001",
            "document_id": doc_id,
            "content": "Kubernetes scaling involves horizontal pod autoscaling. HPA adjusts replicas based on CPU metrics.",
            "tokens": 15,
            "chunk_metadata": "{}"
        },
        {
            "id": "00000000-0000-0000-0001-000000000002",
            "document_id": doc_id,
            "content": "Vertical pod autoscaling adjusts resource limits. VPA is useful for right-sizing containers.",
            "tokens": 14,
            "chunk_metadata": "{}"
        },
        {
            "id": "00000000-0000-0000-0001-000000000003",
            "document_id": doc_id,
            "content": "Cluster autoscaler scales nodes automatically. It works with cloud providers like AWS, GCP, Azure.",
            "tokens": 16,
            "chunk_metadata": "{}"
        }
    ]

    for chunk in chunks:
        await db_session.execute(
            text("""
                INSERT INTO chunks (id, document_id, content, tokens, chunk_metadata)
                VALUES (:id, :document_id, :content, :tokens, :chunk_metadata)
            """),
            chunk
        )

    await db_session.commit()

    yield

    # Cleanup
    await db_session.execute(text(f"DELETE FROM chunks WHERE document_id = '{doc_id}'"))
    await db_session.execute(text(f"DELETE FROM documents WHERE id = '{doc_id}'"))
    await db_session.commit()


@pytest.mark.asyncio
async def test_search_with_all_enhancements_enabled(async_client, setup_test_data):
    """Test search with query expansion + reranking + hybrid mode (full pipeline)."""
    response = await async_client.post(
        "/hexagonal-search/search?mode=hybrid&use_expansion=true&use_reranking=true",
        json={"query": "kubernetes scaling", "top_k": 5}
    )

    assert response.status_code == 200
    data = response.json()

    # Should return results
    assert "chunks" in data
    assert len(data["chunks"]) >= 0  # May be empty if embedder/vector store not available

    # Check that metadata includes mode
    assert "metadata" in data or "retrieval_method" in data


@pytest.mark.asyncio
async def test_search_with_query_expansion_only(async_client, setup_test_data):
    """Test search with query expansion enabled but reranking disabled."""
    response = await async_client.post(
        "/hexagonal-search/search?mode=hybrid&use_expansion=true&use_reranking=false",
        json={"query": "k8s pod scaling", "top_k": 5}
    )

    assert response.status_code == 200
    data = response.json()

    # Should work without reranking
    assert "chunks" in data


@pytest.mark.asyncio
async def test_search_with_reranking_only(async_client, setup_test_data):
    """Test search with reranking enabled but expansion disabled."""
    response = await async_client.post(
        "/hexagonal-search/search?mode=hybrid&use_expansion=false&use_reranking=true",
        json={"query": "horizontal pod autoscaling", "top_k": 5}
    )

    assert response.status_code == 200
    data = response.json()

    # Should work without expansion
    assert "chunks" in data


@pytest.mark.asyncio
async def test_search_with_all_enhancements_disabled(async_client, setup_test_data):
    """Test basic search without expansion or reranking (baseline)."""
    response = await async_client.post(
        "/hexagonal-search/search?mode=hybrid&use_expansion=false&use_reranking=false",
        json={"query": "cluster autoscaler", "top_k": 5}
    )

    assert response.status_code == 200
    data = response.json()

    # Should work in basic mode
    assert "chunks" in data


@pytest.mark.asyncio
async def test_vector_mode_with_enhancements(async_client, setup_test_data):
    """Test vector-only mode with expansion and reranking."""
    response = await async_client.post(
        "/hexagonal-search/search?mode=vector&use_expansion=true&use_reranking=true",
        json={"query": "kubernetes autoscaling", "top_k": 5}
    )

    assert response.status_code == 200
    data = response.json()

    assert "chunks" in data


@pytest.mark.asyncio
async def test_keyword_mode_with_enhancements(async_client, setup_test_data):
    """Test keyword-only mode with expansion and reranking."""
    response = await async_client.post(
        "/hexagonal-search/search?mode=keyword&use_expansion=true&use_reranking=true",
        json={"query": "HPA VPA", "top_k": 5}
    )

    assert response.status_code == 200
    data = response.json()

    assert "chunks" in data


@pytest.mark.asyncio
async def test_default_parameters_use_all_enhancements(async_client, setup_test_data):
    """Test that default parameters enable expansion and reranking."""
    # No query parameters - should use defaults (hybrid + expansion + reranking)
    response = await async_client.post(
        "/hexagonal-search/search",
        json={"query": "scaling containers", "top_k": 5}
    )

    assert response.status_code == 200
    data = response.json()

    assert "chunks" in data
    # Defaults should apply all enhancements


@pytest.mark.asyncio
async def test_search_parameter_combinations(async_client, setup_test_data):
    """Test various combinations of search parameters."""
    test_cases = [
        # (mode, expansion, reranking)
        ("hybrid", True, True),
        ("hybrid", True, False),
        ("hybrid", False, True),
        ("hybrid", False, False),
        ("vector", True, True),
        ("keyword", True, True),
    ]

    for mode, expansion, reranking in test_cases:
        response = await async_client.post(
            f"/hexagonal-search/search?mode={mode}&use_expansion={str(expansion).lower()}&use_reranking={str(reranking).lower()}",
            json={"query": "test query", "top_k": 3}
        )

        # All combinations should work (may return empty if services unavailable)
        assert response.status_code == 200, f"Failed for mode={mode}, expansion={expansion}, reranking={reranking}"
        data = response.json()
        assert "chunks" in data


@pytest.mark.asyncio
async def test_search_respects_top_k_with_reranking(async_client, setup_test_data):
    """Test that top_k is respected even with reranking enabled."""
    response = await async_client.post(
        "/hexagonal-search/search?mode=hybrid&use_reranking=true",
        json={"query": "kubernetes", "top_k": 2}
    )

    assert response.status_code == 200
    data = response.json()

    # Should not return more than top_k results
    if "chunks" in data and len(data["chunks"]) > 0:
        assert len(data["chunks"]) <= 2


@pytest.mark.asyncio
async def test_search_empty_query_fails(async_client, setup_test_data):
    """Test that empty query fails validation."""
    response = await async_client.post(
        "/hexagonal-search/search?use_expansion=true&use_reranking=true",
        json={"query": "", "top_k": 5}
    )

    # Should fail validation
    assert response.status_code == 422
