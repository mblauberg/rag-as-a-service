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
        """Build RAG prompt with citation-aware formatting.

        Creates a structured prompt that instructs the LLM to:
        1. Answer based ONLY on provided context (no hallucination)
        2. Cite sources using inline markers [1], [2], etc.
        3. Format response with clear attribution

        The prompt template includes:
        - System instruction for citation-based answering
        - Context section with numbered chunks
        - User's original query
        - Explicit instruction to use inline citations

        Citation format example:
        "RAG combines retrieval with generation [1]. It improves
        accuracy by grounding responses in documents [2]."

        This approach provides:
        - Answer attribution to specific source chunks
        - Fact verification capability for users
        - Transparency in information sourcing
        - Reduced hallucination (LLM constrained to context)

        Args:
            query: User's natural language query/question.
            chunks: Retrieved document chunks to use as context. Each chunk
                is formatted as "[N] chunk_text" where N is the citation number.

        Returns:
            Formatted prompt string ready for LLM API. Includes system
            instruction, numbered context chunks, and query.

        Example:
            >>> service = PromptService()
            >>> chunks = [
            ...     ChunkInput(text="RAG combines retrieval..."),
            ...     ChunkInput(text="Semantic search uses embeddings...")
            ... ]
            >>> prompt = service.build_rag_prompt("What is RAG?", chunks)
            >>> print(prompt)
            # Shows structured prompt with [1], [2] citation markers
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
        """Estimate token count using character-based heuristic.

        Provides rough token count estimation without loading a tokenizer.
        Uses the common heuristic that English text averages ~4 characters
        per token (including spaces and punctuation).

        This is useful for:
        - Quick context length checks before API calls
        - Cost estimation (tokens * price_per_token)
        - Chunk size validation

        Accuracy varies by language and text type:
        - English prose: ±15% accuracy
        - Code: Often over-estimates (symbols count as single tokens)
        - Non-English: Varies significantly (e.g., Chinese has more tokens)

        For precise token counts, use model-specific tokenizers:
        - tiktoken for OpenAI models (GPT)
        - transformers.AutoTokenizer for other models

        Args:
            text: Input text to estimate token count for.

        Returns:
            Estimated token count (integer). Calculated as len(text) // 4.

        Example:
            >>> service = PromptService()
            >>> text = "Hello world, this is a test."
            >>> tokens = service.estimate_tokens(text)
            >>> print(f"Estimated tokens: {tokens}")
            # Output: Estimated tokens: 7 (actual: ~6-8 depending on model)
        """
        return len(text) // 4
