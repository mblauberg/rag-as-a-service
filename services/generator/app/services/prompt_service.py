"""Prompt engineering service for RAG synthesis."""
import logging
from typing import List
from app.models.schemas import ChunkInput

logger = logging.getLogger(__name__)


class PromptService:
    """Service for building and managing RAG prompts."""

    RAG_TEMPLATE = """You are a helpful assistant. Answer the user's question based ONLY on the provided context.
Cite sources using [1], [2], etc. to reference the document chunks.

Context:
{context}

Question: {query}

Answer with inline citations:"""

    def build_rag_prompt(self, query: str, chunks: List[ChunkInput]) -> str:
        """
        Build RAG prompt with citations.

        Args:
            query: User's search query
            chunks: Retrieved document chunks

        Returns:
            Formatted prompt string
        """
        # Format chunks with citation markers
        context_parts = []
        for idx, chunk in enumerate(chunks, start=1):
            context_parts.append(f"[{idx}] {chunk.text}")

        context = "\n".join(context_parts) if context_parts else "(No context provided)"

        prompt = self.RAG_TEMPLATE.format(
            context=context,
            query=query
        )

        logger.info(f"Built RAG prompt with {len(chunks)} chunks")
        return prompt

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Simple estimation: ~4 characters per token on average.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4
