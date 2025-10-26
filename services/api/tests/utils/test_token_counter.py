import pytest

from app.utils.token_counter import TokenCounter


def test_count_tokens_simple_text():
    """Test token counting for simple text"""
    counter = TokenCounter()
    text = "This is a simple test sentence."
    count = counter.count_tokens(text)
    assert count > 0
    assert count < 20  # Should be around 7-8 tokens


def test_count_tokens_empty_string():
    """Test token counting for empty string"""
    counter = TokenCounter()
    assert counter.count_tokens("") == 0


def test_count_tokens_long_text():
    """Test token counting for longer text"""
    counter = TokenCounter()
    text = "Lorem ipsum " * 100  # Repeat to make longer
    count = counter.count_tokens(text)
    assert count > 100


def test_truncate_to_tokens_basic():
    """Test basic truncation functionality"""
    counter = TokenCounter()
    text = "This is a longer text that needs to be truncated to a smaller number of tokens."
    max_tokens = 5
    truncated = counter.truncate_to_tokens(text, max_tokens)

    # Verify the truncated text has at most max_tokens
    truncated_count = counter.count_tokens(truncated)
    assert truncated_count <= max_tokens

    # Verify text was actually truncated
    assert len(truncated) < len(text)


def test_truncate_no_truncation_needed():
    """Test when text is already short enough"""
    counter = TokenCounter()
    text = "Short text."
    original_count = counter.count_tokens(text)
    max_tokens = original_count + 10

    truncated = counter.truncate_to_tokens(text, max_tokens)

    # Verify text is unchanged when no truncation is needed
    assert truncated == text
    assert counter.count_tokens(truncated) == original_count


def test_truncate_exact_match():
    """Test when text is exactly max_tokens"""
    counter = TokenCounter()
    text = "This is a test sentence."
    original_count = counter.count_tokens(text)

    # Use exact token count as max_tokens
    truncated = counter.truncate_to_tokens(text, original_count)

    # Verify text is unchanged when exactly at max_tokens
    assert truncated == text
    assert counter.count_tokens(truncated) == original_count
