"""SQLAlchemy models for documents and chunks."""
from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Document(Base):
    """Document metadata model."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(1000), nullable=True)
    document_type = Column(String(50), nullable=True)  # pdf, docx, txt, md, csv, etc.
    upload_status = Column(String(50), default="pending", nullable=False)
    embedding_status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to chunks
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """Document chunk model."""

    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    qdrant_point_id = Column(UUID(as_uuid=True), nullable=True)
    token_count = Column(Integer, nullable=True)

    # New metadata fields for semantic chunking
    section_title = Column(Text, nullable=True)
    section_level = Column(Integer, default=0)
    page_number = Column(Integer, nullable=True)
    chunk_tokens = Column(Integer, nullable=True)
    parent_chunk_id = Column(UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True)
    chunk_metadata = Column(JSONB().with_variant(JSON(), 'sqlite'), default={})

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to document
    document = relationship("Document", back_populates="chunks")
