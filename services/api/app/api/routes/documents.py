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

    This endpoint orchestrates the complete document upload workflow using hexagonal
    architecture principles. Documents are validated, chunked into semantic segments,
    embedded using sentence transformers, and stored in both PostgreSQL (metadata)
    and Qdrant (vectors) for hybrid search.

    The upload process follows these stages:
        1. **File Validation**: Verifies file type (TXT, PDF, DOCX), size (<100MB),
           and content integrity
        2. **Text Extraction**: Extracts raw text using appropriate parser for file type
        3. **Semantic Chunking**: Splits text into semantically coherent segments with
           overlap for context preservation
        4. **Embedding Generation**: Calls embedder microservice to generate 384-dim
           vectors using sentence-transformers
        5. **Vector Storage**: Stores embeddings in Qdrant for efficient ANN search
        6. **Metadata Persistence**: Saves document and chunk metadata in PostgreSQL
           with full-text search indexes

    **Supported File Formats:**
        - TXT: Plain text files (UTF-8 encoding)
        - PDF: Adobe PDF documents (text extraction only, no OCR)
        - DOCX: Microsoft Word documents

    **Processing Limits:**
        - Max file size: 100 MB
        - Max processing time: 60 seconds
        - Recommended chunk size: 512 tokens with 50 token overlap

    Args:
        file: Uploaded file object with content and metadata. Must have valid
            filename and non-empty content. Multipart form-data field.
        title: Human-readable document title for display and search. Used in
            search results and document listings. Required field.
        description: Optional longer description providing context about document
            content, source, or purpose. Indexed for full-text search.
        use_case: Injected upload document use case following clean architecture.
            Handles domain logic and orchestration. Auto-injected via FastAPI
            dependency injection.

    Returns:
        UploadDocumentResponse containing:
            - document: Full document metadata including UUID, status, timestamps
            - chunk_count: Number of semantic chunks created (typically 5-20 per document)
            - message: Success confirmation message

        Example response:
            {
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

    Raises:
        HTTPException: Multiple failure modes with appropriate status codes:
            - 400 BAD_REQUEST: Invalid file (empty, no filename), validation failures,
              or file processing errors (corrupt PDF, unsupported encoding)
            - 500 INTERNAL_SERVER_ERROR: Unexpected failures during chunking or
              internal processing errors
            - 503 SERVICE_UNAVAILABLE: Embedder microservice unreachable or Qdrant
              vector database connection failures

        Specific exception types handled:
            - FileProcessingError: File parsing or text extraction failures
            - ChunkingError: Semantic segmentation failures
            - EmbeddingServiceError: Embedder microservice unavailable or timeout
            - VectorStoreError: Qdrant connection or insertion failures
            - ValueError: Invalid parameters or business rule violations

    Example:
        Using httpx for testing:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     files = {"file": ("doc.txt", b"AI research content", "text/plain")}
            ...     data = {"title": "AI Research", "description": "Overview of AI"}
            ...     response = await client.post(
            ...         "http://localhost:8000/api/v1/documents/upload",
            ...         files=files,
            ...         data=data
            ...     )
            ...     print(response.json()["chunk_count"])
            8

        Using curl:
            $ curl -X POST "http://localhost:8000/api/v1/documents/upload" \\
                -F "file=@document.pdf" \\
                -F "title=Research Paper" \\
                -F "description=ML transformer survey"

    Notes:
        - Processing is synchronous; client waits for full pipeline completion
        - Large documents (>50MB) may experience longer processing times
        - Duplicate detection is not performed; same document can be uploaded multiple times
        - Document embeddings are immutable after creation (no re-embedding support)
        - Failed uploads automatically rollback database transactions but may leave
          orphaned vectors in Qdrant (cleaned up by background job)
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
        )

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
        )
    except ChunkingError as e:
        logger.error(f"Chunking failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk document: {str(e)}",
        )
    except EmbeddingServiceError as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding service unavailable: {str(e)}",
        )
    except VectorStoreError as e:
        logger.error(f"Vector store operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector database unavailable: {str(e)}",
        )
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


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

    Returns all documents in the system ordered by creation date (newest first),
    with pagination support for efficient loading of large document collections.
    Each document includes full metadata but excludes chunk content for
    performance.

    This endpoint is designed for document management UIs, enabling users to:
        - Browse their document library
        - View upload and processing status
        - Check file metadata (size, type, timestamps)
        - Navigate to detailed document views

    **Pagination Behavior:**
        - Page numbers are 1-indexed (first page is 1, not 0)
        - Empty pages return empty results array (not 404)
        - Total count reflects all documents regardless of pagination
        - Default limit of 20 balances performance and UX

    Args:
        page: Page number for pagination, starting at 1. Must be positive integer.
            Requesting page beyond available pages returns empty results.
            Default: 1 (first page)
        limit: Maximum number of documents per page. Must be between 1 and 100.
            Higher limits may impact response time for large document collections.
            Default: 20 documents per page
        use_case: Injected list documents use case handling query logic and data
            access. Auto-injected via FastAPI dependency system following clean
            architecture principles.

    Returns:
        ListDocumentsResponse containing:
            - documents: Array of document metadata objects (see DocumentResponse)
            - total: Total number of documents in system (all pages)
            - page: Current page number (echoed from request)
            - limit: Current page size (echoed from request)

        Example response:
            {
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
                    }
                ],
                "total": 47,
                "page": 1,
                "limit": 20
            }

    Raises:
        HTTPException: Validation or processing failures:
            - 400 BAD_REQUEST: Invalid pagination parameters (page < 1, limit < 1
              or limit > 100, or non-integer values)
            - 500 INTERNAL_SERVER_ERROR: Database query failures or unexpected
              errors during document retrieval

        Specific validation rules:
            - ValueError: Raised by use case for invalid page/limit values, converted
              to 400 BAD_REQUEST by route handler

    Example:
        Fetch first page with default limit:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get("http://localhost:8000/api/v1/documents")
            ...     documents = response.json()["documents"]
            ...     print(f"Found {len(documents)} documents")
            Found 20 documents

        Fetch specific page with custom limit:
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get(
            ...         "http://localhost:8000/api/v1/documents?page=2&limit=50"
            ...     )
            ...     print(response.json()["total"])
            47

        Using curl:
            $ curl "http://localhost:8000/api/v1/documents?page=1&limit=10"

    Notes:
        - Documents are ordered by created_at descending (newest first)
        - Pagination uses OFFSET/LIMIT SQL queries (may be slow for deep pages
          on very large collections; consider cursor-based pagination for >10k docs)
        - Document status fields reflect processing state: 'pending', 'processing',
          'completed', or 'failed'
        - Deleted documents are excluded from results (soft delete not implemented)
        - Response includes total count for pagination UI (e.g., "Page 2 of 5")
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}",
        )


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

    Fetches complete document metadata and all associated text chunks with their
    embeddings metadata. This endpoint is designed for document detail views,
    content inspection, and debugging the chunking/embedding pipeline.

    Unlike the list endpoint which only returns document-level metadata, this
    endpoint includes the full chunk collection with:
        - Chunk text content
        - Chunk position/index within document
        - Embedding status and metadata
        - Token counts and boundaries

    This data is essential for:
        - Displaying document content in the UI
        - Debugging why search results include/exclude certain passages
        - Understanding how documents were segmented
        - Verifying embedding pipeline processed all chunks

    Args:
        document_id: UUID of the document to retrieve. Must be a valid UUID v4
            format and correspond to an existing document in the database.
            Example: "550e8400-e29b-41d4-a716-446655440000"
        use_case: Injected get document use case handling data retrieval and
            domain logic. Auto-injected via FastAPI dependency system.

    Returns:
        DocumentDetailResponse containing:
            - All document metadata (id, title, file info, status, timestamps)
            - chunks: Complete array of all chunks with content and metadata
            - Each chunk includes: id, content, chunk_index, token_count, metadata

        Example response:
            {
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
                        "content": "Transformers are neural network architectures...",
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
                        "content": "Attention mechanisms enable models to focus...",
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

    Raises:
        HTTPException: Multiple failure scenarios:
            - 404 NOT_FOUND: Document with specified UUID does not exist in database.
              This is the most common error when document_id is invalid or document
              was deleted.
            - 500 INTERNAL_SERVER_ERROR: Database query failures, connection errors,
              or unexpected exceptions during retrieval.

        Specific exception types:
            - DocumentNotFoundError: Raised by use case when document doesn't exist,
              automatically converted to 404 by route handler
            - Database connection errors: Converted to 500 status

    Example:
        Retrieve document with all chunks:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     doc_id = "550e8400-e29b-41d4-a716-446655440000"
            ...     response = await client.get(
            ...         f"http://localhost:8000/api/v1/documents/{doc_id}"
            ...     )
            ...     document = response.json()
            ...     print(f"Document has {len(document['chunks'])} chunks")
            Document has 12 chunks

        Check if document exists:
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.get(
            ...         f"http://localhost:8000/api/v1/documents/{doc_id}"
            ...     )
            ...     if response.status_code == 200:
            ...         print("Document exists")
            ...     elif response.status_code == 404:
            ...         print("Document not found")
            Document exists

        Using curl:
            $ curl "http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000"

    Notes:
        - Chunks are returned in order by chunk_index (document reading order)
        - Large documents with many chunks may have significant response sizes
          (typical: 50-500KB for research papers with 20-50 chunks)
        - Chunk content includes overlap regions for context preservation
        - Embedding vectors are NOT included in response (stored separately in Qdrant)
        - This endpoint does not perform search or relevance ranking; chunks are
          in document order, not relevance order
        - Document status 'completed' means all chunks have embeddings; 'failed'
          indicates embedding pipeline errors
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

    except DocumentNotFoundError as e:
        # DocumentNotFoundError is already an HTTPException with 404 status
        raise e
    except Exception as e:
        logger.error(f"Failed to get document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}",
        )


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

    Performs cascading deletion across all storage layers in the RAG system,
    ensuring complete removal of document data and freeing storage resources.
    This operation is irreversible and should be used with caution.

    The deletion process removes data from three storage systems:
        1. **PostgreSQL (Relational DB):**
           - Document metadata record (title, file info, timestamps)
           - All associated chunk records with text content
           - Full-text search indexes for the document

        2. **Qdrant (Vector DB):**
           - All embedding vectors for document chunks
           - Vector metadata and payload data
           - Frees vector storage space

        3. **File Storage (if implemented):**
           - Original uploaded file from disk/S3 (future feature)

    The operation uses database transactions to ensure consistency. If deletion
    fails in any system (e.g., Qdrant connection error), the transaction is
    rolled back and document metadata remains intact for retry.

    **Safety Considerations:**
        - Deletion is permanent; no undo or recovery mechanism exists
        - Related search results immediately stop returning this document's chunks
        - In-flight searches may briefly reference deleted chunks (eventual consistency)
        - Consider archiving instead of deletion for audit/compliance requirements

    Args:
        document_id: UUID of the document to delete. Must be a valid UUID v4
            format corresponding to an existing document.
            Example: "550e8400-e29b-41d4-a716-446655440000"
        use_case: Injected delete document use case handling deletion orchestration
            across storage layers. Auto-injected via FastAPI dependency system.

    Returns:
        None. Success is indicated by 204 NO CONTENT status code with empty response
        body. This follows RESTful conventions for successful DELETE operations.

    Raises:
        HTTPException: Multiple failure scenarios:
            - 404 NOT_FOUND: Document with specified UUID does not exist. Already
              deleted documents or invalid UUIDs trigger this error.
            - 503 SERVICE_UNAVAILABLE: Qdrant vector store is unreachable or
              vector deletion failed. Document metadata remains intact for retry.
            - 500 INTERNAL_SERVER_ERROR: Unexpected errors during deletion,
              database transaction failures, or connection issues.

        Specific exception types:
            - DocumentNotFoundError: Document doesn't exist, converted to 404
            - VectorStoreError: Qdrant connection or deletion failures, converted
              to 503 to indicate temporary service unavailability
            - Database errors: Connection or transaction failures, converted to 500

    Example:
        Delete a document:
            >>> import httpx
            >>> async with httpx.AsyncClient() as client:
            ...     doc_id = "550e8400-e29b-41d4-a716-446655440000"
            ...     response = await client.delete(
            ...         f"http://localhost:8000/api/v1/documents/{doc_id}"
            ...     )
            ...     if response.status_code == 204:
            ...         print("Document deleted successfully")
            Document deleted successfully

        Delete with error handling:
            >>> async with httpx.AsyncClient() as client:
            ...     response = await client.delete(
            ...         f"http://localhost:8000/api/v1/documents/{doc_id}"
            ...     )
            ...     if response.status_code == 404:
            ...         print("Document not found or already deleted")
            ...     elif response.status_code == 503:
            ...         print("Vector store unavailable, retry later")

        Using curl:
            $ curl -X DELETE "http://localhost:8000/api/v1/documents/550e8400-e29b-41d4-a716-446655440000"

    Notes:
        - Deletion is synchronous; client waits for complete removal from all systems
        - Database cascading deletes automatically remove chunks when document is deleted
        - Orphaned vectors in Qdrant are removed by document_id payload filter
        - Failed deletions can be retried safely (idempotent operation for 404 case)
        - Large documents with many chunks may take several seconds to delete
        - Background cleanup job periodically removes any orphaned data from failed deletions
        - Consider implementing soft delete (marking as deleted) instead of hard delete
          for audit trails and potential recovery
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
            detail=f"Failed to delete vectors: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )
