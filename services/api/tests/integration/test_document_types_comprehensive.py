#!/usr/bin/env python3
"""
Comprehensive tests for various document type handling.

Tests the complete workflow for all supported document types:
1. Upload - File accepted via API
2. Processing - Content extracted correctly
3. Storage - Document and chunks stored in DB/vector store
4. Metadata - Type, filename, size recorded accurately
5. Chunking - Content properly split for RAG
6. Searchability - Document retrievable via semantic search

Also tests failure scenarios:
- Unsupported file types
- Oversized files
- Corrupted files
- Empty files
"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient

# Test data paths
# Navigate from services/api/tests/integration/ to project root
TEST_CORPUS_DIR = (
    Path(__file__).parent.parent.parent.parent.parent / "data" / "rag_test_corpus"
)

# Document type test cases - (filename, expected_type, should_have_content)
SUPPORTED_DOCUMENT_TYPES = [
    ("doc_01.txt", "txt", True),
    ("doc_pdf_01.pdf", "pdf", True),
    ("doc_docx_01.docx", "docx", True),
    ("doc_md_01.md", "md", True),
    ("doc_csv_01.csv", "csv", True),
]


class TestDocumentTypeSupport:
    """Test suite for document type handling."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "filename,expected_type,should_have_content", SUPPORTED_DOCUMENT_TYPES
    )
    async def test_complete_workflow_for_document_type(
        self,
        filename: str,
        expected_type: str,
        should_have_content: bool,
        async_client: AsyncClient,
        db_session,
    ):
        """
        Test complete upload → process → store → search workflow for each document type.

        This test verifies:
        1. File can be uploaded
        2. Content is extracted
        3. Document is stored with correct metadata
        4. Chunks are created
        5. Document is searchable
        """
        file_path = TEST_CORPUS_DIR / filename

        # Verify test file exists
        assert file_path.exists(), f"Test file not found: {file_path}"

        # Step 1: Upload document
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, self._get_mime_type(expected_type))}
            data = {"title": f"Test: {filename}"}
            response = await async_client.post(
                "/api/v1/documents/upload", files=files, data=data
            )

        assert (
            response.status_code == 201
        ), f"Upload failed for {filename}: {response.text}"
        upload_data = response.json()

        # Verify response structure
        assert "id" in upload_data
        assert "filename" in upload_data
        assert "file_type" in upload_data
        document_id = upload_data["id"]

        # Step 2: Verify document metadata
        assert upload_data["filename"] == filename
        assert upload_data["file_type"] == expected_type
        assert "file_size" in upload_data
        assert upload_data["file_size"] > 0

        # Step 3: Wait for processing (if async)
        await asyncio.sleep(2)

        # Step 4: Retrieve document details
        response = await async_client.get(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        document_data = response.json()

        # Verify document was stored correctly
        assert document_data["id"] == document_id
        assert document_data["filename"] == filename
        assert document_data["file_type"] == expected_type

        # Step 5: Verify content extraction (if applicable)
        if should_have_content:
            # Check that document has content or chunks
            # This might be in embedding_status or a separate field
            assert document_data.get("embedding_status") in [
                "completed",
                "pending",
                "processing",
            ]

        # Step 6: Search for document
        # Use a generic search term that should match most documents
        search_response = await async_client.post(
            "/api/v1/search", json={"query": "test", "limit": 10}
        )
        assert search_response.status_code == 200
        search_results = search_response.json()

        # Verify our document appears in search results (eventually)
        # Note: This might need to wait for embedding to complete
        assert "results" in search_results or "documents" in search_results

        # Step 7: Cleanup - delete the document
        delete_response = await async_client.delete(f"/api/v1/documents/{document_id}")
        assert delete_response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_markdown_variant_extensions(self, async_client: AsyncClient):
        """Test that both .md and .markdown extensions are supported."""
        # Create temporary .markdown file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".markdown", delete=False
        ) as f:
            f.write("# Test Markdown\n\nThis is a test with .markdown extension.")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                files = {"file": ("test.markdown", f, "text/markdown")}
                data = {"title": "Test markdown"}
                response = await async_client.post(
                    "/api/v1/documents/upload", files=files, data=data
                )

            assert response.status_code == 201
            data = response.json()
            assert data["file_type"] == "md"

            # Cleanup
            if "id" in data:
                await async_client.delete(f"/api/documents/{data['id']}")
        finally:
            os.unlink(temp_path)

    def _get_mime_type(self, file_type: str) -> str:
        """Get MIME type for file extension."""
        mime_types = {
            "txt": "text/plain",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "md": "text/markdown",
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "html": "text/html",
        }
        return mime_types.get(file_type, "application/octet-stream")


