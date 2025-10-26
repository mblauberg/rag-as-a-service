"""SQLAlchemy implementation of ChunkRepository port.

This adapter implements the domain repository interface using SQLAlchemy ORM.
It handles mapping between domain entities and database models.
"""
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.chunk import Chunk
from app.infrastructure.db.models import ChunkModel
from app.ports.repositories import ChunkRepository


class ChunkRepositoryImpl(ChunkRepository):
    """SQLAlchemy implementation of chunk repository.

    Maps between Chunk domain entities and ChunkModel ORM models.
    Note: Embedding vectors are NOT stored in PostgreSQL - they go to Qdrant.
    The database only stores chunk metadata and content.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def save_batch(self, chunks: list[Chunk]) -> list[Chunk]:
        """Persist multiple chunks atomically.

        Args:
            chunks: List of chunk entities

        Returns:
            Persisted chunks
        """
        # Convert chunks to models with proper chunk_index
        db_chunks = [self._to_model(chunk, idx) for idx, chunk in enumerate(chunks)]

        # Add all chunks to session
        self.session.add_all(db_chunks)

        # Commit transaction
        await self.session.commit()

        # Refresh all chunks to get any database-generated values
        for db_chunk in db_chunks:
            await self.session.refresh(db_chunk)

        # Convert back to domain entities
        return [self._to_entity(db_chunk) for db_chunk in db_chunks]

    async def find_by_document_id(self, document_id: UUID) -> list[Chunk]:
        """Retrieve all chunks for a document.

        Args:
            document_id: Document UUID

        Returns:
            List of chunks (may be empty)
        """
        stmt = select(ChunkModel).where(ChunkModel.document_id == document_id)
        result = await self.session.execute(stmt)
        db_chunks = result.scalars().all()

        return [self._to_entity(db_chunk) for db_chunk in db_chunks]

    async def delete_by_document_id(self, document_id: UUID) -> None:
        """Delete all chunks for a document.

        Args:
            document_id: Document UUID
        """
        stmt = delete(ChunkModel).where(ChunkModel.document_id == document_id)
        await self.session.execute(stmt)
        await self.session.commit()

    def _to_model(self, entity: Chunk, chunk_index: int = 0) -> ChunkModel:
        """Convert domain entity to ORM model.

        Note: Embedding vectors are intentionally NOT stored in the database.
        They are stored in Qdrant vector database instead.

        Args:
            entity: Chunk domain entity
            chunk_index: Position of chunk in document (0-indexed)

        Returns:
            ChunkModel ORM instance
        """
        return ChunkModel(
            id=entity.id,
            document_id=entity.document_id,
            chunk_text=entity.content,
            token_count=entity.tokens,
            chunk_index=chunk_index,
            chunk_metadata=entity.metadata,
            section_title=entity.section_title,
            section_level=entity.section_level,
            page_number=entity.page_number
            # embedding_vector is NOT stored in DB - goes to Qdrant
        )

    def _to_entity(self, model: ChunkModel) -> Chunk:
        """Convert ORM model to domain entity.

        Args:
            model: ChunkModel ORM instance

        Returns:
            Chunk domain entity
        """
        return Chunk(
            id=model.id,
            document_id=model.document_id,
            content=model.chunk_text,
            tokens=model.token_count or 0,
            metadata=model.chunk_metadata or {},  # Ensure not None
            section_title=model.section_title,
            section_level=model.section_level,
            page_number=model.page_number,
            embedding_vector=None,  # Not retrieved from DB
        )
