"""Unit tests for DocumentUploadService."""
import pytest
from pathlib import Path
from uuid import UUID
from unittest.mock import patch, MagicMock, AsyncMock
import aiofiles

from app.services.document_upload_service import DocumentUploadService
from app.core.exceptions import FileOperationError
from app.utils.file_type_detector import DocumentType


@pytest.fixture
def upload_service(tmp_path):
    """Create DocumentUploadService with temporary directory."""
    with patch("app.services.document_upload_service.settings") as mock_settings:
        mock_settings.upload_dir = str(tmp_path)
        service = DocumentUploadService()
        return service


@pytest.fixture
def sample_file_content():
    """Sample file content for testing."""
    return b"This is a test document content."


@pytest.mark.asyncio
class TestDocumentUploadService:
    """Test suite for DocumentUploadService."""

    async def test_save_file_success_pdf(self, upload_service, sample_file_content):
        """Test successful file save for PDF."""
        filename = "test_document.pdf"

        result = await upload_service.save_file(sample_file_content, filename)

        assert "file_id" in result
        assert isinstance(result["file_id"], UUID)
        assert result["file_path"].endswith(".pdf")
        assert result["file_size"] == len(sample_file_content)
        assert result["document_type"] == "pdf"
        assert Path(result["file_path"]).exists()

    async def test_save_file_success_txt(self, upload_service, sample_file_content):
        """Test successful file save for TXT."""
        filename = "test_document.txt"

        result = await upload_service.save_file(sample_file_content, filename)

        assert "file_id" in result
        assert isinstance(result["file_id"], UUID)
        assert result["file_path"].endswith(".txt")
        assert result["document_type"] == "txt"

    async def test_save_file_success_docx(self, upload_service, sample_file_content):
        """Test successful file save for DOCX."""
        filename = "test_document.docx"

        result = await upload_service.save_file(sample_file_content, filename)

        assert result["document_type"] == "docx"
        assert result["file_path"].endswith(".docx")

    async def test_save_file_unsupported_type(self, upload_service, sample_file_content):
        """Test file save with unsupported file type."""
        filename = "test_document.xyz"

        with pytest.raises(FileOperationError) as exc_info:
            await upload_service.save_file(sample_file_content, filename)

        assert "detect_file_type" in str(exc_info.value)

    async def test_save_file_write_error(self, upload_service, sample_file_content):
        """Test file save with write error."""
        filename = "test_document.pdf"

        # Mock aiofiles.open to raise an exception
        with patch("app.services.document_upload_service.aiofiles.open", side_effect=IOError("Write failed")):
            with pytest.raises(FileOperationError) as exc_info:
                await upload_service.save_file(sample_file_content, filename)

            assert "write" in str(exc_info.value)

    async def test_save_file_creates_directory(self, tmp_path):
        """Test that upload directory is created if it doesn't exist."""
        upload_dir = tmp_path / "new_uploads"
        with patch("app.services.document_upload_service.settings") as mock_settings:
            mock_settings.upload_dir = str(upload_dir)
            service = DocumentUploadService()

            assert upload_dir.exists()

    async def test_delete_file_success(self, upload_service, sample_file_content):
        """Test successful file deletion."""
        filename = "test_document.pdf"
        result = await upload_service.save_file(sample_file_content, filename)
        file_path = result["file_path"]

        # Verify file exists
        assert Path(file_path).exists()

        # Delete file
        await upload_service.delete_file(file_path)

        # Verify file is deleted
        assert not Path(file_path).exists()

    async def test_delete_file_not_found(self, upload_service):
        """Test deleting non-existent file (should not raise error)."""
        non_existent_path = "/path/to/non_existent_file.pdf"

        # Should complete without error (just logs warning)
        await upload_service.delete_file(non_existent_path)

    async def test_delete_file_error(self, upload_service, sample_file_content):
        """Test file deletion with permission error."""
        filename = "test_document.pdf"
        result = await upload_service.save_file(sample_file_content, filename)
        file_path = result["file_path"]

        # Mock unlink to raise permission error
        with patch.object(Path, "unlink", side_effect=PermissionError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                await upload_service.delete_file(file_path)

            assert "delete" in str(exc_info.value)

    async def test_get_file_metadata_success(self, upload_service, sample_file_content):
        """Test successful file metadata retrieval."""
        filename = "test_document.pdf"
        result = await upload_service.save_file(sample_file_content, filename)
        file_path = result["file_path"]

        metadata = upload_service.get_file_metadata(file_path)

        assert "file_type" in metadata
        assert "file_size" in metadata
        assert metadata["file_size"] == len(sample_file_content)

    def test_get_file_metadata_not_found(self, upload_service):
        """Test metadata retrieval for non-existent file."""
        non_existent_path = "/path/to/non_existent_file.pdf"

        with pytest.raises(FileOperationError) as exc_info:
            upload_service.get_file_metadata(non_existent_path)

        assert "read" in str(exc_info.value)

    async def test_save_file_preserves_extension(self, upload_service, sample_file_content):
        """Test that original file extension is preserved."""
        filename = "test_document.md"

        result = await upload_service.save_file(sample_file_content, filename)

        assert result["file_path"].endswith(".md")

    async def test_save_file_unique_ids(self, upload_service, sample_file_content):
        """Test that each saved file gets a unique ID."""
        filename = "test_document.pdf"

        result1 = await upload_service.save_file(sample_file_content, filename)
        result2 = await upload_service.save_file(sample_file_content, filename)

        assert result1["file_id"] != result2["file_id"]
        assert result1["file_path"] != result2["file_path"]

    async def test_save_file_all_supported_types(self, upload_service, sample_file_content):
        """Test saving files of all supported document types."""
        supported_extensions = ["pdf", "docx", "txt", "md", "csv"]

        for ext in supported_extensions:
            filename = f"test_document.{ext}"
            result = await upload_service.save_file(sample_file_content, filename)

            assert result["file_path"].endswith(f".{ext}")
            assert result["document_type"] == ext
            assert Path(result["file_path"]).exists()
