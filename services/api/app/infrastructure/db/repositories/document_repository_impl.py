"""SQLAlchemy implementation of DocumentRepository port.

This adapter implements the domain repository interface using SQLAlchemy ORM.
It handles mapping between domain entities and database models.
"""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UploadStatus
from app.domain.entities.document import Document
from app.infrastructure.db.models import DocumentModel
from app.ports.repositories import DocumentRepository


class DocumentRepositoryImpl(DocumentRepository):
    """SQLAlchemy implementation of document repository.

    Maps between Document domain entities and DocumentModel ORM models.
    Handles enum serialization and UUID types.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def save(self, document: Document) -> Document:
        """Persist document to database.

        Handles both insert (new document) and update (existing document).

        Args:
            document: Document entity to persist

        Returns:
            Persisted document entity
        """
        # Check if document exists
        stmt = select(DocumentModel).where(DocumentModel.id == document.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing document
            existing.title = document.title
            existing.file_name = document.file_name
            existing.file_type = document.file_type
            existing.file_path = document.file_path
            existing.file_size = document.file_size
            existing.description = document.description
            existing.upload_status = document.upload_status.value  # Enum to string
            existing.created_at = document.created_at
        else:
            # Create new document
            db_document = self._to_model(document)
            self.session.add(db_document)

        await self.session.commit()

        # Refresh to get any database-generated values
        if existing:
            await self.session.refresh(existing)
            return self._to_entity(existing)
        else:
            # Need to fetch the newly created document
            stmt = select(DocumentModel).where(DocumentModel.id == document.id)
            result = await self.session.execute(stmt)
            saved = result.scalar_one()
            return self._to_entity(saved)

    async def find_by_id(self, document_id: UUID) -> Document | None:
        """Retrieve document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document entity if found, None otherwise
        """
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        db_document = result.scalar_one_or_none()

        if db_document is None:
            return None

        return self._to_entity(db_document)

    async def find_all(self, page: int, limit: int) -> tuple[list[Document], int]:
        """Retrieve paginated documents.

        Args:
            page: Page number (1-indexed)
            limit: Items per page

        Returns:
            Tuple of (documents list, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(DocumentModel)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated documents
        offset = (page - 1) * limit
        stmt = (
            select(DocumentModel)
            .offset(offset)
            .limit(limit)
            .order_by(DocumentModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_documents = result.scalars().all()

        documents = [self._to_entity(db_doc) for db_doc in db_documents]

        return documents, total

    async def delete(self, document_id: UUID) -> None:
        """Delete document from database.

        Args:
            document_id: Document UUID to delete
        """
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        db_document = result.scalar_one_or_none()

        if db_document:
            await self.session.delete(db_document)
            await self.session.commit()

    def _to_model(self, entity: Document) -> DocumentModel:
        """Convert domain entity to ORM model.

        Args:
            entity: Document domain entity

        Returns:
            DocumentModel ORM instance
        """
        return DocumentModel(
            id=entity.id,
            title=entity.title,
            file_name=entity.file_name,
            file_type=entity.file_type,
            file_path=entity.file_path,
            file_size=entity.file_size,
            description=entity.description,
            upload_status=entity.upload_status.value,  # Enum to string
            created_at=entity.created_at,
        )

    def _to_entity(self, model: DocumentModel) -> Document:
        """Convert ORM model to domain entity.

        Args:
            model: DocumentModel ORM instance

        Returns:
            Document domain entity
        """
        return Document(
            id=model.id,
            title=model.title,
            file_name=model.file_name,
            file_type=model.file_type,
            file_path=model.file_path,
            file_size=model.file_size,
            description=model.description,
            upload_status=UploadStatus(model.upload_status),  # String to enum
            created_at=model.created_at,
        )
