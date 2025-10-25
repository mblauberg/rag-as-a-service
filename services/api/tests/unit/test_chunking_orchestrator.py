"""Unit tests for ChunkingOrchestrator."""
import pytest
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.services.chunking_orchestrator import ChunkingOrchestrator
from app.services.document_metadata_service import DocumentMetadataService
from app.models.document import DocumentChunk
from app.models.schemas import DocumentType
from app.core.exceptions import TextExtractionError, EmbedderServiceError


@pytest.fixture
def mock_metadata_service():
    """Create mock DocumentMetadataService."""
    mock = AsyncMock(spec=DocumentMetadataService)
    return mock


@pytest.fixture
def chunking_orchestrator(mock_metadata_service):
    """Create ChunkingOrchestrator with mocked metadata service."""
    return ChunkingOrchestrator(metadata_service=mock_metadata_service)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_chunks_data():
    """Create sample chunks data for testing."""
    return [
        {
            "content": "This is chunk 1",
            "section_title": "Introduction",
            "section_level": 1,
            "page_number": 1,
            "tokens": 10,
            "metadata": {"source": "test"}
        },
        {
            "content": "This is chunk 2",
            "section_title": "Body",
            "section_level": 1,
            "page_number": 2,
            "tokens": 12,
            "metadata": {"source": "test"}
        }
    ]


@pytest.fixture
def sample_chunks():
    """Create sample DocumentChunk objects for testing."""
    doc_id = uuid4()
    return [
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            chunk_text="This is chunk 1",
            section_title="Introduction"
        ),
        DocumentChunk(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            chunk_text="This is chunk 2",
            section_title="Body"
        )
    ]


