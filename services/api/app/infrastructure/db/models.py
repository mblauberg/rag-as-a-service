"""SQLAlchemy ORM models (infrastructure concern).

These are NOT domain entities - they're database representations.
Repositories map between these and domain entities.
"""
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


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
    embedding_status = Column(
        String(50), nullable=False, default="pending"
    )  # Add missing field
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )  # Add missing field with default

    # Relationships
    chunks = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ChunkModel(Base):
    """SQLAlchemy model for chunks table."""

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    qdrant_point_id = Column(UUID(as_uuid=True), nullable=True)
    token_count = Column(Integer, nullable=True)
    section_title = Column(String(255), nullable=True)
    section_level = Column(Integer, nullable=True, default=0)
    page_number = Column(Integer, nullable=True)
    chunk_tokens = Column(Integer, nullable=True)
    parent_chunk_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=True,
    )
    chunk_metadata = Column(
        JSON, nullable=False, default=dict
    )  # Use JSON for cross-DB compatibility
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
    )

    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")
