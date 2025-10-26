"""Document management endpoints using hexagonal architecture.

These routes implement the HTTP adapter layer, translating between
HTTP requests/responses and domain use cases. They follow clean architecture
principles with dependency injection and proper error handling.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import (
    get_delete_document_use_case,
    get_get_document_use_case,
    get_list_documents_use_case,
    get_upload_document_use_case,
)
from app.api.mappers import chunk_to_response, document_to_response
from app.api.models import (
    DocumentDetailResponse,
    ListDocumentsResponse,
    UploadDocumentResponse,
)
from app.application.use_cases.delete_document import DeleteDocumentUseCase
from app.application.use_cases.get_document import GetDocumentUseCase
from app.application.use_cases.list_documents import ListDocumentsUseCase
from app.application.use_cases.upload_document import UploadDocumentCommand, UploadDocumentUseCase
from app.core.exceptions import (
    ChunkingError,
    DocumentNotFoundError,
    EmbeddingServiceError,
    FileProcessingError,
    VectorStoreError,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="File to upload"),
    title: str = Form(..., description="Document title"),
    description: str | None = Form(None, description="Optional document description"),
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
        file_size=len(content),
        description=description
    )

    # Execute use case
    try:
        document, chunk_count = await use_case.execute(command)

        logger.info(f"Document {document.id} uploaded successfully with {chunk_count} chunks")

        # Convert domain entity to response DTO
        return UploadDocumentResponse(
            document=document_to_response(document),
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
        document_responses = [document_to_response(doc) for doc in documents]

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


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    use_case: GetDocumentUseCase = Depends(get_get_document_use_case)
):
    """Get a single document with all its chunks.

    Args:
        document_id: Document UUID
        use_case: Injected get document use case

    Returns:
        Document details with all chunks

    Raises:
        HTTPException: If document not found
    """
    try:
        document, chunks = await use_case.execute(document_id)

        # Convert to response DTO (enumerate to add chunk_index)
        chunk_responses = []
        for idx, chunk in enumerate(chunks):
            chunk_response = chunk_to_response(chunk)
            chunk_response.chunk_index = idx
            chunk_responses.append(chunk_response)

        return DocumentDetailResponse(
            id=document.id,
            title=document.title,
            file_name=document.file_name,
            file_type=document.file_type,
            file_size=document.file_size,
            file_path=document.file_path,
            upload_status=document.upload_status.value,
            embedding_status=document.embedding_status.value if hasattr(document, 'embedding_status') else "completed",
            created_at=document.created_at,
            updated_at=document.created_at,  # Use created_at as documents don't track updates
            description=document.description,
            chunks=chunk_responses
        )

    except DocumentNotFoundError as e:
        # DocumentNotFoundError is already an HTTPException with 404 status
        raise e
    except Exception as e:
        logger.error(f"Failed to get document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
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
