"""Qdrant vector store implementation.

Implements the VectorStore port using Qdrant as the vector database.
Handles chunk vector storage, similarity search, and deletion operations.
"""
from typing import List, Optional
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector
)

from app.ports.services import VectorStore
from app.domain.entities.chunk import Chunk
from app.core.exceptions import VectorStoreError


class QdrantVectorStoreImpl(VectorStore):
    """Qdrant implementation of VectorStore port.

    Uses Qdrant async client to store and retrieve chunk embeddings.
    Stores chunk metadata as payload for filtering and reconstruction.
    """

    def __init__(self, client: AsyncQdrantClient, collection_name: str) -> None:
        """Initialize Qdrant vector store.

        Args:
            client: Async Qdrant client instance
            collection_name: Name of the Qdrant collection to use
        """
        self.client = client
        self.collection_name = collection_name

    async def upsert(self, chunks: List[Chunk]) -> None:
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
                    )
                )

        try:
            # Convert chunks to Qdrant points
            points = [
                PointStruct(
                    id=str(chunk.id),
                    vector=chunk.embedding_vector,
                    payload={
                        "document_id": str(chunk.document_id),
                        "content": chunk.content,
                        "tokens": chunk.tokens,
                        "metadata": chunk.metadata,
                        "section_title": chunk.section_title,
                        "section_level": chunk.section_level,
                        "page_number": chunk.page_number
                    }
                )
                for chunk in chunks
            ]

            # Upsert to Qdrant
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

        except VectorStoreError:
            # Re-raise VectorStoreError as-is
            raise
        except Exception as e:
            raise VectorStoreError(
                operation="upsert",
                original_error=e
            ) from e

    async def search(
        self,
        query_vector: List[float],
        top_k: int,
        document_id: Optional[UUID] = None
    ) -> List[Chunk]:
        """Search for similar vectors in Qdrant.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            document_id: Optional filter by document

        Returns:
            List of most similar chunks (ordered by similarity)

        Raises:
            VectorStoreError: If search operation fails
        """
        try:
            # Build filter if document_id provided
            query_filter = None
            if document_id is not None:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id))
                        )
                    ]
                )

            # Search Qdrant
            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter
            )

            # Convert results to Chunk entities
            chunks = []
            for scored_point in results:
                payload = scored_point.payload

                chunk = Chunk(
                    id=UUID(scored_point.id),
                    document_id=UUID(payload["document_id"]),
                    content=payload["content"],
                    tokens=payload["tokens"],
                    metadata=payload.get("metadata", {}),
                    section_title=payload.get("section_title"),
                    section_level=payload.get("section_level"),
                    page_number=payload.get("page_number"),
                    # Note: We don't retrieve embedding_vector from search results
                    # to save bandwidth - it can be regenerated if needed
                    embedding_vector=None
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            raise VectorStoreError(
                operation="search",
                original_error=e
            ) from e

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
                        key="document_id",
                        match=MatchValue(value=str(document_id))
                    )
                ]
            )

            # Delete points matching filter
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(filter=query_filter)
            )

        except Exception as e:
            raise VectorStoreError(
                operation="delete",
                original_error=e
            ) from e
