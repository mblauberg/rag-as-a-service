#!/usr/bin/env python3
"""
Re-embed existing documents in the database.

This script re-generates embeddings for all documents that have chunks
but missing or stale vector embeddings in Qdrant. Useful after:
- Qdrant data loss or corruption
- Upgrading embedding models
- Database migrations

Usage:
    python scripts/reembed_documents.py [--document-id UUID] [--force]

Options:
    --document-id UUID    Re-embed only a specific document
    --force              Re-embed even if embedding_status is 'completed'
    --dry-run            Show what would be re-embedded without doing it
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from uuid import UUID
import httpx

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import selectinload, sessionmaker

from app.models.document import Document, DocumentChunk
from app.core.config import settings


class DocumentReembedder:
    """Service to re-embed documents."""

    def __init__(self, embedder_url: str):
        """Initialize with embedder service URL."""
        self.embedder_url = embedder_url
        self.http_client = httpx.AsyncClient(timeout=300.0)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    async def reembed_document(
        self,
        db: AsyncSession,
        document: Document,
        chunks: list[DocumentChunk]
    ) -> bool:
        """
        Re-embed a single document.

        Args:
            db: Database session
            document: Document to re-embed
            chunks: Document chunks

        Returns:
            True if successful, False otherwise
        """
        if not chunks:
            print(f"  ⚠️  Document {document.id} has no chunks to embed")
            return False

        # Prepare chunks for embedder
        chunks_data = [
            {
                "id": str(chunk.id),
                "text": chunk.chunk_text,
                "metadata": {
                    "document_id": str(document.id),
                    "chunk_index": chunk.chunk_index
                }
            }
            for chunk in chunks
        ]

        try:
            # Send to embedder service
            response = await self.http_client.post(
                f"{self.embedder_url}/embed",
                json={"chunks": chunks_data}
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success", False):
                # Update document embedding status
                document.embedding_status = "completed"
                await db.commit()
                print(f"  ✅ Successfully re-embedded {len(chunks)} chunks")
                return True
            else:
                print(f"  ❌ Embedder returned success=false")
                document.embedding_status = "failed"
                await db.commit()
                return False

        except httpx.HTTPError as e:
            print(f"  ❌ HTTP error: {e}")
            document.embedding_status = "failed"
            await db.commit()
            return False
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            document.embedding_status = "failed"
            await db.commit()
            return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Re-embed documents in the RAAS database"
    )
    parser.add_argument(
        "--document-id",
        type=str,
        help="Re-embed only a specific document (UUID)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed even if embedding_status is 'completed'"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be re-embedded without doing it"
    )

    args = parser.parse_args()

    # Get configuration from environment or use defaults
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    embedder_url = os.getenv("EMBEDDER_URL", settings.embedder_url)

    print("🔄 RAAS Document Re-Embedding Script")
    print("=" * 50)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'configured'}")
    print(f"Embedder: {embedder_url}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 50)
    print()

    # Create async engine
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    reembedder = DocumentReembedder(embedder_url)

    try:
        async with async_session() as db:
            # Build query
            query = select(Document).options(
                selectinload(Document.chunks)
            )

            # Filter by document ID if specified
            if args.document_id:
                try:
                    doc_uuid = UUID(args.document_id)
                    query = query.where(Document.id == doc_uuid)
                    print(f"📄 Re-embedding specific document: {doc_uuid}\n")
                except ValueError:
                    print(f"❌ Invalid UUID: {args.document_id}")
                    return 1
            else:
                # Only re-embed documents that need it (unless --force)
                if not args.force:
                    query = query.where(
                        Document.embedding_status.in_(["pending", "failed"])
                    )
                    print("📋 Finding documents with pending/failed embeddings...\n")
                else:
                    print("📋 Finding all documents (--force mode)...\n")

            # Execute query
            result = await db.execute(query)
            documents = result.scalars().all()

            if not documents:
                print("✨ No documents found to re-embed")
                return 0

            print(f"Found {len(documents)} document(s) to re-embed:\n")

            # Process each document
            success_count = 0
            failed_count = 0

            for idx, document in enumerate(documents, 1):
                print(f"[{idx}/{len(documents)}] {document.title}")
                print(f"  ID: {document.id}")
                print(f"  Status: {document.embedding_status}")
                print(f"  Chunks: {len(document.chunks)}")

                if args.dry_run:
                    print(f"  🔍 Would re-embed {len(document.chunks)} chunks")
                    success_count += 1
                else:
                    success = await reembedder.reembed_document(
                        db, document, document.chunks
                    )
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1

                print()

            # Summary
            print("=" * 50)
            print("📊 Summary:")
            print(f"  Total: {len(documents)}")
            print(f"  ✅ Successful: {success_count}")
            if failed_count > 0:
                print(f"  ❌ Failed: {failed_count}")
            if args.dry_run:
                print("  (Dry run - no changes made)")
            print("=" * 50)

            return 0 if failed_count == 0 else 1

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await reembedder.close()
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
