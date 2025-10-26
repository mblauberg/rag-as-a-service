"""Common exception hierarchy for RAAS API service.

Provides consistent error handling with proper HTTP status codes
and structured error responses.
"""


class RaasException(Exception):
    """Base exception for all RAAS errors.

    Attributes:
        message: Human-readable error message.
        details: Additional error context (dict).
        status_code: HTTP status code for this error type.
    """

    status_code = 500

    def __init__(self, *args, message: str = "", details: dict | None = None, **kwargs) -> None:
        # Support multiple initialization patterns for backward compatibility:
        # 1. RaasException(message, details=dict) - new style
        # 2. RaasException(message, key=value, ...) - kwargs style
        # 3. RaasException(arg1, arg2, arg3) - old positional style
        # 4. RaasException(operation=..., original_error=...) - kwargs only

        if args:
            # Old-style positional arguments
            # Convert positional args to a message and details
            if len(args) == 1:
                self.message = str(args[0]) if not message else message
            elif len(args) == 3:
                # Old FileOperationError style: (operation, filename, exception)
                self.message = f"{args[0]} operation failed for {args[1]}: {args[2]}" if not message else message
                kwargs.update({"operation": args[0], "filename": args[1], "original_error": str(args[2])})
            else:
                self.message = " ".join(str(arg) for arg in args) if not message else message
        elif not message and kwargs:
            # Generate message from kwargs if no message provided
            if "operation" in kwargs and "original_error" in kwargs:
                # Clean up operation name for error message
                operation = kwargs['operation'].replace('_', ' ')
                # Special case for chunking operations
                if operation.lower().startswith('chunk'):
                    operation = "Chunking"
                # Capitalize first letter only
                elif operation:
                    operation = operation[0].upper() + operation[1:]
                self.message = f"{operation} operation failed: {kwargs['original_error']}"
            else:
                self.message = "Operation failed"
        else:
            self.message = message

        self.details = details or {}
        # Merge any additional kwargs into details
        self.details.update(kwargs)
        # Also set kwargs as direct attributes for backward compatibility
        for key, value in kwargs.items():
            setattr(self, key, value)
        super().__init__(self.message)


class ServiceUnavailableError(RaasException):
    """External service unavailable (embedder, generator, search, qdrant).

    Used when HTTP requests to dependent services fail or timeout.
    """

    status_code = 503


class ResourceNotFoundError(RaasException):
    """Requested resource not found in database.

    Used for missing documents, chunks, or other database entities.
    """

    status_code = 404


class ValidationError(RaasException):
    """Input validation failed.

    Used for invalid request parameters, malformed data, or
    business rule violations.
    """

    status_code = 422


class StorageError(RaasException):
    """Database or vector store operation failed.

    Used for database connection errors, transaction failures,
    or Qdrant operations that fail unexpectedly.
    """

    status_code = 500


class AuthenticationError(RaasException):
    """Authentication failed.

    Reserved for future authentication implementation.
    """

    status_code = 401


# Backward compatibility aliases
DocumentNotFoundError = ResourceNotFoundError
VectorStoreError = StorageError
ChunkingError = ValidationError
EmbeddingServiceError = ServiceUnavailableError
FileOperationError = StorageError
FileProcessingError = ValidationError
GenerationServiceError = ServiceUnavailableError
