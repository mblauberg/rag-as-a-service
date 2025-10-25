"""Service for document file upload operations."""
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

import aiofiles

from app.core.config import settings
from app.core.exceptions import FileOperationError
from app.utils.file_processing import file_processor
from app.utils.file_type_detector import FileTypeDetector

logger = logging.getLogger(__name__)


class DocumentUploadService:
    """Service handling file I/O operations for document uploads."""

    def __init__(self):
        """Initialize document upload service."""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.file_detector = FileTypeDetector()

    async def save_file(
        self,
        file_content: bytes,
        filename: str
    ) -> dict[str, Any]:
        """
        Save uploaded file to disk and extract metadata.

        Args:
            file_content: File binary content
            filename: Original filename

        Returns:
            Dictionary containing file metadata:
            - file_id: UUID for the file
            - file_path: Path where file was saved
            - file_type: MIME type
            - file_size: Size in bytes
            - document_type: Document type enum value

        Raises:
            FileOperationError: If file save fails
            ValueError: If file type is unsupported
        """
        # Detect document type from filename
        try:
            document_type = self.file_detector.detect_from_filename(filename)
        except ValueError as e:
            logger.error(f"Unsupported file type for {filename}: {e}")
            raise FileOperationError("detect_file_type", filename, e)

        # Generate unique file path
        file_id = uuid4()
        file_extension = Path(filename).suffix
        file_path = self.upload_dir / f"{file_id}{file_extension}"

        # Save file to disk
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            logger.info(f"Saved file to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            raise FileOperationError("write", str(file_path), e)

        # Detect MIME type
        file_type = file_processor.detect_file_type(str(file_path))
        file_size = len(file_content)

        return {
            "file_id": file_id,
            "file_path": str(file_path),
            "file_type": file_type,
            "file_size": file_size,
            "document_type": document_type.value
        }

    async def delete_file(self, file_path: str) -> None:
        """
        Delete file from disk.

        Args:
            file_path: Path to file to delete

        Raises:
            FileOperationError: If file deletion fails
        """
        path = Path(file_path)
        try:
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
            else:
                logger.warning(f"File not found at stored path: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise FileOperationError("delete", str(file_path), e)

    def get_file_metadata(self, file_path: str) -> dict[str, Any]:
        """
        Get metadata for an existing file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file_type and file_size

        Raises:
            FileOperationError: If file doesn't exist or metadata extraction fails
        """
        path = Path(file_path)
        try:
            if not path.exists():
                raise FileOperationError(
                    "read",
                    file_path,
                    FileNotFoundError(f"File not found: {file_path}")
                )

            file_type = file_processor.detect_file_type(str(path))
            file_size = path.stat().st_size

            return {
                "file_type": file_type,
                "file_size": file_size
            }
        except FileOperationError:
            raise
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_path}: {e}")
            raise FileOperationError("read", file_path, e)
