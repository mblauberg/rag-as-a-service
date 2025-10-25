"""SQLAlchemy ORM models (infrastructure concern).

These are NOT domain entities - they're database representations.
Repositories map between these and domain entities.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.infrastructure.db.base import Base


class DocumentModel(Base):
    """SQLAlchemy model for documents table."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(512), nullable=True)
    file_size = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    upload_status = Column(String(50), nullable=False)  # Store enum as string
    created_at = Column(DateTime, nullable=False)

    # Relationships
    chunks = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class ChunkModel(Base):
    """SQLAlchemy model for chunks table."""

    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=False)
    chunk_metadata = Column(JSON, nullable=False, default=dict)  # Use JSON for cross-DB compatibility
    section_title = Column(String(255), nullable=True)
    section_level = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)

    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")
