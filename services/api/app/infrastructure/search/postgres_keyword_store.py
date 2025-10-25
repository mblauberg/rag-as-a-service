"""PostgreSQL full-text search implementation using BM25-like ranking."""
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SearchError
from app.domain.entities.chunk import Chunk
from app.ports.services import KeywordStore


class PostgresKeywordStoreImpl(KeywordStore):
    """BM25-style keyword search using PostgreSQL FTS.

    Uses ts_rank for BM25-like relevance ranking with
    PostgreSQL's full-text search capabilities.
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        self.db_session = db_session

    async def search(
        self,
        query_text: str,
        top_k: int,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search using PostgreSQL full-text search.

        Uses text_search_vector column and ts_rank for BM25-like ranking.
        """
        try:
            # Build SQL with optional document filter
            sql = """
                SELECT
                    id, document_id, chunk_text, token_count,
                    chunk_metadata, section_title,
                    section_level, page_number,
                    ts_rank(
                        text_search_vector,
                        plainto_tsquery('english', :query)
                    ) as rank
                FROM document_chunks
                WHERE text_search_vector @@ plainto_tsquery('english', :query)
            """

            params = {"query": query_text, "limit": top_k}

            if document_id:
                sql += " AND document_id = :document_id"
                params["document_id"] = str(document_id)

            sql += " ORDER BY rank DESC LIMIT :limit"

            # Execute query
            result = await self.db_session.execute(text(sql), params)
            rows = result.fetchall()

            # Convert to Chunk entities
            chunks = []
            for row in rows:
                chunk = Chunk(
                    id=row.id,
                    document_id=row.document_id,
                    content=row.chunk_text,
                    tokens=row.token_count,
                    metadata=row.chunk_metadata or {},
                    section_title=row.section_title,
                    section_level=row.section_level,
                    page_number=row.page_number
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            raise SearchError(
                operation="keyword_search",
                original_error=e
            ) from e
