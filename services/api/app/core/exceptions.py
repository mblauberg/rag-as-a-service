"""Custom exception classes for the API service."""
from fastapi import HTTPException, status


class DocumentNotFoundError(HTTPException):
    """
    Exception raised when a document is not found.

    This exception is raised when attempting to retrieve, update, or delete
    a document that doesn't exist in the database.
    """

    def __init__(self, document_id: str, detail: str = None):
        """
        Initialize DocumentNotFoundError.

        Args:
            document_id: The UUID of the document that was not found
            detail: Optional custom error message
        """
        if detail is None:
            detail = f"Document {document_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class QdrantConnectionError(Exception):
    """
    Exception raised when Qdrant operations fail.

    This exception is raised when vector database operations fail,
    such as search, upsert, or delete operations.
    """

    def __init__(self, operation: str, original_error: Exception = None):
        """
        Initialize QdrantConnectionError.

        Args:
            operation: Description of the operation that failed
            original_error: The original exception that was caught
        """
        message = f"Qdrant operation failed: {operation}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)
        self.operation = operation
        self.original_error = original_error


class EmbedderServiceError(Exception):
    """
    Exception raised when embedder service communication fails.

    This exception is raised when the embedder service is unreachable
    or returns an error response.
    """

    def __init__(self, operation: str, original_error: Exception = None):
        """
        Initialize EmbedderServiceError.

        Args:
            operation: Description of the operation that failed
            original_error: The original exception that was caught
        """
        message = f"Embedder service operation failed: {operation}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)
        self.operation = operation
        self.original_error = original_error


class FileOperationError(Exception):
    """
    Exception raised when file system operations fail.

    This exception is raised when file operations such as reading,
    writing, or deleting fail.
    """

    def __init__(self, operation: str, file_path: str, original_error: Exception = None):
        """
        Initialize FileOperationError.

        Args:
            operation: Description of the operation that failed (e.g., "read", "write", "delete")
            file_path: Path to the file that caused the error
            original_error: The original exception that was caught
        """
        message = f"File operation '{operation}' failed for {file_path}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)
        self.operation = operation
        self.file_path = file_path
        self.original_error = original_error


class TextExtractionError(Exception):
    """
    Exception raised when text extraction from documents fails.

    This exception is raised when the file processor cannot extract
    text from a document file.
    """

    def __init__(self, file_path: str, file_type: str, original_error: Exception = None):
        """
        Initialize TextExtractionError.

        Args:
            file_path: Path to the file that caused the error
            file_type: Type of the file (e.g., "pdf", "docx")
            original_error: The original exception that was caught
        """
        message = f"Failed to extract text from {file_type} file: {file_path}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message)
        self.file_path = file_path
        self.file_type = file_type
        self.original_error = original_error
