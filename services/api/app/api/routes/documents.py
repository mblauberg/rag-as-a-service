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
from app.api.models import DocumentDetailResponse, ListDocumentsResponse, UploadDocumentResponse
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


@router.post(
    "/upload",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for semantic search",
    description="""
    Upload a document for semantic search with full RAG pipeline processing.

    **Supported formats:** TXT, PDF, DOCX
    **Max file size:** 100MB
    **Processing stages:** Validation → Chunking → Embedding → Storage
    """,
    responses={
        201: {
            "description": "Document uploaded and processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "title": "Machine Learning Research Paper",
                            "file_name": "ml_paper.pdf",
                            "file_type": "application/pdf",
                            "file_size": 2048576,
                            "upload_status": "completed",
                            "embedding_status": "completed",
                            "created_at": "2025-10-26T10:30:00Z",
                            "updated_at": "2025-10-26T10:30:05Z",
                            "description": "Survey of transformer architectures"
                        },
                        "chunk_count": 12,
                        "message": "Document uploaded and processed successfully"
                    }
                }
            }
        },
        400: {
            "description": "Invalid file or validation failure",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_file": {
                            "summary": "Empty file uploaded",
                            "value": {
                                "detail": "File is empty"
                            }
                        },
                        "no_filename": {
                            "summary": "No filename provided",
                            "value": {
                                "detail": "No file provided"
                            }
                        },
                        "processing_error": {
                            "summary": "File processing failed",
                            "value": {
                                "detail": "Failed to process file: Unsupported file encoding"
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Request validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "title"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during chunking",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to chunk document: Unexpected error during text segmentation"
                    }
                }
            }
        },
        503: {
            "description": "External service unavailable",
            "content": {
                "application/json": {
                    "examples": {
                        "embedder_down": {
                            "summary": "Embedder service unavailable",
                            "value": {
                                "detail": "Embedding service unavailable: Connection timeout"
                            }
                        },
                        "qdrant_down": {
                            "summary": "Vector database unavailable",
                            "value": {
                                "detail": "Vector database unavailable: Cannot connect to Qdrant"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def upload_document(
    file: UploadFile = File(..., description="File to upload"),
    title: str = Form(..., description="Document title"),
    description: str | None = Form(None, description="Optional document description"),
    use_case: UploadDocumentUseCase = Depends(get_upload_document_use_case),
) -> UploadDocumentResponse:
    """Upload a document for semantic search with full RAG pipeline processing.

    Validates, chunks, embeds, and stores documents in PostgreSQL and Qdrant.

    Args:
        file: Uploaded file (TXT, PDF, DOCX). Max 100MB.
        title: Document title for display and search.
        description: Optional description for search context.
        use_case: Injected upload use case.

    Returns:
        UploadDocumentResponse with document metadata, chunk count, and success message.

    Raises:
        HTTPException: 400 for invalid files, 500 for chunking errors, 503 for service unavailability.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read file: {str(e)}",
        ) from e

    # Validate file size
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty"
        )

    # Create command
    command = UploadDocumentCommand(
        title=title,
        file_name=file.filename,
        file_content=content,
        file_size=len(content),
        description=description,
    )

    # Execute use case
    try:
        document, chunk_count = await use_case.execute(command)

        logger.info(
            f"Document {document.id} uploaded successfully with {chunk_count} chunks"
        )

        # Convert domain entity to response DTO
        return UploadDocumentResponse(
            document=document_to_response(document),
            chunk_count=chunk_count,
            message="Document uploaded and processed successfully",
        )

    except FileProcessingError as e:
        logger.error(f"File processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}",
        ) from e
    except ChunkingError as e:
        logger.error(f"Chunking failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk document: {str(e)}",
        ) from e
    except EmbeddingServiceError as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {str(e)}",
        ) from e
    except VectorStoreError as e:
        logger.error(f"Vector store operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector database unavailable: {str(e)}",
        ) from e
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        ) from e


@router.get(
    "",
    response_model=ListDocumentsResponse,
    summary="List all uploaded documents",
    description="""
    Retrieve paginated list of all uploaded documents with metadata.

    **Pagination:** 1-indexed, default 20 per page
    **Ordering:** Newest first (by created_at)
    """,
    responses={
        200: {
            "description": "List of documents retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "documents": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "title": "Research Paper 2024",
                                "file_name": "paper.pdf",
                                "file_type": "application/pdf",
                                "file_size": 2048576,
                                "upload_status": "completed",
                                "embedding_status": "completed",
                                "created_at": "2025-10-26T10:30:00Z",
                                "updated_at": "2025-10-26T10:30:00Z",
                                "description": "Machine learning survey"
                            },
                            {
                                "id": "660e8400-e29b-41d4-a716-446655440111",
                                "title": "Technical Documentation",
                                "file_name": "docs.txt",
                                "file_type": "text/plain",
                                "file_size": 512000,
                                "upload_status": "completed",
                                "embedding_status": "completed",
                                "created_at": "2025-10-26T09:15:00Z",
                                "updated_at": "2025-10-26T09:15:00Z",
                                "description": None
                            }
                        ],
                        "total": 47,
                        "page": 1,
                        "limit": 20
                    }
                }
            }
        },
        400: {
            "description": "Invalid pagination parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_page": {
                            "summary": "Page number too low",
                            "value": {
                                "detail": "Page must be >= 1"
                            }
                        },
                        "invalid_limit": {
                            "summary": "Limit out of range",
                            "value": {
                                "detail": "Limit must be between 1 and 100"
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during retrieval",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to retrieve documents: Database connection error"
                    }
                }
            }
        }
    }
)
async def list_documents(
    page: int = 1,
    limit: int = 20,
    use_case: ListDocumentsUseCase = Depends(get_list_documents_use_case),
) -> ListDocumentsResponse:
    """Retrieve paginated list of all uploaded documents with metadata.

    Returns documents ordered by creation date (newest first) with pagination support.

    Args:
        page: Page number (1-indexed). Default: 1.
        limit: Documents per page (1-100). Default: 20.
        use_case: Injected list documents use case.

    Returns:
        ListDocumentsResponse with documents array, total count, page, and limit.

    Raises:
        HTTPException: 400 for invalid pagination, 500 for database errors.
    """
    # Validation is done by use case, but we catch exceptions
    try:
        documents, total = await use_case.execute(page=page, limit=limit)

        # Convert domain entities to response DTOs
        document_responses = [document_to_response(doc) for doc in documents]

        return ListDocumentsResponse(
            documents=document_responses, total=total, page=page, limit=limit
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        ) from e


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details with all chunks",
    description="""
    Retrieve detailed information for a specific document including all text chunks.

    **Includes:** Full document metadata + all chunks with content
    **Use for:** Document detail views, content inspection, debugging
    """,
    responses={
        200: {
            "description": "Document details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Machine Learning Research",
                        "file_name": "ml_paper.pdf",
                        "file_type": "application/pdf",
                        "file_size": 2048576,
                        "upload_status": "completed",
                        "embedding_status": "completed",
                        "created_at": "2025-10-26T10:30:00Z",
                        "updated_at": "2025-10-26T10:30:05Z",
                        "description": "Survey of transformer architectures",
                        "chunks": [
                            {
                                "id": "660e8400-e29b-41d4-a716-446655440111",
                                "content": "Transformers are neural network architectures that use self-attention mechanisms to process sequential data. Unlike RNNs, transformers can process all positions simultaneously, enabling parallel computation.",
                                "chunk_index": 0,
                                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                                "token_count": 512,
                                "metadata": {
                                    "start_char": 0,
                                    "end_char": 2450,
                                    "embedding_model": "all-MiniLM-L6-v2"
                                }
                            },
                            {
                                "id": "660e8400-e29b-41d4-a716-446655440222",
                                "content": "Attention mechanisms enable models to focus on relevant parts of the input when generating outputs. The self-attention layer computes relationships between all positions in the sequence.",
                                "chunk_index": 1,
                                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                                "token_count": 498,
                                "metadata": {
                                    "start_char": 2400,
                                    "end_char": 4820,
                                    "embedding_model": "all-MiniLM-L6-v2"
                                }
                            }
                        ]
                    }
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Document with ID 550e8400-e29b-41d4-a716-446655440000 not found"
                    }
                }
            }
        },
        422: {
            "description": "Invalid UUID format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "document_id"],
                                "msg": "value is not a valid uuid",
                                "type": "type_error.uuid"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during retrieval",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to retrieve document: Database connection error"
                    }
                }
            }
        }
    }
)
async def get_document(
    document_id: UUID, use_case: GetDocumentUseCase = Depends(get_get_document_use_case)
) -> DocumentDetailResponse:
    """Retrieve detailed information for a specific document including all chunks.

    Fetches complete document metadata and all associated text chunks with content and embedding metadata.

    Args:
        document_id: UUID of the document to retrieve.
        use_case: Injected get document use case.

    Returns:
        DocumentDetailResponse with document metadata and all chunks (ordered by chunk_index).

    Raises:
        HTTPException: 404 if document not found, 500 for database errors.
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
            file_size=document.file_size or 0,  # Default to 0 if None
            file_path=document.file_path,
            upload_status=document.upload_status.value,
            embedding_status=document.embedding_status.value
            if hasattr(document, "embedding_status")
            else "completed",
            created_at=document.created_at,
            updated_at=document.created_at,  # Use created_at as documents don't track updates
            description=document.description,
            chunks=chunk_responses,
        )

    except DocumentNotFoundError:
        # DocumentNotFoundError is already an HTTPException with 404 status
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        ) from e


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document permanently",
    description="""
    Permanently delete a document and all associated data from all storage systems.

    **Removes data from:**
    - PostgreSQL (metadata + chunks)
    - Qdrant (vectors)
    - File storage (if applicable)

    **Warning:** This operation is irreversible.
    """,
    responses={
        204: {
            "description": "Document deleted successfully (empty response)"
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Document with ID 550e8400-e29b-41d4-a716-446655440000 not found"
                    }
                }
            }
        },
        422: {
            "description": "Invalid UUID format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "document_id"],
                                "msg": "value is not a valid uuid",
                                "type": "type_error.uuid"
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Vector store unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to delete vectors: Cannot connect to Qdrant"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during deletion",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to delete document: Database transaction error"
                    }
                }
            }
        }
    }
)
async def delete_document(
    document_id: UUID,
    use_case: DeleteDocumentUseCase = Depends(get_delete_document_use_case),
) -> None:
    """Permanently delete a document and all associated data from all storage systems.

    Performs cascading deletion across PostgreSQL (metadata/chunks) and Qdrant (vectors). This operation is irreversible.

    Args:
        document_id: UUID of the document to delete.
        use_case: Injected delete document use case.

    Returns:
        None. Success indicated by 204 NO CONTENT status.

    Raises:
        HTTPException: 404 if not found, 503 for Qdrant failures, 500 for database errors.
    """
    try:
        await use_case.execute(document_id)
        logger.info(f"Document {document_id} deleted successfully")

    except DocumentNotFoundError:
        # DocumentNotFoundError is already an HTTPException with 404 status
        raise
    except VectorStoreError as e:
        logger.error(f"Vector store deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to delete vectors: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        ) from e
