"""
BM25-style lexical search using PostgreSQL full-text search.

Uses PostgreSQL's ts_rank for BM25-like relevance ranking.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentChunk


class BM25SearchService:
    """
    BM25-style keyword/lexical search using PostgreSQL FTS.

    Uses ts_rank for BM25-like relevance ranking with PostgreSQL's
    full-text search capabilities.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def search(
        self,
        query: str,
        limit: int = 20,
        document_ids: Optional[List[UUID]] = None
    ) -> List[DocumentChunk]:
        """
        Search chunks using BM25-like ranking.

        Args:
            query: Search query (natural language)
            limit: Maximum results to return
            document_ids: Optional filter by document IDs

        Returns:
            List of DocumentChunk objects ranked by relevance
        """
        # Check if we're using PostgreSQL or SQLite
        database_url = str(self.db_session.get_bind().url)
        is_postgres = "postgresql" in database_url

        if is_postgres:
            # Use PostgreSQL full-text search with ts_rank
            return await self._search_postgres(query, limit, document_ids)
        else:
            # Fallback to simple LIKE search for SQLite (testing)
            return await self._search_sqlite(query, limit, document_ids)

    async def _search_postgres(
        self,
        query: str,
        limit: int,
        document_ids: Optional[List[UUID]]
    ) -> List[DocumentChunk]:
        """
        PostgreSQL full-text search implementation.

        Uses text_search_vector column and ts_rank for ranking.
        """
        # Build SQL query with optional document filter
        sql = """
            SELECT
                id,
                document_id,
                chunk_index,
                chunk_text,
                token_count,
                ts_rank(text_search_vector, plainto_tsquery('english', :query)) as rank
            FROM document_chunks
            WHERE text_search_vector @@ plainto_tsquery('english', :query)
        """

        params = {"query": query, "limit": limit}

        if document_ids:
            # Convert UUIDs to strings for SQL query
            doc_ids_str = [str(doc_id) for doc_id in document_ids]
            sql += " AND document_id = ANY(:document_ids)"
            params["document_ids"] = doc_ids_str

        sql += " ORDER BY rank DESC LIMIT :limit"

        # Execute query

        result = await self.db_session.execute(text(sql), params)
        rows = result.fetchall()

        # Convert to DocumentChunk objects
        chunks = []
        for row in rows:
            chunk = DocumentChunk(
                id=row.id,
                document_id=row.document_id,
                chunk_index=row.chunk_index,
                chunk_text=row.chunk_text,
                token_count=row.token_count
            )
            # Store rank as metadata
            chunk.bm25_score = float(row.rank)
            chunks.append(chunk)

        return chunks

    async def _search_sqlite(
        self,
        query: str,
        limit: int,
        document_ids: Optional[List[UUID]]
    ) -> List[DocumentChunk]:
        """
        SQLite fallback implementation using LIKE for testing.

        This is a simple implementation for testing purposes.
        Production should use PostgreSQL with FTS.
        """
        # Split query into terms
        terms = query.lower().split()

        # Build query
        stmt = select(DocumentChunk)

        # Add LIKE conditions for each term (simple scoring)
        # In SQLite, we'll do client-side scoring
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

        stmt = stmt.limit(limit * 5)  # Get more results for filtering

        result = await self.db_session.execute(stmt)
        all_chunks = result.scalars().all()

        # Score chunks based on term matches
        scored_chunks = []
        for chunk in all_chunks:
            text_lower = chunk.chunk_text.lower()
            score = 0.0

            for term in terms:
                if term in text_lower:
                    # Simple scoring: count occurrences
                    score += text_lower.count(term)

            if score > 0:
                chunk.bm25_score = score
                scored_chunks.append(chunk)

        # Sort by score (descending) and limit
        scored_chunks.sort(key=lambda c: c.bm25_score, reverse=True)
        return scored_chunks[:limit]
