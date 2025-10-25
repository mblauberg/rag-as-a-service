"""Standalone test runner for upload document use case - bypasses conftest."""
import sys
import os
import asyncio

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.application.use_cases.upload_document import (
    UploadDocumentUseCase,
    UploadDocumentCommand
)
from app.domain.entities.document import Document
from app.domain.entities.chunk import Chunk
from app.core.enums import UploadStatus
from app.ports.repositories import DocumentRepository, ChunkRepository
from app.ports.services import EmbeddingService, VectorStore, FileProcessor, TextChunker


async def test_upload_document_success():
    """Test successful document upload workflow."""
    print("Testing: test_upload_document_success")

    # Arrange: Create mocks for all dependencies
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_chunk_repo = Mock(spec=ChunkRepository)
    mock_embedding_service = Mock(spec=EmbeddingService)
    mock_vector_store = Mock(spec=VectorStore)
    mock_file_processor = Mock(spec=FileProcessor)
    mock_chunker = Mock(spec=TextChunker)

    # Configure mock behavior
    mock_doc_repo.save = AsyncMock(side_effect=lambda doc: doc)
    mock_chunk_repo.save_batch = AsyncMock(side_effect=lambda chunks: chunks)
    mock_file_processor.extract_text = AsyncMock(return_value="Sample document text content")
    mock_chunker.chunk = AsyncMock(return_value=["chunk 1 content", "chunk 2 content"])
    mock_embedding_service.generate_embeddings = AsyncMock(
        return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    )
    mock_vector_store.upsert = AsyncMock()

    # Create use case with mocked dependencies
    use_case = UploadDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=mock_chunk_repo,
        embedding_service=mock_embedding_service,
        vector_store=mock_vector_store,
        file_processor=mock_file_processor,
        chunker=mock_chunker
    )

    # Act: Execute use case
    command = UploadDocumentCommand(
        title="Test Document",
        file_name="test.pdf",
        file_content=b"PDF content bytes",
        description="Test description"
    )
    document, chunk_count = await use_case.execute(command)

    # Assert: Verify orchestration
    assert document.title == "Test Document", f"Expected title 'Test Document', got '{document.title}'"
    assert document.upload_status == UploadStatus.COMPLETED, f"Expected COMPLETED status, got {document.upload_status}"
    assert chunk_count == 2, f"Expected 2 chunks, got {chunk_count}"

    # Verify interactions
    assert mock_doc_repo.save.call_count == 2, f"Expected 2 save calls, got {mock_doc_repo.save.call_count}"
    assert mock_chunk_repo.save_batch.call_count == 1, f"Expected 1 save_batch call, got {mock_chunk_repo.save_batch.call_count}"
    assert mock_embedding_service.generate_embeddings.call_count == 1
    assert mock_vector_store.upsert.call_count == 1

    # Verify final save was with completed status
    final_save_call = mock_doc_repo.save.call_args_list[1]
    saved_doc = final_save_call[0][0]
    assert saved_doc.upload_status == UploadStatus.COMPLETED, "Final save should mark document as COMPLETED"

    print("✓ PASS: test_upload_document_success")


async def test_upload_document_failure_marks_failed():
    """Test that errors mark document as failed."""
    print("Testing: test_upload_document_failure_marks_failed")

    # Arrange
    mock_doc_repo = Mock(spec=DocumentRepository)
    mock_file_processor = Mock(spec=FileProcessor)

    mock_doc_repo.save = AsyncMock(side_effect=lambda doc: doc)
    mock_file_processor.extract_text = AsyncMock(side_effect=Exception("Processing failed"))

    use_case = UploadDocumentUseCase(
        document_repo=mock_doc_repo,
        chunk_repo=Mock(spec=ChunkRepository),
        embedding_service=Mock(spec=EmbeddingService),
        vector_store=Mock(spec=VectorStore),
        file_processor=mock_file_processor,
        chunker=Mock(spec=TextChunker)
    )

    # Act & Assert
    command = UploadDocumentCommand(
        title="Test",
        file_name="test.pdf",
        file_content=b"content"
    )

    try:
        await use_case.execute(command)
        raise AssertionError("Expected exception to be raised")
    except Exception as e:
        assert str(e) == "Processing failed", f"Expected 'Processing failed', got '{e}'"

    # Verify document was marked as failed
    assert mock_doc_repo.save.call_count == 2, f"Expected 2 saves, got {mock_doc_repo.save.call_count}"
    failed_call = mock_doc_repo.save.call_args_list[1]
    failed_doc = failed_call[0][0]
    assert failed_doc.upload_status == UploadStatus.FAILED, f"Expected FAILED status, got {failed_doc.upload_status}"

    print("✓ PASS: test_upload_document_failure_marks_failed")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running UploadDocumentUseCase Tests")
    print("="*60 + "\n")

    try:
        await test_upload_document_success()
        await test_upload_document_failure_marks_failed()
        print("\n" + "="*60)
        print("All tests PASSED ✓")
        print("="*60 + "\n")
        return 0
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
