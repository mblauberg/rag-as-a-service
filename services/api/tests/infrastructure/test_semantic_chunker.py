"""Tests for SemanticChunker infrastructure adapter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.processing.semantic_chunker import SemanticChunkerImpl
from app.core.exceptions import ChunkingError
from app.services.chunking.semantic_chunker_v2 import ChunkResult


@pytest.fixture
def semantic_chunker():
    """Create SemanticChunker instance."""
    return SemanticChunkerImpl()


@pytest.fixture
def sample_text():
    """Sample text for chunking."""
    return """
    Machine learning is a subset of artificial intelligence. It focuses on the development
    of algorithms that can learn from data. Deep learning is a specialized form of machine
    learning. It uses neural networks with multiple layers. These networks can learn complex
    patterns in data. Natural language processing is another important field. It deals with
    the interaction between computers and human language.
    """.strip()


@pytest.fixture
def sample_chunk_results():
    """Sample chunk results from the underlying chunker."""
    return [
        ChunkResult(
            text="Machine learning is a subset of artificial intelligence.",
            start_index=0,
            end_index=56,
            token_count=10,
            coherence_score=0.95
        ),
        ChunkResult(
            text="It focuses on the development of algorithms that can learn from data.",
            start_index=57,
            end_index=126,
            token_count=12,
            coherence_score=0.92
        ),
        ChunkResult(
            text="Deep learning is a specialized form of machine learning. It uses neural networks with multiple layers.",
            start_index=127,
            end_index=230,
            token_count=18,
            coherence_score=0.88
        ),
    ]


class TestSemanticChunkerImpl:
    """Test suite for SemanticChunkerImpl."""

    @pytest.mark.asyncio
    async def test_chunk_text_success(self, semantic_chunker, sample_text, sample_chunk_results):
        """Test successful text chunking."""
        # Mock the underlying chunker
        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = sample_chunk_results

            result = await semantic_chunker.chunk(sample_text)

            assert len(result) == 3
            assert result[0] == "Machine learning is a subset of artificial intelligence."
            assert result[1] == "It focuses on the development of algorithms that can learn from data."
            assert result[2] == "Deep learning is a specialized form of machine learning. It uses neural networks with multiple layers."
            mock_chunk.assert_called_once_with(sample_text)

    @pytest.mark.asyncio
    async def test_chunk_empty_text(self, semantic_chunker):
        """Test chunking empty text."""
        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = []

            result = await semantic_chunker.chunk("")

            assert result == []
            mock_chunk.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_chunk_single_sentence(self, semantic_chunker):
        """Test chunking single sentence."""
        text = "This is a single sentence."
        chunk_result = ChunkResult(
            text=text,
            start_index=0,
            end_index=len(text),
            token_count=5,
            coherence_score=1.0
        )

        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = [chunk_result]

            result = await semantic_chunker.chunk(text)

            assert len(result) == 1
            assert result[0] == text

    @pytest.mark.asyncio
    async def test_chunk_with_special_characters(self, semantic_chunker):
        """Test chunking text with special characters."""
        text = "Hello 世界! This is a test with special chars: é, ñ, ü."
        chunk_result = ChunkResult(
            text=text,
            start_index=0,
            end_index=len(text),
            token_count=12,
            coherence_score=0.9
        )

        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = [chunk_result]

            result = await semantic_chunker.chunk(text)

            assert len(result) == 1
            assert result[0] == text

    @pytest.mark.asyncio
    async def test_chunk_long_text(self, semantic_chunker):
        """Test chunking longer text with multiple chunks."""
        text = "Lorem ipsum dolor sit amet. " * 100  # Long text
        chunks = [
            ChunkResult(
                text=text[:200],
                start_index=0,
                end_index=200,
                token_count=40,
                coherence_score=0.85
            ),
            ChunkResult(
                text=text[200:400],
                start_index=200,
                end_index=400,
                token_count=40,
                coherence_score=0.83
            ),
        ]

        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = chunks

            result = await semantic_chunker.chunk(text)

            assert len(result) == 2
            assert isinstance(result[0], str)
            assert isinstance(result[1], str)

    @pytest.mark.asyncio
    async def test_chunk_error_handling(self, semantic_chunker, sample_text):
        """Test that chunking errors are properly wrapped in ChunkingError."""
        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.side_effect = Exception("Underlying chunker failed")

            with pytest.raises(ChunkingError) as exc_info:
                await semantic_chunker.chunk(sample_text)

            assert "Chunking operation failed" in str(exc_info.value)
            assert "Underlying chunker failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chunk_whitespace_only(self, semantic_chunker):
        """Test chunking text with only whitespace."""
        text = "   \n\t\n   "

        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = []

            result = await semantic_chunker.chunk(text)

            assert result == []

    @pytest.mark.asyncio
    async def test_chunk_preserves_order(self, semantic_chunker):
        """Test that chunks are returned in correct order."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = [
            ChunkResult(text="First sentence.", start_index=0, end_index=15, token_count=2),
            ChunkResult(text="Second sentence.", start_index=16, end_index=32, token_count=2),
            ChunkResult(text="Third sentence.", start_index=33, end_index=48, token_count=2),
        ]

        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = chunks

            result = await semantic_chunker.chunk(text)

            assert result == ["First sentence.", "Second sentence.", "Third sentence."]

    @pytest.mark.asyncio
    async def test_chunk_with_newlines(self, semantic_chunker):
        """Test chunking text with newlines."""
        text = "First paragraph.\n\nSecond paragraph with more text.\n\nThird paragraph here."
        chunks = [
            ChunkResult(text="First paragraph.", start_index=0, end_index=16, token_count=2),
            ChunkResult(text="Second paragraph with more text.", start_index=18, end_index=50, token_count=5),
            ChunkResult(text="Third paragraph here.", start_index=52, end_index=73, token_count=3),
        ]

        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = chunks

            result = await semantic_chunker.chunk(text)

            assert len(result) == 3
            assert all(isinstance(chunk, str) for chunk in result)

    @pytest.mark.asyncio
    async def test_chunker_initialization(self, semantic_chunker):
        """Test that the chunker is properly initialized."""
        assert semantic_chunker.chunker is not None
        assert hasattr(semantic_chunker.chunker, 'chunk_text')

    @pytest.mark.asyncio
    async def test_chunk_extracts_text_from_chunk_results(self, semantic_chunker):
        """Test that only text is extracted from ChunkResult objects."""
        text = "Test text"
        chunk_result = ChunkResult(
            text="Extracted text",
            start_index=0,
            end_index=14,
            token_count=2,
            coherence_score=0.95
        )

        with patch.object(
            semantic_chunker.chunker,
            'chunk_text',
            new_callable=AsyncMock
        ) as mock_chunk:
            mock_chunk.return_value = [chunk_result]

            result = await semantic_chunker.chunk(text)

            # Should return only the text, not the full ChunkResult object
            assert result == ["Extracted text"]
            assert isinstance(result[0], str)
