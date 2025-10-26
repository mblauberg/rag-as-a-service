"""Keyword search service using PostgreSQL Full-Text Search."""
import logging
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Chunk

logger = logging.getLogger(__name__)


class KeywordSearchService:
    """Service for keyword/lexical search using PostgreSQL FTS."""

    async def search(
        self,
        session: AsyncSession,
        query_text: str,
        top_k: int = 10,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search using PostgreSQL Full-Text Search with BM25-like ranking.

        Performs lexical search using PostgreSQL's built-in full-text search
        capabilities. Uses tsvector indexes for fast term matching and ts_rank
        for BM25-style relevance scoring.

        PostgreSQL FTS provides:
        - Stemming and stop-word removal (configurable language, default: english)
        - Term frequency scoring with document length normalization
        - Boolean operators (AND, OR, NOT) via tsquery syntax
        - Fast indexed search using GIN or GiST indexes

        Keyword search excels at:
        - Exact term matching (product codes, IDs, technical terms)
        - Named entity queries (person names, locations, organizations)
        - Queries with specific terminology not in embedding vocabulary

        Complements vector search in hybrid mode by capturing lexical signals
        that pure semantic search might miss.

        Args:
            session: Active AsyncSession for PostgreSQL database queries.
            query_text: Natural language query text. PostgreSQL tokenizes using
                plainto_tsquery, which handles stemming and stop-words.
            top_k: Number of top-ranked results to return. Defaults to 10.
            document_id: Optional UUID to filter results to single document.
                Applied as SQL WHERE condition.

        Returns:
            List of Chunk objects ranked by PostgreSQL ts_rank (descending).
            Each chunk includes:
            - score: ts_rank value (float, higher = more relevant)
            - content: Original chunk text with matched terms
            - document metadata: title, filename, chunk_index

        Note:
            The search_vector column must be populated via database trigger
            or application code. It's a tsvector representation of chunk
            content with stemming applied.

        Example:
            >>> service = KeywordSearchService()
            >>> results = await service.search(
            ...     session=db_session,
            ...     query_text="machine learning algorithms",
            ...     top_k=10
            ... )
            >>> print(f"Found {len(results)} matches")
            >>> print(f"Top rank: {results[0].score:.4f}")
        """
        # Build query with FTS ranking
        query = """
        SELECT
            c.id,
            c.document_id,
            c.content,
            c.tokens,
            c.chunk_index,
            d.title as document_title,
            d.file_name as document_filename,
            ts_rank(c.search_vector, plainto_tsquery('english', :query)) as rank
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.search_vector @@ plainto_tsquery('english', :query)
        """

        params = {"query": query_text, "limit": top_k}

        # Add document filter if provided
        if document_id:
            query += " AND c.document_id = :document_id"
            params["document_id"] = str(document_id)

        query += " ORDER BY rank DESC LIMIT :limit"

        # Execute search
        result = await session.execute(text(query), params)
        rows = result.all()

        # Convert to Chunk objects
        chunks = []
        for row in rows:
            chunk = Chunk(
                id=row.id,
                document_id=row.document_id,
                content=row.content,
                tokens=row.tokens,
                score=float(row.rank),  # FTS rank becomes score
                document_title=row.document_title,
                document_filename=row.document_filename,
                chunk_index=row.chunk_index
            )
            chunks.append(chunk)

        logger.info(f"Keyword search returned {len(chunks)} results")
        return chunks
