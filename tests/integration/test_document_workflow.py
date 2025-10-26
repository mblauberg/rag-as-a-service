"""Integration tests for document upload workflow.

Tests the complete flow: API → chunking → embedding → Qdrant storage → search.

This integration test verifies the end-to-end document processing pipeline:
1. Document upload via API endpoint
2. File validation and text extraction
3. Semantic chunking of document text
4. Embedding generation via embedder microservice
5. Vector storage in Qdrant
6. Document metadata persistence in PostgreSQL
7. Document status transitions
8. Search retrieval of uploaded chunks

The test requires running services (API, embedder, Qdrant, PostgreSQL)
and will be skipped if RUN_INTEGRATION_TESTS environment variable is not set.
"""
import asyncio
import os
from typing import AsyncGenerator

import httpx
import pytest
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse


# Skip marker for integration tests
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require running services (set RUN_INTEGRATION_TESTS=1)",
)


@pytest.fixture
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create async HTTP client for API service.

    Yields:
        AsyncClient configured with 30-second timeout for API operations.
    """
    async with httpx.AsyncClient(
        base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        timeout=30.0,
    ) as client:
        yield client


@pytest.fixture
async def qdrant_client() -> QdrantClient:
    """Create Qdrant client for vector store verification.

    Returns:
        QdrantClient instance connected to test Qdrant instance.
    """
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        timeout=10.0,
    )


@pytest.fixture
def sample_document() -> tuple[str, bytes, str]:
    """Create sample document content for testing.

    Returns:
        Tuple of (filename, content, title) for document upload.
    """
    content = b"""Semantic Search and Retrieval-Augmented Generation

Semantic search uses vector embeddings to find similar documents based on meaning
rather than just keyword matching. This enables more intelligent information retrieval
that understands context and intent.

Vector embeddings are numerical representations of text that capture semantic meaning.
Documents are converted into high-dimensional vectors where similar meanings are
positioned close together in the vector space.

Retrieval-Augmented Generation (RAG) combines semantic search with large language models.
The system retrieves relevant documents using vector search, then uses those documents
as context for generating accurate, grounded responses.

Hybrid search combines vector search with traditional keyword search using techniques
like Reciprocal Rank Fusion. This approach achieves better accuracy than either method
alone by balancing semantic understanding with exact term matching.

