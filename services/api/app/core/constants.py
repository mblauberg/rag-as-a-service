"""Application-wide constants

Centralizes magic numbers and configuration defaults.
These can be overridden by environment variables via Settings class.
"""

# Embedding Configuration
EMBEDDING_DIMENSION = 384  # sentence-transformers all-MiniLM-L6-v2 dimension

# Search Configuration
DEFAULT_SEARCH_LIMIT = 10  # Default number of results to return
MAX_SEARCH_LIMIT = 100  # Maximum allowed search results

# Chunking Configuration
DEFAULT_CHUNK_MIN_SIZE = 128  # Minimum chunk size in characters
DEFAULT_CHUNK_MAX_SIZE = 512  # Maximum chunk size in characters
SEMANTIC_BREAKPOINT_PERCENTILE = 95  # Percentile for semantic breakpoint detection

# Upload Configuration
MAX_UPLOAD_SIZE_MB = 100  # Maximum file upload size in megabytes

# Timeout Configuration
EMBEDDER_TIMEOUT_SECONDS = 30.0  # HTTP timeout for embedder service calls
GENERATOR_TIMEOUT_SECONDS = 60.0  # HTTP timeout for generator service calls (LLMs are slower)
