"""Qdrant vector store implementation.

Implements the VectorStore port using Qdrant as the vector database.
Handles chunk vector storage and deletion operations.
Search is now delegated to the dedicated search microservice.
"""
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (FieldCondition, Filter, FilterSelector,
                                  MatchValue, PointStruct)

from app.core.exceptions import VectorStoreError
from app.domain.entities.chunk import Chunk
from app.ports.services import VectorStore


class QdrantVectorStoreImpl(VectorStore):
    """Qdrant implementation of VectorStore port.

    Uses Qdrant async client to store chunk embeddings for document upload.
    Stores chunk metadata as payload.
    Search operations are handled by the dedicated search microservice.
    """

    def __init__(self, client: AsyncQdrantClient, collection_name: str) -> None:
        """Initialize Qdrant vector store.

        Args:
            client: Async Qdrant client instance
            collection_name: Name of the Qdrant collection to use
        """
        self.client = client
        self.collection_name = collection_name

    async def upsert(self, chunks: list[Chunk]) -> None:
        """Insert or update chunk vectors in Qdrant.

        Args:
            chunks: List of chunks with embedding_vector populated

        Raises:
            VectorStoreError: If upsert operation fails or chunks missing embeddings
        """
        if not chunks:
            return

        # Validate all chunks have embeddings
        for chunk in chunks:
            if not chunk.has_embedding():
                raise VectorStoreError(
                    operation="upsert",
                    original_error=ValueError(
                        f"Chunk {chunk.id} is missing embedding vector"
                    ),
                )

        try:
            # Convert chunks to Qdrant points
            points = [
                PointStruct(
                    id=str(chunk.id),
                    vector=chunk.embedding_vector,  # type: ignore[arg-type]
                    payload={
                        "document_id": str(chunk.document_id),
                        "content": chunk.content,
                        "tokens": chunk.tokens,
                        "metadata": chunk.metadata,
                        "section_title": chunk.section_title,
                        "section_level": chunk.section_level,
                        "page_number": chunk.page_number,
                    },
                )
                for chunk in chunks
            ]

            # Upsert to Qdrant
            await self.client.upsert(
                collection_name=self.collection_name, points=points
            )

        except VectorStoreError:
            # Re-raise VectorStoreError as-is
            raise
        except Exception as e:
            raise VectorStoreError(operation="upsert", original_error=e) from e

    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete all vectors for a document.

        Args:
            document_id: Document UUID

        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            # Build filter for document_id
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id", match=MatchValue(value=str(document_id))
                    )
                ]
            )

            # Delete points matching filter
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(filter=query_filter),
            )

        except Exception as e:
            raise VectorStoreError(operation="delete", original_error=e) from e
