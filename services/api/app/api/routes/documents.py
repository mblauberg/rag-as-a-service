"""Document management endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_document_service
from app.models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentResponse
)

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="File to upload"),
    title: str = Form(..., description="Document title"),
    description: str = Form(None, description="Optional document description"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document file.

    Accepts multipart form data with a file and metadata.
    The file is saved, text is extracted, chunked, and queued for embedding.

    Args:
        file: Uploaded file
        title: Document title
        description: Optional description
        db: Database session
        document_service: Injected document service facade

    Returns:
        Document details and processing status

    Raises:
        HTTPException: If file processing fails
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

    # Create document service instance
    document_service = get_document_service()

    # Process document
    try:
        document, chunk_count = await document_service.create_document(
            db=db,
            file_content=content,
            filename=file.filename,
            title=title,
            description=description
        )

        return DocumentUploadResponse(
            **DocumentResponse.model_validate(document).model_dump(),
            message="Document uploaded and processed successfully",
            chunk_count=chunk_count
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of documents.

    Args:
        page: Page number (1-indexed)
        limit: Items per page
        db: Database session

    Returns:
        Paginated list of documents
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be >= 1"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )

    document_service = get_document_service()
    return await document_service.get_documents(db, page=page, limit=limit)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed document information including chunks.

    Args:
        document_id: Document UUID
        db: Database session

    Returns:
        Document details with chunks

    Raises:
        HTTPException: If document not found
    """
    document_service = get_document_service()
    document = await document_service.get_document_detail(db, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and all associated data.

    Removes document metadata, chunks, vectors from Qdrant, and file from disk.

    Args:
        document_id: Document UUID
        db: Database session

    Raises:
        DocumentNotFoundError: If document not found (raised by service)
        QdrantConnectionError: If vector deletion fails
        FileOperationError: If file deletion fails
    """
    document_service = get_document_service()
    # Service now raises DocumentNotFoundError instead of returning False
    await document_service.delete_document(db, document_id)
