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
        """Search using PostgreSQL full-text search (BM25-like).

        Args:
            session: Database session
            query_text: Search query text
            top_k: Number of results
            document_id: Optional document filter

        Returns:
            List of chunks ranked by keyword relevance
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
