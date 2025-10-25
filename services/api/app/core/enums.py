"""Core enumerations for type-safe status values.

This module provides status enums to replace magic strings throughout the codebase,
improving type safety and preventing typos.
"""

from enum import Enum


class UploadStatus(str, Enum):
    """Document upload status values.

    Represents the various states a document can be in during the upload process.
    Inherits from both str and Enum to allow direct string comparison while
    maintaining enum type safety.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EmbeddingStatus(str, Enum):
    """Embedding generation status values.

    Represents the various states of the embedding generation process for
    document chunks. Inherits from both str and Enum to allow direct string
    comparison while maintaining enum type safety.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStatus(str, Enum):
    """Document processing status values.

    Represents the various states of document processing workflow
    (extract → chunk → embed). Inherits from both str and Enum to allow
    direct string comparison while maintaining enum type safety.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
