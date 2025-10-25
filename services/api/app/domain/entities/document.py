"""Document domain entity."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.enums import UploadStatus


@dataclass
class Document:
    """Core document entity representing an uploaded document.

    Enforces business rules around document lifecycle transitions.
    Domain entity has no infrastructure dependencies.
    """

    id: UUID
    title: str
    file_name: str
    file_type: str
    created_at: datetime
    upload_status: UploadStatus
    description: str | None = None
    file_path: str | None = None
    file_size: int | None = None

    def mark_completed(self) -> None:
        """Transition document to completed state.

        Should be called after successful processing, chunking, and embedding.
        """
        self.upload_status = UploadStatus.COMPLETED

    def mark_failed(self) -> None:
        """Transition document to failed state.

        Called when processing, chunking, or embedding fails.
        """
        self.upload_status = UploadStatus.FAILED

    def is_processing(self) -> bool:
        """Check if document is currently being processed."""
        return self.upload_status == UploadStatus.PROCESSING

    def is_completed(self) -> bool:
        """Check if document processing is complete."""
        return self.upload_status == UploadStatus.COMPLETED
