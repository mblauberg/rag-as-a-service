import pytest
from app.services.document_processing_service import DocumentProcessingService
from app.core.config import settings


def test_document_processing_service_uses_semantic_chunking():
    """Test that document processing service uses semantic chunking when configured"""
    # Set semantic chunking strategy
    original_strategy = settings.CHUNKING_STRATEGY
    settings.CHUNKING_STRATEGY = "semantic"

    try:
        processing_service = DocumentProcessingService()

        # Sample document with clear semantic boundaries
        text = """
        Docker containers provide isolation. They package applications with dependencies.
        Containers are lightweight and portable across environments.

        Kubernetes orchestrates containers. It handles deployment, scaling, and management.
        Kubernetes provides self-healing and load balancing capabilities.
        """

        # Use chunker directly to test semantic chunking
        chunks = processing_service.chunker.chunk_with_metadata(text)

        # Should create multiple semantic chunks
        assert len(chunks) > 0

        # Verify chunks have expected structure
        for chunk in chunks:
            assert "content" in chunk
            assert "tokens" in chunk
            assert len(chunk["content"].split()) >= 10  # Reasonable min size

        # Verify semantic chunking is being used (not the legacy recursive chunker)
        # Semantic chunker should be SemanticChunkerV2
        assert processing_service.chunker.__class__.__name__ == "SemanticChunkerV2Wrapper", \
            f"Expected SemanticChunkerV2Wrapper but got {processing_service.chunker.__class__.__name__}"
    finally:
        # Restore original strategy
        settings.CHUNKING_STRATEGY = original_strategy
