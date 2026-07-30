"""Tests for LLM query augmenter."""
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import GenerationServiceError
from app.infrastructure.generation.llm_query_augmenter import LLMQueryAugmenterImpl


@pytest.fixture
def mock_generation_service():
    """Create mock GenerationService for testing."""
    service = AsyncMock()
    return service


@pytest.fixture
def augmenter(mock_generation_service):
    """Create LLMQueryAugmenterImpl instance with mock service."""
    return LLMQueryAugmenterImpl(mock_generation_service)


@pytest.mark.asyncio
async def test_expand_generates_variants(augmenter, mock_generation_service):
    """Test query expansion generates alternative phrasings."""
    mock_generation_service.generate.return_value = (
        "Kubernetes scaling methods\n" "How to increase pod replicas in K8s"
    )

    expanded = await augmenter.expand("How do I scale Kubernetes?", num_variants=2)

    # Should have original + 2 variants
    assert len(expanded) == 3
    assert expanded[0] == "How do I scale Kubernetes?"
    assert "Kubernetes scaling methods" in expanded[1]
    assert "K8s" in expanded[2]

    # Verify the generation service was called with correct prompt
    mock_generation_service.generate.assert_called_once()
    call_args = mock_generation_service.generate.call_args
    assert "How do I scale Kubernetes?" in call_args.kwargs["prompt"]
    assert call_args.kwargs["context"] == []


@pytest.mark.asyncio
async def test_expand_handles_numbered_variants(augmenter, mock_generation_service):
    """Test expansion handles numbered list format from LLM."""
    mock_generation_service.generate.return_value = (
        "1. Python programming language fundamentals\n"
        "2. Learning Python for beginners"
    )

    expanded = await augmenter.expand("Python basics", num_variants=2)

    # Should strip numbering
    assert len(expanded) == 3
    assert expanded[0] == "Python basics"
    assert "Python programming language fundamentals" in expanded[1]
    assert "Learning Python for beginners" in expanded[2]


@pytest.mark.asyncio
async def test_expand_handles_quoted_variants(augmenter, mock_generation_service):
    """Test expansion handles quoted variants."""
    mock_generation_service.generate.return_value = (
        '"Machine learning algorithms"\n' "'AI and ML techniques'"
    )

    expanded = await augmenter.expand("Machine learning", num_variants=2)

    # Should strip quotes
    assert len(expanded) == 3
    assert "Machine learning algorithms" in expanded[1]
    assert "AI and ML techniques" in expanded[2]


@pytest.mark.asyncio
async def test_expand_handles_markdown_formatting(augmenter, mock_generation_service):
    """Test expansion handles markdown formatting from LLM."""
    mock_generation_service.generate.return_value = (
        "**Docker container basics**\n" "*Containerization fundamentals*"
    )

    expanded = await augmenter.expand("Docker containers", num_variants=2)

    # Should strip markdown formatting
    assert len(expanded) == 3
    assert "Docker container basics" in expanded[1]
    assert "Containerization fundamentals" in expanded[2]


@pytest.mark.asyncio
async def test_expand_handles_empty_lines(augmenter, mock_generation_service):
    """Test expansion ignores empty lines in response."""
    mock_generation_service.generate.return_value = (
        "Container orchestration\n" "\n" "Managing containers at scale\n" "\n"
    )

    expanded = await augmenter.expand("Kubernetes", num_variants=2)

    # Should only include non-empty variants
    assert len(expanded) == 3
    assert expanded[0] == "Kubernetes"
    assert "Container orchestration" in expanded[1]
    assert "Managing containers at scale" in expanded[2]


@pytest.mark.asyncio
async def test_expand_limits_to_num_variants(augmenter, mock_generation_service):
    """Test expansion respects num_variants parameter."""
    mock_generation_service.generate.return_value = (
        "Variant 1\n" "Variant 2\n" "Variant 3\n" "Variant 4\n" "Variant 5"
    )

    expanded = await augmenter.expand("Original query", num_variants=2)

    # Should only return original + 2 variants (total 3)
    assert len(expanded) == 3
    assert expanded[0] == "Original query"
    assert expanded[1] == "Variant 1"
    assert expanded[2] == "Variant 2"


@pytest.mark.asyncio
async def test_expand_graceful_degradation_on_error(augmenter, mock_generation_service):
    """Test graceful degradation when expansion fails."""
    mock_generation_service.generate.side_effect = GenerationServiceError("LLM error")

    expanded = await augmenter.expand("test query")

    # Should return original query only
    assert len(expanded) == 1
    assert expanded[0] == "test query"


@pytest.mark.asyncio
async def test_expand_graceful_degradation_on_unexpected_error(
    augmenter, mock_generation_service
):
    """Test graceful degradation on unexpected errors."""
    mock_generation_service.generate.side_effect = Exception("Unexpected error")

    expanded = await augmenter.expand("test query")

    # Should return original query only
    assert len(expanded) == 1
    assert expanded[0] == "test query"


@pytest.mark.asyncio
async def test_expand_rejects_unsupported_method(augmenter, mock_generation_service):
    """Test that unsupported expansion methods raise ValueError."""
    with pytest.raises(ValueError) as exc_info:
        await augmenter.expand("test query", method="unsupported")

    assert "Unsupported expansion method" in str(exc_info.value)


@pytest.mark.asyncio
async def test_expand_builds_correct_prompt(augmenter, mock_generation_service):
    """Test that expansion builds correct prompt for LLM."""
    mock_generation_service.generate.return_value = "Variant 1\nVariant 2"

    await augmenter.expand("What is Python?", num_variants=3)

    # Verify prompt structure
    call_args = mock_generation_service.generate.call_args
    prompt = call_args.kwargs["prompt"]

    assert "Generate 3 alternative phrasings" in prompt
    assert "What is Python?" in prompt
    assert "semantically equivalent" in prompt
    assert "one per line" in prompt


@pytest.mark.asyncio
async def test_expand_with_single_variant(augmenter, mock_generation_service):
    """Test expansion with num_variants=1."""
    mock_generation_service.generate.return_value = "Single alternative phrasing"

    expanded = await augmenter.expand("Original", num_variants=1)

    # Should have original + 1 variant
    assert len(expanded) == 2
    assert expanded[0] == "Original"
    assert expanded[1] == "Single alternative phrasing"
