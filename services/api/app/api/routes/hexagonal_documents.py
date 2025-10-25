"""Document management endpoints using hexagonal architecture.

These routes implement the HTTP adapter layer, translating between
HTTP requests/responses and domain use cases. They follow clean architecture
principles with dependency injection and proper error handling.
"""
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status

from app.api.dependencies import (
    get_upload_document_use_case,
    get_list_documents_use_case,
    get_delete_document_use_case
)
from app.api.models import (
    UploadDocumentResponse,
    DocumentResponse,
    ListDocumentsResponse,
    ErrorResponse
)
from app.application.use_cases.upload_document import (
    UploadDocumentUseCase,
    UploadDocumentCommand
)
from app.application.use_cases.list_documents import ListDocumentsUseCase
from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.core.exceptions import (
    DocumentNotFoundError,
    FileProcessingError,
    ChunkingError,
    EmbeddingServiceError,
    VectorStoreError
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="File to upload"),
    title: str = Form(..., description="Document title"),
    description: Optional[str] = Form(None, description="Optional document description"),
    use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case)
):
    """Upload a document file with hexagonal architecture.

    This endpoint orchestrates the complete document upload workflow:
    1. File validation
    2. Text extraction
    3. Semantic chunking
    4. Embedding generation
    5. Vector storage
    6. Metadata persistence

    Args:
        file: Uploaded file
        title: Document title
        description: Optional description
        use_case: Injected upload document use case

    Returns:
        Document details and chunk count

    Raises:
        HTTPException: On validation or processing failures
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read file: {str(e)}"
        )

    # Validate file size
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    # Create command
    command = UploadDocumentCommand(
        title=title,
        file_name=file.filename,
        file_content=content,
        description=description
    )

    # Execute use case
    try:
        document, chunk_count = await use_case.execute(command)

        logger.info(f"Document {document.id} uploaded successfully with {chunk_count} chunks")

        # Convert domain entity to response DTO
        return UploadDocumentResponse(
            document=DocumentResponse(
                id=document.id,
                title=document.title,
                file_name=document.file_name,
                file_type=document.file_type,
                created_at=document.created_at,
                upload_status=document.upload_status.value,
                description=document.description,
                file_path=document.file_path,
                file_size=document.file_size
            ),
            chunk_count=chunk_count,
            message="Document uploaded and processed successfully"
        )

    except FileProcessingError as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )
    except ChunkingError as e:
        logger.error(f"Chunking failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk document: {str(e)}"
        )
    except EmbeddingServiceError as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {str(e)}"
        )
    except VectorStoreError as e:
        logger.error(f"Vector store operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector database unavailable: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("", response_model=ListDocumentsResponse)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    use_case: ListDocumentsUseCase = Depends(get_list_documents_use_case)
):
    """Get paginated list of documents.

    Args:
        page: Page number (1-indexed)
        limit: Items per page (1-100)
        use_case: Injected list documents use case

    Returns:
        Paginated list of documents

    Raises:
        HTTPException: On validation errors
    """
    # Validation is done by use case, but we catch exceptions
    try:
        documents, total = await use_case.execute(page=page, limit=limit)

        # Convert domain entities to response DTOs
        document_responses = [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                file_name=doc.file_name,
                file_type=doc.file_type,
                created_at=doc.created_at,
                upload_status=doc.upload_status.value,
                description=doc.description,
                file_path=doc.file_path,
                file_size=doc.file_size
            )
            for doc in documents
        ]

        return ListDocumentsResponse(
            documents=document_responses,
            total=total,
            page=page,
            limit=limit
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    use_case: DeleteDocumentUseCase = Depends(get_delete_document_use_case)
):
    """Delete a document and all associated data.

    Removes:
    - Document metadata (PostgreSQL)
    - Chunks (PostgreSQL)
    - Vectors (Qdrant)

    Args:
        document_id: Document UUID
        use_case: Injected delete document use case

    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        await use_case.execute(document_id)
        logger.info(f"Document {document_id} deleted successfully")

    except DocumentNotFoundError as e:
        # DocumentNotFoundError is already an HTTPException with 404 status
        raise e
    except VectorStoreError as e:
        logger.error(f"Vector store deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to delete vectors: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
