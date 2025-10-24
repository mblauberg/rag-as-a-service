import pytest
from app.services.bm25_search import BM25SearchService
from app.models.document import DocumentChunk
from uuid import uuid4


@pytest.mark.asyncio
async def test_bm25_search_returns_ranked_results(db_session):
    """Test BM25 search returns results ranked by relevance"""
    # Create test document ID
    doc_id = uuid4()

    # Create test chunks
    chunks = [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            chunk_text="Kubernetes deployment configuration for production environments",
            token_count=7
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            chunk_text="Docker container networking and service discovery mechanisms",
            token_count=7
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=2,
            chunk_text="Python programming best practices and design patterns",
            token_count=7
        ),
    ]

    for chunk in chunks:
        db_session.add(chunk)
    await db_session.commit()

    # Search for kubernetes-related content
    bm25_service = BM25SearchService(db_session)
    results = await bm25_service.search("kubernetes deployment", limit=5)

    # Should return kubernetes chunk first
    assert len(results) > 0
    assert "kubernetes" in results[0].chunk_text.lower()

    # Verify chunks have BM25 scores attached
    assert hasattr(results[0], 'bm25_score')
    assert results[0].bm25_score is not None
    assert results[0].bm25_score > 0


@pytest.mark.asyncio
async def test_bm25_search_with_no_matches(db_session):
    """Test BM25 search returns empty list when no matches"""
    bm25_service = BM25SearchService(db_session)
    results = await bm25_service.search("nonexistent query terms", limit=5)

    assert results == []


@pytest.mark.asyncio
async def test_bm25_search_respects_limit(db_session):
    """Test BM25 search respects limit parameter"""
    doc_id = uuid4()

    # Create many test chunks
    for i in range(10):
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=i,
            chunk_text=f"Kubernetes cluster deployment configuration number {i}",
            token_count=6
        )
        db_session.add(chunk)
    await db_session.commit()

    bm25_service = BM25SearchService(db_session)
    results = await bm25_service.search("kubernetes cluster", limit=3)

    # Should return exactly 3 results
    assert len(results) == 3


@pytest.mark.asyncio
async def test_bm25_search_filters_by_document_id(db_session):
    """Test BM25 search can filter by document ID"""
    doc_id_1 = uuid4()
    doc_id_2 = uuid4()

    # Create chunks for two different documents
    chunk1 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id_1,
        chunk_index=0,
        chunk_text="Kubernetes deployment in production",
        token_count=4
    )
    chunk2 = DocumentChunk(
        id=uuid4(),
        document_id=doc_id_2,
        chunk_index=0,
        chunk_text="Kubernetes configuration best practices",
        token_count=4
    )

    db_session.add(chunk1)
    db_session.add(chunk2)
    await db_session.commit()

    bm25_service = BM25SearchService(db_session)

    # Search with document filter
    results = await bm25_service.search("kubernetes", limit=5, document_ids=[doc_id_1])

    # Should only return chunk from doc_id_1
    assert len(results) == 1
    assert results[0].document_id == doc_id_1