Cross-encoder reranking further improves precision by computing interaction scores
between the query and each candidate document. This two-stage retrieval approach
optimizes both recall and precision.
"""
    filename = "semantic_search_guide.txt"
    title = "Semantic Search and RAG Guide"
    return filename, content, title


@pytest.mark.asyncio
async def test_full_document_upload_workflow(
    api_client: httpx.AsyncClient,
    qdrant_client: QdrantClient,
    sample_document: tuple[str, bytes, str],
) -> None:
    """Test complete document upload workflow: API → chunking → embedding → Qdrant.

    This test verifies the entire RAG pipeline:
    1. Document uploads successfully via API
    2. File is validated and processed
    3. Text is chunked into semantic segments
    4. Chunks are embedded via embedder microservice
    5. Vectors are stored in Qdrant vector database
    6. Document metadata is saved in PostgreSQL
    7. Document status transitions to 'completed'
    8. Uploaded chunks can be retrieved via search
    9. Cleanup properly removes all data

    Args:
        api_client: HTTP client for API service.
        qdrant_client: Client for Qdrant vector store verification.
        sample_document: Test document content and metadata.

    Raises:
        AssertionError: If any step of the workflow fails.
    """
    filename, content, title = sample_document
    doc_id = None
    chunk_count = 0

    try:
        # ===== STEP 1: Upload document via API =====
        files = {"file": (filename, content, "text/plain")}
        data = {
            "title": title,
            "description": "Integration test document for RAG pipeline",
        }

        response = await api_client.post(
            "/api/v1/documents/upload", files=files, data=data
        )

        # Verify upload succeeded
        assert response.status_code == 201, (
            f"Upload failed with status {response.status_code}: {response.text}"
        )

        upload_result = response.json()
        assert "document" in upload_result, "Response missing 'document' field"
        assert "chunk_count" in upload_result, "Response missing 'chunk_count' field"
        assert "message" in upload_result, "Response missing 'message' field"

        # Extract document details
        document = upload_result["document"]
        doc_id = document["id"]
        chunk_count = upload_result["chunk_count"]

        # Verify document metadata
        assert document["title"] == title, "Document title mismatch"
        assert document["file_name"] == filename, "Filename mismatch"
        assert document["file_type"] == "text/plain", "File type mismatch"
        assert document["upload_status"] in [
            "processing",
            "completed",
        ], f"Unexpected upload status: {document['upload_status']}"
        assert chunk_count > 0, f"No chunks created (expected > 0, got {chunk_count})"

        # ===== STEP 2: Wait for processing to complete =====
        # Processing may be async, so poll until status is 'completed'
        max_wait_seconds = 30
        for attempt in range(max_wait_seconds):
            response = await api_client.get(f"/api/v1/documents/{doc_id}")
            assert response.status_code == 200, (
                f"Failed to fetch document: {response.status_code}"
            )

            document = response.json()
            upload_status = document["upload_status"]
            embedding_status = document.get("embedding_status", "unknown")

            # Check if processing complete
            if upload_status == "completed" and embedding_status == "completed":
                break

            # Check for failure
            if upload_status == "failed" or embedding_status == "failed":
                pytest.fail(
                    f"Document processing failed: upload={upload_status}, "
                    f"embedding={embedding_status}"
                )

            # Wait before next poll
            await asyncio.sleep(1)
        else:
            # Timeout - processing didn't complete
            pytest.fail(
                f"Document processing did not complete within {max_wait_seconds}s. "
                f"Status: upload={upload_status}, embedding={embedding_status}"
            )

        # ===== STEP 3: Verify document details include chunks =====
        response = await api_client.get(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200, "Failed to retrieve document details"

        document_detail = response.json()
        assert "chunks" in document_detail, "Document detail missing chunks"

        chunks = document_detail["chunks"]
        assert len(chunks) == chunk_count, (
            f"Chunk count mismatch: expected {chunk_count}, got {len(chunks)}"
        )

        # Verify chunk structure
        for idx, chunk in enumerate(chunks):
            assert "id" in chunk, f"Chunk {idx} missing 'id' field"
            assert "content" in chunk, f"Chunk {idx} missing 'content' field"
            assert "chunk_index" in chunk, f"Chunk {idx} missing 'chunk_index' field"
            assert "document_id" in chunk, f"Chunk {idx} missing 'document_id' field"
            assert chunk["document_id"] == doc_id, (
                f"Chunk {idx} has wrong document_id"
            )
            assert len(chunk["content"]) > 0, f"Chunk {idx} has empty content"

        # ===== STEP 4: Verify vectors stored in Qdrant =====
        try:
            # Check if collection exists
            collections = qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            collection_name = os.getenv("QDRANT_COLLECTION", "documents")

            assert collection_name in collection_names, (
                f"Qdrant collection '{collection_name}' not found. "
                f"Available: {collection_names}"
            )

            # Verify points exist for this document
            # Search for points with matching document_id in payload
            search_result = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "document_id",
                            "match": {"value": doc_id}
                        }
                    ]
                },
                limit=100,
            )

            vectors = search_result[0]  # First element is the list of points
            assert len(vectors) == chunk_count, (
                f"Vector count mismatch in Qdrant: expected {chunk_count}, "
                f"got {len(vectors)}"
            )

            # Verify vector structure
            for vector in vectors:
                assert vector.payload is not None, "Vector missing payload"
                assert "document_id" in vector.payload, "Vector payload missing document_id"
                assert vector.payload["document_id"] == doc_id, (
                    "Vector has wrong document_id"
                )
                assert "chunk_text" in vector.payload, "Vector payload missing chunk_text"
                assert len(vector.payload["chunk_text"]) > 0, "Vector has empty chunk_text"

        except UnexpectedResponse as e:
            pytest.fail(f"Qdrant verification failed: {e}")

        # ===== STEP 5: Verify chunks retrievable via search =====
        # Search for content that should be in the document
        search_response = await api_client.post(
            "/api/v1/search",
            json={
                "query": "semantic search vector embeddings",
                "limit": 10,
                "mode": "hybrid",
            },
        )
        assert search_response.status_code == 200, (
            f"Search failed: {search_response.status_code}"
        )

        search_results = search_response.json()
        assert "results" in search_results, "Search response missing 'results' field"

        results = search_results["results"]
        assert len(results) > 0, "Search returned no results for uploaded document"

        # Verify at least one result belongs to our document
        our_doc_results = [
            r for r in results if r.get("document_id") == doc_id
        ]
        assert len(our_doc_results) > 0, (
            f"Uploaded document not found in search results. "
            f"Query returned {len(results)} results but none matched doc_id={doc_id}"
        )

        # Verify search result structure
        for result in our_doc_results:
            assert "score" in result, "Search result missing 'score' field"
            assert "text" in result, "Search result missing 'text' field"
            assert result["score"] > 0, f"Search result has invalid score: {result['score']}"
            assert len(result["text"]) > 0, "Search result has empty text"

    finally:
        # ===== CLEANUP: Delete document and verify removal =====
        if doc_id:
            # Delete document via API
            delete_response = await api_client.delete(f"/api/v1/documents/{doc_id}")
            assert delete_response.status_code == 204, (
                f"Delete failed: {delete_response.status_code}"
            )

            # Verify document no longer exists
            get_response = await api_client.get(f"/api/v1/documents/{doc_id}")
            assert get_response.status_code == 404, (
                "Document still exists after deletion"
            )

            # Verify vectors removed from Qdrant
            try:
                collection_name = os.getenv("QDRANT_COLLECTION", "documents")
                search_result = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter={
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"value": doc_id}
                            }
                        ]
                    },
                    limit=100,
                )

                remaining_vectors = search_result[0]
                assert len(remaining_vectors) == 0, (
                    f"Vectors not deleted from Qdrant: {len(remaining_vectors)} remaining"
                )
            except UnexpectedResponse:
                # Collection might not exist if this is the first test run
                pass


@pytest.mark.asyncio
async def test_document_upload_with_invalid_file(api_client: httpx.AsyncClient) -> None:
    """Test document upload validation with invalid file.

    Verifies that the API properly rejects invalid uploads:
    - Empty files
    - Files without names
    - Invalid file types (if validation implemented)

    Args:
        api_client: HTTP client for API service.
    """
    # Test 1: Empty file
    files = {"file": ("empty.txt", b"", "text/plain")}
    data = {"title": "Empty Document"}

    response = await api_client.post(
        "/api/v1/documents/upload", files=files, data=data
    )
    assert response.status_code == 400, (
        f"Expected 400 for empty file, got {response.status_code}"
    )

    # Test 2: No filename (this might be caught by FastAPI validation)
    files = {"file": ("", b"content", "text/plain")}
    data = {"title": "No Filename"}

    response = await api_client.post(
        "/api/v1/documents/upload", files=files, data=data
    )
    assert response.status_code in [400, 422], (
        f"Expected 400/422 for missing filename, got {response.status_code}"
    )


@pytest.mark.asyncio
async def test_document_upload_processing_status_transitions(
    api_client: httpx.AsyncClient,
) -> None:
    """Test that document status properly transitions during processing.

    Verifies:
    1. Initial status is 'processing' or 'completed' immediately after upload
    2. Status eventually transitions to 'completed'
    3. Embedding status transitions properly
    4. Status remains 'completed' after processing finishes

    Args:
        api_client: HTTP client for API service.
    """
    filename = "status_test.txt"
    content = b"Test document for status transition verification."
    doc_id = None

    try:
        # Upload document
        files = {"file": (filename, content, "text/plain")}
        data = {"title": "Status Transition Test"}

        response = await api_client.post(
            "/api/v1/documents/upload", files=files, data=data
        )
        assert response.status_code == 201, f"Upload failed: {response.status_code}"

        result = response.json()
        doc_id = result["document"]["id"]
        initial_status = result["document"]["upload_status"]

        # Status should be processing or completed (depending on speed)
        assert initial_status in ["processing", "completed"], (
            f"Unexpected initial status: {initial_status}"
        )

        # Poll for completion
        max_attempts = 30
        for _ in range(max_attempts):
            response = await api_client.get(f"/api/v1/documents/{doc_id}")
            assert response.status_code == 200

            document = response.json()
            status = document["upload_status"]
            embedding_status = document.get("embedding_status", "unknown")

            if status == "completed" and embedding_status == "completed":
                # Processing complete - verify status is stable
                await asyncio.sleep(1)

                # Check status again to ensure it's stable
                response = await api_client.get(f"/api/v1/documents/{doc_id}")
                document = response.json()
                assert document["upload_status"] == "completed"
                assert document.get("embedding_status") == "completed"
                break

            await asyncio.sleep(1)
        else:
            pytest.fail("Document processing did not complete within timeout")

    finally:
        # Cleanup
        if doc_id:
            await api_client.delete(f"/api/v1/documents/{doc_id}")
