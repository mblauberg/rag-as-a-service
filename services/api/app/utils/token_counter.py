import tiktoken


class TokenCounter:
    """Utility for counting tokens in text using tiktoken"""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize token counter with specified encoding.

        Args:
            encoding_name: Tiktoken encoding name (default: cl100k_base for GPT-4)
        """
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to maximum token count.

        Args:
            text: Input text
            max_tokens: Maximum number of tokens

        Returns:
            Truncated text
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.encoding.decode(tokens[:max_tokens])