@pytest.mark.asyncio
class TestChunkingOrchestrator:
    """Test suite for ChunkingOrchestrator."""

    async def test_process_and_chunk_success(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service,
        sample_chunks_data
    ):
        """Test successful document processing and chunking."""
        document_id = uuid4()
        file_path = Path("/test/document.pdf")
        document_type = DocumentType.PDF

        # Mock processing service
        mock_chunks = [
            DocumentChunk(
                id=uuid4(),
                document_id=document_id,
                chunk_index=i,
                chunk_text=chunk["content"]
            )
            for i, chunk in enumerate(sample_chunks_data)
        ]

        with patch.object(
            chunking_orchestrator.processing_service,
            "process_and_chunk",
            return_value=sample_chunks_data
        ):
            mock_metadata_service.create_chunk_records.return_value = mock_chunks

            result = await chunking_orchestrator.process_and_chunk(
                db=mock_db,
                document_id=document_id,
                file_path=file_path,
                document_type=document_type
            )

            assert len(result) == 2
            mock_metadata_service.create_chunk_records.assert_called_once_with(
                mock_db,
                document_id,
                sample_chunks_data
            )

    async def test_process_and_chunk_text_extraction_error(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service
    ):
        """Test chunking with text extraction error."""
        document_id = uuid4()
        file_path = Path("/test/document.pdf")
        document_type = DocumentType.PDF

        # Mock processing service to raise error
        with patch.object(
            chunking_orchestrator.processing_service,
            "process_and_chunk",
            side_effect=TextExtractionError("extraction", "test.pdf", Exception("Failed"))
        ):
            with pytest.raises(TextExtractionError):
                await chunking_orchestrator.process_and_chunk(
                    db=mock_db,
                    document_id=document_id,
                    file_path=file_path,
                    document_type=document_type
                )

            # Should not create chunk records
            mock_metadata_service.create_chunk_records.assert_not_called()

    async def test_trigger_embedding_success(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service,
        sample_chunks
    ):
        """Test successful embedding trigger."""
        document_id = sample_chunks[0].document_id

        # Mock HTTP client response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.__aexit__.return_value = None

        with patch("app.services.chunking_orchestrator.httpx.AsyncClient", return_value=mock_http_client):
            await chunking_orchestrator.trigger_embedding(
                db=mock_db,
                document_id=document_id,
                chunks=sample_chunks
            )

            # Verify embedding status updated to completed via metadata service
            mock_metadata_service.update_embedding_status.assert_called_once_with(
                mock_db,
                document_id,
                "completed"
            )

    async def test_trigger_embedding_http_error(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service,
        sample_chunks
    ):
        """Test embedding trigger with HTTP error."""
        document_id = sample_chunks[0].document_id

        # Mock HTTP client to raise error
        mock_http_client = AsyncMock()
        mock_http_client.post.side_effect = httpx.HTTPError("Connection failed")
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.__aexit__.return_value = None

        with patch("app.services.chunking_orchestrator.httpx.AsyncClient", return_value=mock_http_client):
            # Should not raise error (background operation)
            await chunking_orchestrator.trigger_embedding(
                db=mock_db,
                document_id=document_id,
                chunks=sample_chunks
            )

            # Verify embedding status updated to failed via metadata service
            mock_metadata_service.update_embedding_status.assert_called_once_with(
                mock_db,
                document_id,
                "failed"
            )

    async def test_trigger_embedding_embedder_returns_false(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service,
        sample_chunks
    ):
        """Test embedding trigger when embedder returns success=false."""
        document_id = sample_chunks[0].document_id

        # Mock HTTP client response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": False}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.__aexit__.return_value = None

        with patch("app.services.chunking_orchestrator.httpx.AsyncClient", return_value=mock_http_client):
            await chunking_orchestrator.trigger_embedding(
                db=mock_db,
                document_id=document_id,
                chunks=sample_chunks
            )

            # Verify embedding status updated to failed via metadata service
            mock_metadata_service.update_embedding_status.assert_called_once_with(
                mock_db,
                document_id,
                "failed"
            )

    async def test_trigger_embedding_uses_metadata_service(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service,
        sample_chunks
    ):
        """Test that ChunkingOrchestrator uses DocumentMetadataService for status updates."""
        document_id = sample_chunks[0].document_id

        # Mock HTTP client response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.__aexit__.return_value = None

        with patch("app.services.chunking_orchestrator.httpx.AsyncClient", return_value=mock_http_client):
            await chunking_orchestrator.trigger_embedding(
                db=mock_db,
                document_id=document_id,
                chunks=sample_chunks
            )

            # Verify NO direct database operations were performed
            mock_db.execute.assert_not_called()
            mock_db.commit.assert_not_called()

            # Verify metadata service was used instead
            mock_metadata_service.update_embedding_status.assert_called_once()

    async def test_trigger_embedding_prepares_correct_payload(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service,
        sample_chunks
    ):
        """Test that embedding trigger prepares correct payload for embedder."""
        document_id = sample_chunks[0].document_id

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.__aexit__.return_value = None

        with patch("app.services.chunking_orchestrator.httpx.AsyncClient", return_value=mock_http_client):
            await chunking_orchestrator.trigger_embedding(
                db=mock_db,
                document_id=document_id,
                chunks=sample_chunks
            )

            # Verify correct payload was sent
            call_args = mock_http_client.post.call_args
            json_payload = call_args.kwargs["json"]

            assert "chunks" in json_payload
            assert len(json_payload["chunks"]) == 2
            assert json_payload["chunks"][0]["text"] == "This is chunk 1"
            assert json_payload["chunks"][0]["metadata"]["document_id"] == str(document_id)
            assert json_payload["chunks"][0]["metadata"]["chunk_index"] == 0

    async def test_trigger_embedding_unexpected_error(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service,
        sample_chunks
    ):
        """Test embedding trigger with unexpected error."""
        document_id = sample_chunks[0].document_id

        # Mock HTTP client to raise unexpected error
        mock_http_client = AsyncMock()
        mock_http_client.post.side_effect = Exception("Unexpected error")
        mock_http_client.__aenter__.return_value = mock_http_client
        mock_http_client.__aexit__.return_value = None

        with patch("app.services.chunking_orchestrator.httpx.AsyncClient", return_value=mock_http_client):
            # Should not raise error (background operation)
            await chunking_orchestrator.trigger_embedding(
                db=mock_db,
                document_id=document_id,
                chunks=sample_chunks
            )

            # Verify embedding status updated to failed via metadata service
            mock_metadata_service.update_embedding_status.assert_called_once_with(
                mock_db,
                document_id,
                "failed"
            )

    async def test_process_and_chunk_creates_correct_chunk_count(
        self,
        chunking_orchestrator,
        mock_db,
        mock_metadata_service
    ):
        """Test that correct number of chunks are created."""
        document_id = uuid4()
        file_path = Path("/test/document.pdf")
        document_type = DocumentType.PDF

        chunks_data = [{"content": f"Chunk {i}", "tokens": 10} for i in range(5)]

        mock_chunks = [
            DocumentChunk(
                id=uuid4(),
                document_id=document_id,
                chunk_index=i,
                chunk_text=chunk["content"]
            )
            for i, chunk in enumerate(chunks_data)
        ]

        with patch.object(
            chunking_orchestrator.processing_service,
            "process_and_chunk",
            return_value=chunks_data
        ):
            mock_metadata_service.create_chunk_records.return_value = mock_chunks

            result = await chunking_orchestrator.process_and_chunk(
                db=mock_db,
                document_id=document_id,
                file_path=file_path,
                document_type=document_type
            )

            assert len(result) == 5
            # Verify metadata service was called with correct data
            call_args = mock_metadata_service.create_chunk_records.call_args
            assert len(call_args[0][2]) == 5  # chunks_data parameter
