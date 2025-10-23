"""Integration tests for document upload flow."""
import pytest
from io import BytesIO
from uuid import uuid4
from unittest.mock import AsyncMock, Mock
from sqlalchemy import select

from app.models.document import Document, DocumentChunk


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_success(async_client, db_session, mock_embedder_client):
    """
    Test successful document upload flow.

    Verifies:
    - Document is created in database
    - Chunks are created
    - File is processed
    - Embedder service is called
    """
    # Prepare test file
    file_content = b"This is a test document with some content for chunking."
    files = {
        "file": ("test.txt", BytesIO(file_content), "text/plain")
    }
    data = {
        "title": "Test Document",
        "description": "Test description"
    }

    # Make request
    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    # Verify response
    assert response.status_code == 201
    result = response.json()

    assert result["title"] == "Test Document"
    assert result["description"] == "Test description"
    assert result["file_name"] == "test.txt"
    assert result["file_type"] == "text/plain"
    assert result["file_size"] == len(file_content)
    assert result["upload_status"] == "completed"
    assert result["embedding_status"] == "pending"
    assert result["message"] == "Document uploaded and processed successfully"
    assert result["chunk_count"] > 0
    assert "id" in result

    # Verify document in database
    document_id = result["id"]
    query = select(Document).where(Document.id == document_id)
    db_result = await db_session.execute(query)
    document = db_result.scalar_one_or_none()

    assert document is not None
    assert document.title == "Test Document"
    assert document.upload_status == "completed"

    # Verify chunks in database
    chunk_query = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    chunk_result = await db_session.execute(chunk_query)
    chunks = chunk_result.scalars().all()

    assert len(chunks) == result["chunk_count"]
    assert all(chunk.document_id == uuid4(document_id) for chunk in chunks)

    # Verify embedder was called
    assert mock_embedder_client.post.called


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_no_file(async_client):
    """
    Test upload with no file provided.

    Should return 422 validation error.
    """
    data = {
        "title": "Test Document",
        "description": "Test description"
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        data=data
    )

    # FastAPI returns 422 for missing required fields
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_empty_file(async_client):
    """
    Test upload with empty file.

    Should return 400 error.
    """
    files = {
        "file": ("empty.txt", BytesIO(b""), "text/plain")
    }
    data = {
        "title": "Test Document",
        "description": "Test description"
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_missing_title(async_client):
    """
    Test upload without required title field.

    Should return 422 validation error.
    """
    files = {
        "file": ("test.txt", BytesIO(b"test content"), "text/plain")
    }
    data = {
        "description": "Test description"
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_with_pdf(async_client, db_session):
    """
    Test upload with PDF file.

    Verifies PDF file type is detected correctly.
    """
    # Minimal PDF header
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n/Resources <<\n/Font <<\n/F1 5 0 R\n>>\n>>\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\n5 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000274 00000 n\n0000000367 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n445\n%%EOF\n"

    files = {
        "file": ("test.pdf", BytesIO(pdf_content), "application/pdf")
    }
    data = {
        "title": "Test PDF Document",
        "description": "PDF test"
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    result = response.json()

    # Note: file_type detection may vary based on python-magic
    # It should detect as PDF-related type
    assert "pdf" in result["file_type"].lower() or result["file_type"] == "application/pdf"
    assert result["file_name"] == "test.pdf"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_with_optional_description(async_client, db_session):
    """
    Test upload without optional description field.

    Should succeed with description as null.
    """
    files = {
        "file": ("test.txt", BytesIO(b"test content"), "text/plain")
    }
    data = {
        "title": "Test Document"
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    result = response.json()

    assert result["title"] == "Test Document"
    assert result["description"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_embedder_failure(async_client, db_session, mock_embedder_client):
    """
    Test upload when embedder service fails.

    Document should still be created successfully (embedder is async background task).
    """
    # Configure mock to fail
    error_response = Mock()
    error_response.status_code = 500
    error_response.raise_for_status.side_effect = Exception("Embedder service error")

    async def mock_post_error(*args, **kwargs):
        return error_response

    mock_embedder_client.post = AsyncMock(side_effect=mock_post_error)

    files = {
        "file": ("test.txt", BytesIO(b"test content"), "text/plain")
    }
    data = {
        "title": "Test Document",
        "description": "Test description"
    }

    # Request should still succeed (embedder failure is logged, not raised)
    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    result = response.json()

    assert result["upload_status"] == "completed"
    assert result["embedding_status"] == "pending"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_multiple_documents(async_client, db_session):
    """
    Test uploading multiple documents in sequence.

    Verifies each upload creates separate database records.
    """
    documents = []

    for i in range(3):
        files = {
            "file": (f"test{i}.txt", BytesIO(f"Content {i}".encode()), "text/plain")
        }
        data = {
            "title": f"Document {i}",
            "description": f"Description {i}"
        }

        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data
        )

        assert response.status_code == 201
        documents.append(response.json())

    # Verify all documents are unique
    document_ids = [doc["id"] for doc in documents]
    assert len(document_ids) == len(set(document_ids))

    # Verify all exist in database
    for doc_id in document_ids:
        query = select(Document).where(Document.id == doc_id)
        result = await db_session.execute(query)
        doc = result.scalar_one_or_none()
        assert doc is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_document_chunks_created(async_client, db_session):
    """
    Test that uploaded document is properly chunked.

    Verifies chunks have correct attributes and ordering.
    """
    # Create longer content to ensure multiple chunks
    long_content = " ".join([f"Sentence {i} with some content." for i in range(100)])

    files = {
        "file": ("test.txt", BytesIO(long_content.encode()), "text/plain")
    }
    data = {
        "title": "Long Document",
        "description": "Multi-chunk test"
    }

    response = await async_client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    result = response.json()
    document_id = result["id"]

    # Verify chunks in database
    query = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunk_result = await db_session.execute(query)
    chunks = chunk_result.scalars().all()

    # Verify chunk properties
    assert len(chunks) == result["chunk_count"]

    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.chunk_text is not None
        assert len(chunk.chunk_text) > 0
        assert chunk.token_count is not None
        assert chunk.token_count > 0
        assert chunk.document_id == uuid4(document_id)
