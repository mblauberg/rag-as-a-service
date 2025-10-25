"""Integration test for document upload in async context (reproduces event loop bug)."""
import pytest
import asyncio
from pathlib import Path
from app.services.document_processing_service import DocumentProcessingService
from app.models.schemas import DocumentType


@pytest.mark.asyncio
async def test_process_and_chunk_in_async_context():
    """
    Test that process_and_chunk works when called from an async context.

    This reproduces the production bug where FastAPI (async) calls the chunking
    orchestrator which tries to use run_until_complete() in an already-running loop.
    """
    # Create a test file
    test_content = """
    This is a test document for semantic chunking.

    It has multiple sentences to test the chunking logic.
    The semantic chunker should split this appropriately.

    This paragraph talks about something else entirely.
    It should potentially be in a different chunk.
    """

    test_file = Path("/tmp/test_async_upload.txt")
    test_file.write_text(test_content)

    try:
        # Initialize service
        service = DocumentProcessingService()

        # This should NOT raise "event loop already running" error
        # We're already in an async context (pytest-asyncio)
        chunks = await service.process_and_chunk(
            file_path=test_file,
            document_type=DocumentType.TXT
        )

        # Verify we got chunks
        assert len(chunks) > 0
        assert all('content' in chunk for chunk in chunks)
        assert all('tokens' in chunk for chunk in chunks)

    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


@pytest.mark.asyncio
async def test_semantic_chunker_v2_directly():
    """Test that SemanticChunkerV2 works correctly in async context."""
    from app.services.chunking.semantic_chunker_v2 import SemanticChunkerV2

    chunker = SemanticChunkerV2(
        min_chunk_size=128,
        max_chunk_size=512,
        breakpoint_percentile=95.0
    )

    test_text = """
    Machine learning is a subset of artificial intelligence.
    It focuses on teaching computers to learn from data.

    Deep learning uses neural networks with multiple layers.
    This allows for more complex pattern recognition.
    """

    # Should work without event loop errors
    chunks = await chunker.chunk_text(test_text)

    assert len(chunks) > 0
    assert all(chunk.token_count is not None for chunk in chunks)
