"""Application-wide constants

Centralizes magic numbers and configuration defaults.
These can be overridden by environment variables via Settings class.
"""

# Embedding Configuration
EMBEDDING_DIMENSION = 384  # sentence-transformers all-MiniLM-L6-v2 dimension

# Search Configuration
DEFAULT_SEARCH_LIMIT = 10  # Default number of results to return
MAX_SEARCH_LIMIT = 100  # Maximum allowed search results
MIN_SEARCH_TOP_K = 1  # Minimum allowed top_k for search queries
MAX_SEARCH_TOP_K = 100  # Maximum allowed top_k for search queries

# Chunking Configuration
DEFAULT_CHUNK_MIN_SIZE = 128  # Minimum chunk size in characters
DEFAULT_CHUNK_MAX_SIZE = 512  # Maximum chunk size in characters
SEMANTIC_BREAKPOINT_PERCENTILE = 95  # Percentile for semantic breakpoint detection

# Upload Configuration
MAX_UPLOAD_SIZE_MB = 100  # Maximum file upload size in megabytes

# Timeout Configuration
EMBEDDER_TIMEOUT_SECONDS = 30.0  # HTTP timeout for embedder service calls
GENERATOR_TIMEOUT_SECONDS = (
    60.0  # HTTP timeout for generator service calls (LLMs are slower)
)
HEALTH_CHECK_TIMEOUT_SECONDS = 5.0  # HTTP timeout for health check calls

# Vector Store Configuration
QDRANT_COLLECTION_NAME = "document_chunks"  # Name of the Qdrant collection
