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
