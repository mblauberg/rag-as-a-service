"""Integration tests for hexagonal architecture HTTP routes.

These tests verify that the FastAPI HTTP layer correctly integrates
with the hexagonal architecture use cases via dependency injection.
"""
from datetime import UTC, datetime
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import UploadFile
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (get_delete_document_use_case,
                                  get_get_document_use_case,
                                  get_list_documents_use_case,
                                  get_search_documents_use_case,
                                  get_upload_document_use_case)
from app.core.enums import UploadStatus
from app.core.exceptions import DocumentNotFoundError
from app.domain.entities.chunk import Chunk
from app.domain.entities.document import Document
from app.main import app


@pytest.mark.asyncio
async def test_upload_document_success():
    """Test successful document upload via hexagonal route."""
    # Mock use case
    mock_use_case = AsyncMock()

    # Create mock document entity
    document_id = uuid4()
    mock_document = Document(
        id=document_id,
        title="Test Doc",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED,
        description="Test description",
        file_path="/path/to/test.pdf",
        file_size=1024,
    )

    mock_use_case.execute.return_value = (mock_document, 5)

    # Override dependency
    app.dependency_overrides[get_upload_document_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Create file upload
            files = {"file": ("test.pdf", b"test content", "application/pdf")}
            data = {"title": "Test Doc", "description": "Test description"}

            response = await client.post(
                "/api/v1/documents/upload", files=files, data=data
            )

        assert response.status_code == 201
        result = response.json()
        assert result["document"]["title"] == "Test Doc"
        assert result["chunk_count"] == 5
        assert result["message"] == "Document uploaded and processed successfully"

        # Verify use case was called
        mock_use_case.execute.assert_called_once()

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_document_empty_file():
    """Test upload with empty file returns 400."""
    mock_use_case = AsyncMock()
    app.dependency_overrides[get_upload_document_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            files = {"file": ("test.pdf", b"", "application/pdf")}
            data = {"title": "Test Doc"}

            response = await client.post(
                "/api/v1/documents/upload", files=files, data=data
            )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_documents_success():
    """Test successful document listing via hexagonal route."""
    mock_use_case = AsyncMock()

    # Create mock documents
    doc1 = Document(
        id=uuid4(),
        title="Doc 1",
        file_name="doc1.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED,
        file_size=1024,
    )
    doc2 = Document(
        id=uuid4(),
        title="Doc 2",
        file_name="doc2.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED,
        file_size=2048,
    )

    mock_use_case.execute.return_value = ([doc1, doc2], 2)

    app.dependency_overrides[get_list_documents_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/documents?page=1&limit=20")

        assert response.status_code == 200
        result = response.json()
        assert result["total"] == 2
        assert result["page"] == 1
        assert result["limit"] == 20
        assert len(result["documents"]) == 2
        assert result["documents"][0]["title"] == "Doc 1"

        mock_use_case.execute.assert_called_once_with(page=1, limit=20)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_documents_invalid_pagination():
    """Test list with invalid pagination returns 400."""
    mock_use_case = AsyncMock()
    mock_use_case.execute.side_effect = ValueError("Page must be >= 1")

    app.dependency_overrides[get_list_documents_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/documents?page=0&limit=20")

        assert response.status_code == 400
        assert "Page must be >= 1" in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_document_success():
    """Test successful document deletion via hexagonal route."""
    mock_use_case = AsyncMock()
    mock_use_case.execute.return_value = None

    app.dependency_overrides[get_delete_document_use_case] = lambda: mock_use_case

    document_id = uuid4()

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/documents/{document_id}")

        assert response.status_code == 204
        mock_use_case.execute.assert_called_once_with(document_id)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_document_not_found():
    """Test delete non-existent document returns 404."""
    mock_use_case = AsyncMock()
    document_id = uuid4()
    mock_use_case.execute.side_effect = DocumentNotFoundError(str(document_id))

    app.dependency_overrides[get_delete_document_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/documents/{document_id}")

        assert response.status_code == 404
        assert str(document_id) in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_documents_success():
    """Test successful search via hexagonal route."""
    mock_use_case = AsyncMock()

    # Create mock chunks
    chunk1 = Chunk(id=uuid4(), document_id=uuid4(), content="Test content 1", tokens=10)
    chunk2 = Chunk(id=uuid4(), document_id=uuid4(), content="Test content 2", tokens=12)

    mock_use_case.execute.return_value = [chunk1, chunk2]

    app.dependency_overrides[get_search_documents_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/search", json={"query": "test query", "top_k": 10}
            )

        assert response.status_code == 200
        result = response.json()
        assert result["query"] == "test query"
        assert result["total_results"] == 2
        assert len(result["results"]) == 2
        assert result["results"][0]["content"] == "Test content 1"

        mock_use_case.execute.assert_called_once()

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_documents_empty_query():
    """Test search with empty query returns 422 (Pydantic validation error)."""
    mock_use_case = AsyncMock()
    app.dependency_overrides[get_search_documents_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/search", json={"query": "", "top_k": 10}
            )

        # Pydantic validation returns 422 for empty string with min_length constraint
        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_document_by_id_success():
    """Test retrieving a single document with chunks via hexagonal route."""
    mock_use_case = AsyncMock()

    # Create mock document with chunks
    document_id = uuid4()
    chunk_id1 = uuid4()
    chunk_id2 = uuid4()

    mock_document = Document(
        id=document_id,
        title="Test Document",
        file_name="test.pdf",
        file_type="pdf",
        created_at=datetime.now(UTC),
        upload_status=UploadStatus.COMPLETED,
        description="Test description",
        file_path="/path/to/test.pdf",
        file_size=2048,
    )

    mock_chunks = [
        Chunk(
            id=chunk_id1,
            document_id=document_id,
            content="First chunk content",
            tokens=50,
        ),
        Chunk(
            id=chunk_id2,
            document_id=document_id,
            content="Second chunk content",
            tokens=60,
        ),
    ]

    mock_use_case.execute.return_value = (mock_document, mock_chunks)

    app.dependency_overrides[get_get_document_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/documents/{document_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(document_id)
        assert result["title"] == "Test Document"
        assert result["description"] == "Test description"
        assert len(result["chunks"]) == 2
        assert result["chunks"][0]["chunk_text"] == "First chunk content"
        assert result["chunks"][1]["chunk_text"] == "Second chunk content"

        mock_use_case.execute.assert_called_once_with(document_id)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_document_by_id_not_found():
    """Test retrieving non-existent document returns 404."""
    mock_use_case = AsyncMock()
    document_id = uuid4()
    mock_use_case.execute.side_effect = DocumentNotFoundError(str(document_id))

    app.dependency_overrides[get_get_document_use_case] = lambda: mock_use_case

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/documents/{document_id}")

        assert response.status_code == 404
        assert str(document_id) in response.json()["detail"]

    finally:
        app.dependency_overrides.clear()