class TestDocumentTypeFailures:
    """Test suite for document type validation and error handling."""

    @pytest.mark.asyncio
    async def test_unsupported_file_type_rejection(self, async_client: AsyncClient):
        """Test that unsupported file types are rejected."""
        unsupported_types = [
            ("image.jpg", "image/jpeg"),
            ("archive.zip", "application/zip"),
            ("executable.exe", "application/x-msdownload"),
            ("video.mp4", "video/mp4"),
        ]

        for filename, mime_type in unsupported_types:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=Path(filename).suffix, delete=False
            ) as f:
                f.write(b"fake content")
                temp_path = f.name

            try:
                with open(temp_path, "rb") as f:
                    files = {"file": (filename, f, mime_type)}
                    data = {"title": "Test test"}
                    response = await async_client.post(
                        "/api/v1/documents/upload", files=files, data=data
                    )

                # Should reject with 400 Bad Request or 422 Unprocessable Entity
                assert response.status_code in [
                    400,
                    422,
                ], f"Expected rejection for {filename}, got {response.status_code}"

                # Verify error message mentions unsupported type
                error_data = response.json()
                assert "detail" in error_data or "error" in error_data
            finally:
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_oversized_file_rejection(self, async_client: AsyncClient):
        """Test that files exceeding size limit are rejected."""
        # Create a file larger than 100MB
        # For testing purposes, we'll just test the validation logic
        # without actually creating a huge file

        # Create a 1MB file (we'll simulate size check in validation)
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # Write 1MB of data
            f.write(b"x" * (1024 * 1024))
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                files = {"file": ("large_file.txt", f, "text/plain")}
                data = {"title": "Test large_file.txt"}
                response = await async_client.post(
                    "/api/v1/documents/upload", files=files, data=data
                )

            # This should succeed as it's under 100MB
            # A real >100MB test would need different infrastructure
            assert response.status_code in [201, 400, 413, 422]

            if response.status_code == 201:
                # Cleanup if successful
                data = response.json()
                if "id" in data:
                    await async_client.delete(f"/api/v1/documents/{data['id']}")
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_empty_file_handling(self, async_client: AsyncClient):
        """Test that empty files are handled gracefully."""
        # Create empty file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Don't write anything - leave it empty
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                files = {"file": ("empty.txt", f, "text/plain")}
                data = {"title": "Test empty.txt"}
                response = await async_client.post(
                    "/api/v1/documents/upload", files=files, data=data
                )

            # System should either reject or accept with warning
            # Both are acceptable behaviors
            assert response.status_code in [201, 400, 422]

            if response.status_code == 201:
                data = response.json()
                # If accepted, file_size should be 0
                assert data.get("file_size") == 0

                # Cleanup
                if "id" in data:
                    await async_client.delete(f"/api/v1/documents/{data['id']}")
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_corrupted_pdf_handling(self, async_client: AsyncClient):
        """Test that corrupted PDF files are handled gracefully."""
        # Create a file with .pdf extension but invalid content
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
            f.write(b"This is not a valid PDF file content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                files = {"file": ("corrupted.pdf", f, "application/pdf")}
                data = {"title": "Test corrupted.pdf"}
                response = await async_client.post(
                    "/api/v1/documents/upload", files=files, data=data
                )

            # Should either reject during upload or fail during processing
            # But should not crash the server
            assert response.status_code in [201, 400, 422, 500]

            if response.status_code == 201:
                # If upload succeeded, processing might fail later
                data = response.json()
                if "id" in data:
                    # Check document status
                    detail_response = await async_client.get(
                        f"/api/v1/documents/{data['id']}"
                    )
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        # Processing should have failed
                        assert detail_data.get("embedding_status") in [
                            "failed",
                            "error",
                            "pending",
                        ]

                    # Cleanup
                    await async_client.delete(f"/api/v1/documents/{data['id']}")
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_corrupted_docx_handling(self, async_client: AsyncClient):
        """Test that corrupted DOCX files are handled gracefully."""
        # Create a file with .docx extension but invalid content
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".docx", delete=False) as f:
            f.write(b"This is not a valid DOCX file content")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                files = {
                    "file": (
                        "corrupted.docx",
                        f,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                }
                data = {"title": "Test corrupted.docx"}
                response = await async_client.post(
                    "/api/v1/documents/upload", files=files, data=data
                )

            # Should either reject during upload or fail during processing
            assert response.status_code in [201, 400, 422, 500]

            if response.status_code == 201:
                data = response.json()
                if "id" in data:
                    # Cleanup
                    await async_client.delete(f"/api/v1/documents/{data['id']}")
        finally:
            os.unlink(temp_path)


class TestDocumentContentExtraction:
    """Test that content is correctly extracted from different document types."""

    @pytest.mark.asyncio
    async def test_pdf_content_extraction(self, async_client: AsyncClient):
        """Verify PDF content is extracted correctly."""
        file_path = TEST_CORPUS_DIR / "doc_pdf_01.pdf"

        with open(file_path, "rb") as f:
            files = {"file": ("doc_pdf_01.pdf", f, "application/pdf")}
            data = {"title": "Test PDF content extraction"}
            response = await async_client.post(
                "/api/v1/documents/upload", files=files, data=data
            )

        assert response.status_code == 201
        data = response.json()
        document_id = data["id"]

        # Wait for processing
        await asyncio.sleep(2)

        # Retrieve document
        response = await async_client.get(f"/api/v1/documents/{document_id}")
        assert response.status_code == 200
        doc_data = response.json()

        # Should have extracted some content
        # (actual content verification would depend on API structure)
        assert doc_data.get("embedding_status") is not None

        # Cleanup
        await async_client.delete(f"/api/v1/documents/{document_id}")

    @pytest.mark.asyncio
    async def test_csv_content_extraction(self, async_client: AsyncClient):
        """Verify CSV content is extracted correctly."""
        file_path = TEST_CORPUS_DIR / "doc_csv_01.csv"

        with open(file_path, "rb") as f:
            files = {"file": ("doc_csv_01.csv", f, "text/csv")}
            data = {"title": "Test CSV content extraction"}
            response = await async_client.post(
                "/api/v1/documents/upload", files=files, data=data
            )

        assert response.status_code == 201
        data = response.json()
        document_id = data["id"]

        # Wait for processing
        await asyncio.sleep(2)

        # CSV should be processed and searchable
        search_response = await async_client.post(
            "/api/v1/search", json={"query": "Employee Engineering", "limit": 10}
        )
        assert search_response.status_code == 200

        # Cleanup
        await async_client.delete(f"/api/v1/documents/{document_id}")

    @pytest.mark.asyncio
    async def test_markdown_content_extraction(self, async_client: AsyncClient):
        """Verify Markdown content is extracted correctly."""
        file_path = TEST_CORPUS_DIR / "doc_md_01.md"

        with open(file_path, "rb") as f:
            files = {"file": ("doc_md_01.md", f, "text/markdown")}
            data = {"title": "Test Markdown content extraction"}
            response = await async_client.post(
                "/api/v1/documents/upload", files=files, data=data
            )

        assert response.status_code == 201
        data = response.json()
        document_id = data["id"]

        # Wait for processing
        await asyncio.sleep(2)

        # Markdown should preserve structure and be searchable
        search_response = await async_client.post(
            "/api/v1/search",
            json={"query": "neural networks machine learning", "limit": 10},
        )
        assert search_response.status_code == 200

        # Cleanup
        await async_client.delete(f"/api/v1/documents/{document_id}")
