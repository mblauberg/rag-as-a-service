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

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
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
