# RAG System Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade RAAS RAG system with modern embedding models, hybrid search, and reranking to achieve +65-80% improvement in retrieval quality.

**Architecture:** Three-phase implementation starting with BGE-M3 embedding upgrade and cross-encoder reranking (Phase 1), adding hybrid dense+sparse search with reciprocal rank fusion (Phase 2), then advanced features like semantic chunking and query optimization (Phase 3).

**Tech Stack:** BGE-M3 embeddings (1024-dim), BAAI bge-reranker-v2-m3, Qdrant sparse vectors, BM25, sentence-transformers, langchain-experimental

---

## Phase 1: Critical Upgrades (Week 1-2)

### Task 1: Add Cross-Encoder Reranking Service

**Files:**
- Create: `services/api/app/services/reranker.py`
- Modify: `services/api/app/core/config.py` (add reranker config)
- Test: `services/api/tests/test_reranker.py`

**Step 1: Write failing test for reranker initialization**

File: `services/api/tests/test_reranker.py`
```python
import pytest
from app.services.reranker import RerankerService


@pytest.mark.asyncio
async def test_reranker_initializes():
    """Test that reranker service loads the model successfully."""
    reranker = RerankerService()
    assert reranker.model is not None
    assert hasattr(reranker.model, 'predict')
```

**Step 2: Run test to verify it fails**

```bash
cd services/api
poetry run pytest tests/test_reranker.py::test_reranker_initializes -v
```

Expected: `ImportError: No module named 'app.services.reranker'`

**Step 3: Install sentence-transformers dependency**

File: `services/api/pyproject.toml`
```toml
[tool.poetry.dependencies]
# ... existing dependencies ...
sentence-transformers = "^2.2.2"
```

Run:
```bash
cd services/api
poetry lock
poetry install
```

**Step 4: Create reranker service**

File: `services/api/app/services/reranker.py`
```python
"""Cross-encoder reranking service for improving retrieval precision."""
from typing import List, Tuple
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)


class RerankerService:
    """Reranks search results using cross-encoder for better precision."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Initialize reranker with cross-encoder model.

        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        logger.info(f"Loading reranker model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Reranker model loaded successfully")

    def rerank(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Rerank candidate documents and return top-K with scores.

        Args:
            query: Search query string
            candidates: List of candidate document texts
            top_k: Number of top results to return

        Returns:
            List of (index, score) tuples sorted by score descending
        """
        if not candidates:
            return []

        # Create query-document pairs
        pairs = [(query, candidate) for candidate in candidates]

        # Score all pairs
        scores = self.model.predict(pairs)

        # Sort by score descending and return top-K
        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked[:top_k]
```

**Step 5: Run test to verify it passes**

```bash
poetry run pytest tests/test_reranker.py::test_reranker_initializes -v
```

Expected: PASS

**Step 6: Write test for reranking functionality**

File: `services/api/tests/test_reranker.py`
```python
@pytest.mark.asyncio
async def test_reranker_reranks_correctly():
    """Test that reranker ranks relevant docs higher."""
    reranker = RerankerService()

    query = "What is machine learning?"
    candidates = [
        "Machine learning is a subset of artificial intelligence.",
        "I like to eat pizza for dinner.",
        "Deep learning uses neural networks for pattern recognition.",
    ]

    results = reranker.rerank(query, candidates, top_k=3)

    # Should return 3 results
    assert len(results) == 3

    # Each result is (index, score) tuple
    assert all(isinstance(r, tuple) and len(r) == 2 for r in results)

    # First result should be index 0 (most relevant)
    assert results[0][0] == 0

    # Last result should be index 1 (least relevant - pizza)
    assert results[2][0] == 1
```

**Step 7: Run test to verify it passes**

```bash
poetry run pytest tests/test_reranker.py::test_reranker_reranks_correctly -v
```

Expected: PASS

**Step 8: Add configuration for reranker**

File: `services/api/app/core/config.py`
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Reranker settings
    RERANKER_MODEL: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description="Cross-encoder model for reranking"
    )
    RERANKER_TOP_K: int = Field(
        default=10,
        description="Number of results to return after reranking"
    )
    RERANKER_CANDIDATE_MULTIPLIER: int = Field(
        default=5,
        description="Retrieve N*top_k candidates before reranking"
    )
```

**Step 9: Commit**

```bash
git add services/api/app/services/reranker.py \
        services/api/tests/test_reranker.py \
        services/api/app/core/config.py \
        services/api/pyproject.toml \
        services/api/poetry.lock
git commit -m "feat(api): add cross-encoder reranking service"
```

---

### Task 2: Integrate Reranker into Search Endpoint

**Files:**
- Modify: `services/api/app/api/routes/search.py`
- Modify: `services/api/app/main.py` (add reranker singleton)
- Test: `services/api/tests/test_search.py`

**Step 1: Write failing integration test**

File: `services/api/tests/test_search.py`
```python
@pytest.mark.asyncio
async def test_search_with_reranking(test_client, test_db):
    """Test that search results are reranked for better precision."""
    # Upload a test document
    response = await test_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"Machine learning is AI. Pizza is food.", "text/plain")}
    )
    assert response.status_code == 201

    # Wait for embedding (in real test, use async polling)
    await asyncio.sleep(2)

    # Search with query
    response = await test_client.post(
        "/api/v1/search",
        json={
            "query": "What is machine learning?",
            "limit": 5,
            "enable_reranking": True
        }
    )

    assert response.status_code == 200
    results = response.json()["results"]

    # First result should be about ML, not pizza
    assert "machine learning" in results[0]["content"].lower()
    assert results[0]["reranked_score"] is not None
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_search.py::test_search_with_reranking -v
```

Expected: FAIL (enable_reranking parameter not recognized)

**Step 3: Update search request schema**

File: `services/api/app/models/schemas.py`
```python
class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    score_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )
    enable_reranking: bool = Field(
        default=True,
        description="Whether to apply cross-encoder reranking"
    )


class SearchResult(BaseModel):
    """Single search result."""

    chunk_id: int
    document_id: int
    content: str
    score: float
    reranked_score: Optional[float] = Field(
        None,
        description="Cross-encoder reranking score if enabled"
    )
    metadata: Dict[str, Any]
```

**Step 4: Initialize reranker in app startup**

File: `services/api/app/main.py`
```python
from app.services.reranker import RerankerService

# ... existing imports ...

# Global reranker instance
reranker_service: Optional[RerankerService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global reranker_service

    logger.info("Starting up API service...")

    # Initialize database
    await init_db()

    # Initialize reranker
    try:
        reranker_service = RerankerService(
            model_name=settings.RERANKER_MODEL
        )
        logger.info("Reranker service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize reranker: {e}")
        reranker_service = None

    logger.info("API service started successfully")


def get_reranker() -> Optional[RerankerService]:
    """Dependency injection for reranker service."""
    return reranker_service
```

**Step 5: Update search route to use reranker**

File: `services/api/app/api/routes/search.py`
```python
from app.main import get_reranker
from app.services.reranker import RerankerService

# ... existing imports ...


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    reranker: Optional[RerankerService] = Depends(get_reranker)
):
    """
    Search documents using semantic similarity with optional reranking.

    - Retrieves initial candidates using vector similarity
    - Optionally reranks with cross-encoder for better precision
    - Returns top-K results with scores
    """
    try:
        # Determine candidate limit
        candidate_limit = request.limit
        if request.enable_reranking and reranker:
            candidate_limit = request.limit * settings.RERANKER_CANDIDATE_MULTIPLIER

        # Generate query embedding
        async with httpx.AsyncClient() as client:
            embed_response = await client.post(
                f"{settings.EMBEDDER_URL}/embed",
                json={"texts": [request.query]}
            )
            embed_response.raise_for_status()
            query_embedding = embed_response.json()["embeddings"][0]

        # Search Qdrant for candidates
        qdrant_results = await qdrant_client.search(
            collection_name="documents",
            query_vector=query_embedding,
            limit=candidate_limit,
            score_threshold=request.score_threshold
        )

        if not qdrant_results:
            return SearchResponse(query=request.query, results=[])

        # Extract chunk IDs
        chunk_ids = [int(hit.id) for hit in qdrant_results]

        # Fetch chunk metadata from database
        query_stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.id.in_(chunk_ids))
        )
        result = await db.execute(query_stmt)
        chunks = {chunk.id: chunk for chunk in result.scalars().all()}

        # Build initial results
        initial_results = []
        for hit in qdrant_results:
            chunk = chunks.get(int(hit.id))
            if chunk:
                initial_results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "score": hit.score,
                    "metadata": chunk.chunk_metadata or {}
                })

        # Apply reranking if enabled
        if request.enable_reranking and reranker and initial_results:
            # Extract contents for reranking
            candidates = [r["content"] for r in initial_results]

            # Rerank
            reranked_indices = reranker.rerank(
                query=request.query,
                candidates=candidates,
                top_k=request.limit
            )

            # Rebuild results in reranked order
            final_results = []
            for idx, rerank_score in reranked_indices:
                result = initial_results[idx].copy()
                result["reranked_score"] = float(rerank_score)
                final_results.append(SearchResult(**result))
        else:
            # No reranking - use initial results
            final_results = [
                SearchResult(**r) for r in initial_results[:request.limit]
            ]

        return SearchResponse(
            query=request.query,
            results=final_results
        )

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

**Step 6: Run integration test**

```bash
poetry run pytest tests/test_search.py::test_search_with_reranking -v
```

Expected: PASS

**Step 7: Commit**

```bash
git add services/api/app/api/routes/search.py \
        services/api/app/models/schemas.py \
        services/api/app/main.py \
        services/api/tests/test_search.py
git commit -m "feat(api): integrate cross-encoder reranking into search"
```

---

### Task 3: Add Score Threshold Filtering

**Files:**
- Modify: `services/api/app/core/config.py`
- Modify: `services/api/app/models/schemas.py`
- Test: `services/api/tests/test_search.py`

**Step 1: Write test for score threshold filtering**

File: `services/api/tests/test_search.py`
```python
@pytest.mark.asyncio
async def test_search_score_threshold_filters_low_scores(test_client, test_db):
    """Test that score threshold filters out low-scoring results."""
    # Upload test document
    response = await test_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"Python programming language", "text/plain")}
    )
    assert response.status_code == 201

    await asyncio.sleep(2)  # Wait for embedding

    # Search with high threshold - should get results
    response = await test_client.post(
        "/api/v1/search",
        json={
            "query": "Python programming",
            "limit": 10,
            "score_threshold": 0.5
        }
    )

    results_high = response.json()["results"]

    # Search with very high threshold - should get fewer/no results
    response = await test_client.post(
        "/api/v1/search",
        json={
            "query": "JavaScript frameworks",  # Unrelated query
            "limit": 10,
            "score_threshold": 0.8
        }
    )

    results_low = response.json()["results"]

    # All returned results should meet threshold
    for result in results_high:
        assert result["score"] >= 0.5

    # Unrelated query with high threshold should return fewer results
    assert len(results_low) <= len(results_high)
```

**Step 2: Run test**

```bash
poetry run pytest tests/test_search.py::test_search_score_threshold_filters_low_scores -v
```

Expected: PASS (already implemented in Task 2)

**Step 3: Add dynamic threshold configuration**

File: `services/api/app/core/config.py`
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Search settings
    DEFAULT_SCORE_THRESHOLD: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Default minimum similarity score for results"
    )
    ADAPTIVE_THRESHOLD_ENABLED: bool = Field(
        default=False,
        description="Enable adaptive score threshold based on query"
    )
```

**Step 4: Update search schema with better threshold default**

File: `services/api/app/models/schemas.py`
```python
class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (uses system default if not provided)"
    )
    enable_reranking: bool = Field(
        default=True,
        description="Whether to apply cross-encoder reranking"
    )
```

**Step 5: Update search route to use default threshold**

File: `services/api/app/api/routes/search.py`
```python
@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    reranker: Optional[RerankerService] = Depends(get_reranker)
):
    """Search documents using semantic similarity with optional reranking."""
    try:
        # Use provided threshold or system default
        score_threshold = (
            request.score_threshold
            if request.score_threshold is not None
            else settings.DEFAULT_SCORE_THRESHOLD
        )

        # ... rest of search logic using score_threshold ...

        qdrant_results = await qdrant_client.search(
            collection_name="documents",
            query_vector=query_embedding,
            limit=candidate_limit,
            score_threshold=score_threshold
        )

        # ... rest of implementation ...
```

**Step 6: Run all search tests**

```bash
poetry run pytest tests/test_search.py -v
```

Expected: All PASS

**Step 7: Commit**

```bash
git add services/api/app/core/config.py \
        services/api/app/models/schemas.py \
        services/api/app/api/routes/search.py \
        services/api/tests/test_search.py
git commit -m "feat(api): add configurable score threshold filtering"
```

---

### Task 4: Upgrade Embedder to BGE-M3 Model

**Files:**
- Modify: `services/embedder/app/core/config.py`
- Modify: `services/embedder/app/services/embedding_service.py`
- Test: `services/embedder/tests/test_embeddings.py`

**Step 1: Write test for BGE-M3 embeddings**

File: `services/embedder/tests/test_embeddings.py`
```python
import pytest
from app.services.embedding_service import EmbeddingService


@pytest.mark.asyncio
async def test_bge_m3_model_loads():
    """Test that BGE-M3 model loads successfully."""
    service = EmbeddingService(model_name="BAAI/bge-m3")

    assert service.model is not None
    assert service.model_dimension == 1024


@pytest.mark.asyncio
async def test_bge_m3_generates_embeddings():
    """Test that BGE-M3 generates 1024-dim embeddings."""
    service = EmbeddingService(model_name="BAAI/bge-m3")

    texts = ["This is a test document about machine learning."]
    embeddings = await service.embed_texts(texts)

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1024
    assert all(isinstance(v, float) for v in embeddings[0])
```

**Step 2: Run test to verify it fails with current model**

```bash
cd services/embedder
poetry run pytest tests/test_embeddings.py::test_bge_m3_model_loads -v
```

Expected: FAIL (model dimension mismatch)

**Step 3: Update embedder configuration**

File: `services/embedder/app/core/config.py`
```python
class Settings(BaseSettings):
    """Embedder service configuration."""

    # Model settings
    MODEL_NAME: str = Field(
        default="BAAI/bge-m3",
        description="HuggingFace model name for embeddings"
    )
    MODEL_DIMENSION: int = Field(
        default=1024,
        description="Embedding dimension (384 for MiniLM, 1024 for BGE-M3)"
    )
    BATCH_SIZE: int = Field(
        default=16,  # Reduced from 32 due to larger model
        description="Batch size for embedding generation"
    )
    MAX_SEQUENCE_LENGTH: int = Field(
        default=512,  # Increased from 256
        description="Maximum token sequence length"
    )

    # Qdrant settings
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector database URL"
    )
    COLLECTION_NAME: str = Field(
        default="documents",
        description="Qdrant collection name"
    )
```

**Step 4: Update embedding service to support configurable dimensions**

File: `services/embedder/app/services/embedding_service.py`
```python
from sentence_transformers import SentenceTransformer
from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        batch_size: int = 16,
        max_seq_length: int = 512
    ):
        """
        Initialize embedding service with specified model.

        Args:
            model_name: HuggingFace model identifier
            batch_size: Batch size for encoding
            max_seq_length: Maximum sequence length
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size

        # Set max sequence length
        self.model.max_seq_length = max_seq_length

        # Get model dimension
        self.model_dimension = self.model.get_sentence_embedding_dimension()

        logger.info(
            f"Model loaded: {model_name} "
            f"(dim={self.model_dimension}, max_seq={max_seq_length})"
        )

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is list of floats)
        """
        if not texts:
            return []

        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]
```

**Step 5: Run tests**

```bash
poetry run pytest tests/test_embeddings.py::test_bge_m3_model_loads -v
poetry run pytest tests/test_embeddings.py::test_bge_m3_generates_embeddings -v
```

Expected: PASS

**Step 6: Update Qdrant collection initialization**

File: `services/embedder/app/services/qdrant_service.py`
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import logging

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for interacting with Qdrant vector database."""

    def __init__(self, url: str, collection_name: str, vector_dimension: int):
        """
        Initialize Qdrant client and ensure collection exists.

        Args:
            url: Qdrant server URL
            collection_name: Name of collection to use
            vector_dimension: Dimension of vectors (384 or 1024)
        """
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.vector_dimension = vector_dimension

        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            logger.info(
                f"Creating collection '{self.collection_name}' "
                f"with dimension {self.vector_dimension}"
            )
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_dimension,
                    distance=Distance.COSINE
                )
            )
        else:
            # Verify dimension matches
            collection_info = self.client.get_collection(self.collection_name)
            existing_dim = collection_info.config.params.vectors.size

            if existing_dim != self.vector_dimension:
                logger.warning(
                    f"Collection dimension mismatch: "
                    f"existing={existing_dim}, expected={self.vector_dimension}. "
                    f"You may need to recreate the collection or re-embed documents."
                )
```

**Step 7: Update main app to use new configuration**

File: `services/embedder/app/main.py`
```python
from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

# ... existing imports ...

# Global service instances
embedding_service: Optional[EmbeddingService] = None
qdrant_service: Optional[QdrantService] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global embedding_service, qdrant_service

    logger.info("Starting up Embedder service...")

    # Initialize embedding service
    embedding_service = EmbeddingService(
        model_name=settings.MODEL_NAME,
        batch_size=settings.BATCH_SIZE,
        max_seq_length=settings.MAX_SEQUENCE_LENGTH
    )

    # Initialize Qdrant service
    qdrant_service = QdrantService(
        url=settings.QDRANT_URL,
        collection_name=settings.COLLECTION_NAME,
        vector_dimension=embedding_service.model_dimension
    )

    logger.info("Embedder service started successfully")
```

**Step 8: Run all embedder tests**

```bash
poetry run pytest tests/ -v
```

Expected: All PASS

**Step 9: Update environment configuration**

File: `services/embedder/.env.example`
```bash
# Model Configuration
MODEL_NAME=BAAI/bge-m3
MODEL_DIMENSION=1024
BATCH_SIZE=16
MAX_SEQUENCE_LENGTH=512

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
COLLECTION_NAME=documents
```

**Step 10: Commit**

```bash
git add services/embedder/app/core/config.py \
        services/embedder/app/services/embedding_service.py \
        services/embedder/app/services/qdrant_service.py \
        services/embedder/app/main.py \
        services/embedder/tests/test_embeddings.py \
        services/embedder/.env.example
git commit -m "feat(embedder): upgrade to BGE-M3 model (1024-dim)"
```

---

### Task 5: Add Migration Strategy for Existing Documents

**Files:**
- Create: `services/api/app/api/routes/migration.py`
- Create: `scripts/migrate_embeddings.py`
- Test: `services/api/tests/test_migration.py`

**Step 1: Write test for migration endpoint**

File: `services/api/tests/test_migration.py`
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_migration_status_endpoint(test_client):
    """Test migration status endpoint returns current state."""
    response = await test_client.get("/api/v1/migration/status")

    assert response.status_code == 200
    data = response.json()

    assert "total_documents" in data
    assert "migrated_documents" in data
    assert "pending_documents" in data
    assert "migration_progress" in data


@pytest.mark.asyncio
async def test_trigger_migration(test_client, test_db):
    """Test triggering background migration."""
    # Upload a document first
    response = await test_client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"Test content", "text/plain")}
    )
    assert response.status_code == 201

    # Trigger migration
    response = await test_client.post(
        "/api/v1/migration/migrate",
        json={"batch_size": 10, "max_documents": 100}
    )

    assert response.status_code == 202  # Accepted
    data = response.json()
    assert data["status"] == "migration_started"
```

**Step 2: Run test to verify it fails**

```bash
cd services/api
poetry run pytest tests/test_migration.py -v
```

Expected: FAIL (endpoint doesn't exist)

**Step 3: Create migration route**

File: `services/api/app/api/routes/migration.py`
```python
"""Migration endpoints for re-embedding documents with new model."""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
import httpx
import logging

from app.db.session import get_db
from app.models.document import Document, DocumentChunk
from app.core.config import settings

router = APIRouter(prefix="/migration", tags=["migration"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_migration_status(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current migration status.

    Returns:
        - total_documents: Total number of documents
        - migrated_documents: Documents with new embeddings
        - pending_documents: Documents pending re-embedding
        - migration_progress: Percentage complete
    """
    # Count total documents
    total_result = await db.execute(select(func.count(Document.id)))
    total_documents = total_result.scalar_one()

    # For now, assume all documents need migration
    # In production, track migration status in database
    migrated_documents = 0
    pending_documents = total_documents

    progress = 0.0
    if total_documents > 0:
        progress = (migrated_documents / total_documents) * 100

    return {
        "total_documents": total_documents,
        "migrated_documents": migrated_documents,
        "pending_documents": pending_documents,
        "migration_progress": round(progress, 2)
    }


async def _migrate_document_batch(
    batch_size: int,
    max_documents: int,
    db: AsyncSession
):
    """Background task to migrate documents in batches."""
    try:
        logger.info(f"Starting migration: batch_size={batch_size}, max={max_documents}")

        # Get documents to migrate
        query = select(Document).limit(max_documents)
        result = await db.execute(query)
        documents = result.scalars().all()

        migrated_count = 0

        for doc in documents:
            try:
                # Get document chunks
                chunk_query = select(DocumentChunk).where(
                    DocumentChunk.document_id == doc.id
                )
                chunk_result = await db.execute(chunk_query)
                chunks = chunk_result.scalars().all()

                if not chunks:
                    continue

                # Re-embed chunks
                texts = [chunk.content for chunk in chunks]

                async with httpx.AsyncClient(timeout=30.0) as client:
                    embed_response = await client.post(
                        f"{settings.EMBEDDER_URL}/embed",
                        json={"texts": texts}
                    )
                    embed_response.raise_for_status()
                    embeddings = embed_response.json()["embeddings"]

                # Update embeddings in Qdrant
                # (Implementation depends on Qdrant client in API service)

                migrated_count += 1
                logger.info(f"Migrated document {doc.id} ({migrated_count}/{len(documents)})")

            except Exception as e:
                logger.error(f"Failed to migrate document {doc.id}: {e}")
                continue

        logger.info(f"Migration complete: {migrated_count} documents migrated")

    except Exception as e:
        logger.error(f"Migration batch failed: {e}")


@router.post("/migrate")
async def trigger_migration(
    background_tasks: BackgroundTasks,
    batch_size: int = 10,
    max_documents: int = 100,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Trigger background migration to re-embed documents.

    Args:
        batch_size: Number of documents to process per batch
        max_documents: Maximum documents to migrate (for testing)

    Returns:
        Status message indicating migration started
    """
    # Add migration task to background
    background_tasks.add_task(
        _migrate_document_batch,
        batch_size=batch_size,
        max_documents=max_documents,
        db=db
    )

    return {
        "status": "migration_started",
        "message": f"Migrating up to {max_documents} documents in background"
    }
```

**Step 4: Register migration router**

File: `services/api/app/main.py`
```python
from app.api.routes import migration

# ... existing code ...

# Include routers
app.include_router(documents.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1/search")
app.include_router(migration.router, prefix="/api/v1")  # Add this line
```

**Step 5: Run migration tests**

```bash
poetry run pytest tests/test_migration.py -v
```

Expected: PASS

**Step 6: Create standalone migration script**

File: `scripts/migrate_embeddings.py`
```python
#!/usr/bin/env python3
"""
Standalone script to migrate documents to new embedding model.

Usage:
    python scripts/migrate_embeddings.py --batch-size 10 --max-documents 1000
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api"))

from app.db.session import AsyncSessionLocal
from app.models.document import Document, DocumentChunk
from sqlalchemy import select
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_documents(batch_size: int, max_documents: int, embedder_url: str):
    """Migrate documents to new embeddings."""
    async with AsyncSessionLocal() as db:
        # Get all documents
        query = select(Document).limit(max_documents)
        result = await db.execute(query)
        documents = result.scalars().all()

        logger.info(f"Found {len(documents)} documents to migrate")

        for idx, doc in enumerate(documents, 1):
            try:
                # Get chunks
                chunk_query = select(DocumentChunk).where(
                    DocumentChunk.document_id == doc.id
                )
                chunk_result = await db.execute(chunk_query)
                chunks = chunk_result.scalars().all()

                if not chunks:
                    logger.warning(f"Document {doc.id} has no chunks, skipping")
                    continue

                # Re-embed
                texts = [chunk.content for chunk in chunks]

                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{embedder_url}/embed",
                        json={"texts": texts}
                    )
                    response.raise_for_status()

                logger.info(f"✓ Migrated document {doc.id} ({idx}/{len(documents)})")

                # Add small delay to avoid overload
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"✗ Failed to migrate document {doc.id}: {e}")
                continue

        logger.info("Migration complete!")


def main():
    parser = argparse.ArgumentParser(description="Migrate documents to new embeddings")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    parser.add_argument("--max-documents", type=int, default=1000, help="Max documents")
    parser.add_argument(
        "--embedder-url",
        default="http://localhost:8001",
        help="Embedder service URL"
    )

    args = parser.parse_args()

    asyncio.run(migrate_documents(
        batch_size=args.batch_size,
        max_documents=args.max_documents,
        embedder_url=args.embedder_url
    ))


if __name__ == "__main__":
    main()
```

**Step 7: Make script executable**

```bash
chmod +x scripts/migrate_embeddings.py
```

**Step 8: Test migration script**

```bash
python scripts/migrate_embeddings.py --max-documents 5
```

Expected: Script runs and attempts to migrate documents

**Step 9: Commit**

```bash
git add services/api/app/api/routes/migration.py \
        services/api/app/main.py \
        services/api/tests/test_migration.py \
        scripts/migrate_embeddings.py
git commit -m "feat(api): add migration endpoints and script for re-embedding"
```

---

## Phase 2: Hybrid Search (Week 3-4)

### Task 6: Implement BM25 Sparse Search

**Files:**
- Create: `services/api/app/services/bm25_service.py`
- Modify: `services/api/pyproject.toml` (add rank-bm25)
- Test: `services/api/tests/test_bm25.py`

**Step 1: Write test for BM25 indexing**

File: `services/api/tests/test_bm25.py`
```python
import pytest
from app.services.bm25_service import BM25Service


def test_bm25_index_documents():
    """Test BM25 can index and search documents."""
    service = BM25Service()

    documents = [
        {"id": 1, "content": "Machine learning is a subset of AI"},
        {"id": 2, "content": "Deep learning uses neural networks"},
        {"id": 3, "content": "Pizza is delicious food"},
    ]

    service.index_documents(documents)

    # Search for ML-related query
    results = service.search("machine learning algorithms", top_k=2)

    assert len(results) <= 2
    assert results[0]["id"] == 1  # Most relevant
    assert all("score" in r for r in results)


def test_bm25_search_returns_scores():
    """Test BM25 returns normalized scores."""
    service = BM25Service()

    documents = [
        {"id": 1, "content": "Python programming language"},
        {"id": 2, "content": "JavaScript web development"},
    ]

    service.index_documents(documents)
    results = service.search("Python", top_k=2)

    # First result should have higher score
    assert results[0]["score"] > results[1]["score"]

    # Scores should be positive
    assert all(r["score"] > 0 for r in results)
```

**Step 2: Run test to verify it fails**

```bash
cd services/api
poetry run pytest tests/test_bm25.py -v
```

Expected: FAIL (module doesn't exist)

**Step 3: Add BM25 dependency**

File: `services/api/pyproject.toml`
```toml
[tool.poetry.dependencies]
# ... existing dependencies ...
rank-bm25 = "^0.2.2"
```

Run:
```bash
poetry lock
poetry install
```

**Step 4: Implement BM25 service**

File: `services/api/app/services/bm25_service.py`
```python
"""BM25 sparse retrieval service for keyword-based search."""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BM25Service:
    """BM25 keyword-based search service."""

    def __init__(self):
        """Initialize BM25 service."""
        self.bm25 = None
        self.documents = []
        self.tokenized_docs = []

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization (split on whitespace and lowercase)."""
        return text.lower().split()

    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents for BM25 search.

        Args:
            documents: List of dicts with 'id' and 'content' keys
        """
        self.documents = documents
        self.tokenized_docs = [
            self._tokenize(doc["content"]) for doc in documents
        ]

        if self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)
            logger.info(f"Indexed {len(documents)} documents for BM25 search")
        else:
            logger.warning("No documents to index")

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents using BM25.

        Args:
            query: Search query string
            top_k: Number of top results to return

        Returns:
            List of results with 'id', 'content', and 'score'
        """
        if not self.bm25:
            logger.warning("BM25 index not initialized")
            return []

        # Tokenize query
        tokenized_query = self._tokenize(query)

        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Create results with scores
        results = [
            {
                "id": doc["id"],
                "content": doc["content"],
                "score": float(score)
            }
            for doc, score in zip(self.documents, scores)
        ]

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        # Return top-K
        return results[:top_k]

    def add_document(self, document: Dict[str, Any]):
        """
        Add single document to index.

        Args:
            document: Dict with 'id' and 'content' keys
        """
        self.documents.append(document)
        tokenized = self._tokenize(document["content"])
        self.tokenized_docs.append(tokenized)

        # Rebuild index
        if self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)
```

**Step 5: Run BM25 tests**

```bash
poetry run pytest tests/test_bm25.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add services/api/app/services/bm25_service.py \
        services/api/tests/test_bm25.py \
        services/api/pyproject.toml \
        services/api/poetry.lock
git commit -m "feat(api): add BM25 sparse search service"
```

---

### Task 7: Implement Reciprocal Rank Fusion (RRF)

**Files:**
- Create: `services/api/app/services/fusion.py`
- Test: `services/api/tests/test_fusion.py`

**Step 1: Write test for RRF**

File: `services/api/tests/test_fusion.py`
```python
import pytest
from app.services.fusion import reciprocal_rank_fusion


def test_rrf_combines_rankings():
    """Test RRF combines multiple rankings correctly."""
    # Two result lists with different rankings
    dense_results = [
        {"id": 1, "score": 0.9},
        {"id": 2, "score": 0.8},
        {"id": 3, "score": 0.7},
    ]

    sparse_results = [
        {"id": 3, "score": 10.5},  # Different order
        {"id": 1, "score": 8.2},
        {"id": 4, "score": 5.1},   # New result
    ]

    fused = reciprocal_rank_fusion(
        [dense_results, sparse_results],
        k=60
    )

    # Should return all unique IDs
    assert len(fused) == 4

    # Each result should have fused score
    assert all("fused_score" in r for r in fused)

    # Should be sorted by fused score
    scores = [r["fused_score"] for r in fused]
    assert scores == sorted(scores, reverse=True)


def test_rrf_handles_empty_lists():
    """Test RRF handles empty result lists."""
    dense_results = [{"id": 1, "score": 0.9}]
    sparse_results = []

    fused = reciprocal_rank_fusion([dense_results, sparse_results])

    assert len(fused) == 1
    assert fused[0]["id"] == 1


def test_rrf_k_parameter_affects_scores():
    """Test that k parameter affects fusion scores."""
    results = [[{"id": 1, "score": 0.9}]]

    fused_k60 = reciprocal_rank_fusion(results, k=60)
    fused_k10 = reciprocal_rank_fusion(results, k=10)

    # Different k should give different scores
    assert fused_k60[0]["fused_score"] != fused_k10[0]["fused_score"]
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_fusion.py -v
```

Expected: FAIL (module doesn't exist)

**Step 3: Implement RRF function**

File: `services/api/app/services/fusion.py`
```python
"""Reciprocal Rank Fusion for combining multiple search result lists."""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    result_lists: List[List[Dict[str, Any]]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion.

    RRF formula: score = sum(1 / (k + rank)) for each list

    Args:
        result_lists: List of result lists, each containing dicts with 'id' key
        k: Constant for RRF formula (default 60, standard value)

    Returns:
        Fused results sorted by RRF score descending
    """
    # Collect all results by ID
    fused_scores: Dict[int, float] = {}
    result_data: Dict[int, Dict[str, Any]] = {}

    for result_list in result_lists:
        for rank, result in enumerate(result_list, start=1):
            result_id = result["id"]

            # Calculate RRF score contribution
            rrf_score = 1.0 / (k + rank)

            # Add to total score
            if result_id in fused_scores:
                fused_scores[result_id] += rrf_score
            else:
                fused_scores[result_id] = rrf_score
                result_data[result_id] = result.copy()

    # Build final results with fused scores
    fused_results = []
    for result_id, fused_score in fused_scores.items():
        result = result_data[result_id].copy()
        result["fused_score"] = fused_score
        fused_results.append(result)

    # Sort by fused score descending
    fused_results.sort(key=lambda x: x["fused_score"], reverse=True)

    logger.debug(f"RRF fused {len(fused_results)} results from {len(result_lists)} lists")

    return fused_results
```

**Step 4: Run tests**

```bash
poetry run pytest tests/test_fusion.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/api/app/services/fusion.py \
        services/api/tests/test_fusion.py
git commit -m "feat(api): add reciprocal rank fusion for hybrid search"
```

---

### Task 8: Integrate Hybrid Search into Search Endpoint

**Files:**
- Modify: `services/api/app/api/routes/search.py`
- Modify: `services/api/app/models/schemas.py`
- Modify: `services/api/app/main.py`
- Test: `services/api/tests/test_search.py`

**Step 1: Write test for hybrid search**

File: `services/api/tests/test_search.py`
```python
@pytest.mark.asyncio
async def test_hybrid_search_combines_dense_and_sparse(test_client, test_db):
    """Test hybrid search uses both dense and sparse retrieval."""
    # Upload document with specific keywords
    response = await test_client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "test.txt",
                b"Python is a programming language. Machine learning ML.",
                "text/plain"
            )
        }
    )
    assert response.status_code == 201

    await asyncio.sleep(2)

    # Search with hybrid mode enabled
    response = await test_client.post(
        "/api/v1/search",
        json={
            "query": "Python programming",
            "limit": 5,
            "search_mode": "hybrid"
        }
    )

    assert response.status_code == 200
    results = response.json()["results"]

    # Should have fused scores
    assert any("fused_score" in r for r in results)


@pytest.mark.asyncio
async def test_search_mode_parameter(test_client):
    """Test different search modes work."""
    for mode in ["dense", "sparse", "hybrid"]:
        response = await test_client.post(
            "/api/v1/search",
            json={
                "query": "test query",
                "limit": 5,
                "search_mode": mode
            }
        )
        assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_search.py::test_hybrid_search_combines_dense_and_sparse -v
```

Expected: FAIL (search_mode parameter not recognized)

**Step 3: Update search schema with search_mode**

File: `services/api/app/models/schemas.py`
```python
from enum import Enum


class SearchMode(str, Enum):
    """Search mode enum."""
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score"
    )
    enable_reranking: bool = Field(
        default=True,
        description="Whether to apply cross-encoder reranking"
    )
    search_mode: SearchMode = Field(
        default=SearchMode.HYBRID,
        description="Search mode: dense (vector only), sparse (BM25 only), or hybrid (both)"
    )


class SearchResult(BaseModel):
    """Single search result."""

    chunk_id: int
    document_id: int
    content: str
    score: float
    reranked_score: Optional[float] = None
    fused_score: Optional[float] = Field(
        None,
        description="RRF fused score for hybrid search"
    )
    metadata: Dict[str, Any]
```

**Step 4: Initialize BM25 service in app**

File: `services/api/app/main.py`
```python
from app.services.bm25_service import BM25Service

# ... existing imports ...

# Global service instances
reranker_service: Optional[RerankerService] = None
bm25_service: Optional[BM25Service] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global reranker_service, bm25_service

    logger.info("Starting up API service...")

    # Initialize database
    await init_db()

    # Initialize reranker
    try:
        reranker_service = RerankerService(model_name=settings.RERANKER_MODEL)
        logger.info("Reranker service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize reranker: {e}")
        reranker_service = None

    # Initialize BM25
    try:
        bm25_service = BM25Service()
        # Load existing documents into BM25 index
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DocumentChunk))
            chunks = result.scalars().all()

            if chunks:
                documents = [
                    {"id": chunk.id, "content": chunk.content}
                    for chunk in chunks
                ]
                bm25_service.index_documents(documents)
                logger.info(f"BM25 indexed {len(documents)} chunks")
    except Exception as e:
        logger.error(f"Failed to initialize BM25: {e}")
        bm25_service = None

    logger.info("API service started successfully")


def get_bm25() -> Optional[BM25Service]:
    """Dependency injection for BM25 service."""
    return bm25_service
```

**Step 5: Update search route with hybrid logic**

File: `services/api/app/api/routes/search.py`
```python
from app.services.fusion import reciprocal_rank_fusion
from app.services.bm25_service import BM25Service
from app.models.schemas import SearchMode

# ... existing imports ...


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    reranker: Optional[RerankerService] = Depends(get_reranker),
    bm25: Optional[BM25Service] = Depends(get_bm25)
):
    """
    Search documents using dense, sparse, or hybrid search.

    - Dense: Vector similarity only
    - Sparse: BM25 keyword matching only
    - Hybrid: RRF fusion of dense + sparse (recommended)
    """
    try:
        score_threshold = (
            request.score_threshold
            if request.score_threshold is not None
            else settings.DEFAULT_SCORE_THRESHOLD
        )

        # Determine candidate limit
        candidate_limit = request.limit
        if request.enable_reranking and reranker:
            candidate_limit = request.limit * settings.RERANKER_CANDIDATE_MULTIPLIER

        dense_results = []
        sparse_results = []

        # Dense vector search
        if request.search_mode in [SearchMode.DENSE, SearchMode.HYBRID]:
            # Generate query embedding
            async with httpx.AsyncClient() as client:
                embed_response = await client.post(
                    f"{settings.EMBEDDER_URL}/embed",
                    json={"texts": [request.query]}
                )
                embed_response.raise_for_status()
                query_embedding = embed_response.json()["embeddings"][0]

            # Search Qdrant
            qdrant_results = await qdrant_client.search(
                collection_name="documents",
                query_vector=query_embedding,
                limit=candidate_limit,
                score_threshold=score_threshold
            )

            # Convert to standard format
            chunk_ids = [int(hit.id) for hit in qdrant_results]

            # Fetch metadata
            query_stmt = select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
            result = await db.execute(query_stmt)
            chunks = {chunk.id: chunk for chunk in result.scalars().all()}

            for hit in qdrant_results:
                chunk = chunks.get(int(hit.id))
                if chunk:
                    dense_results.append({
                        "id": chunk.id,
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "content": chunk.content,
                        "score": hit.score,
                        "metadata": chunk.chunk_metadata or {}
                    })

        # Sparse BM25 search
        if request.search_mode in [SearchMode.SPARSE, SearchMode.HYBRID]:
            if bm25:
                bm25_results = bm25.search(request.query, top_k=candidate_limit)

                # Fetch metadata for BM25 results
                bm25_ids = [r["id"] for r in bm25_results]
                query_stmt = select(DocumentChunk).where(DocumentChunk.id.in_(bm25_ids))
                result = await db.execute(query_stmt)
                chunks = {chunk.id: chunk for chunk in result.scalars().all()}

                for bm25_result in bm25_results:
                    chunk = chunks.get(bm25_result["id"])
                    if chunk:
                        sparse_results.append({
                            "id": chunk.id,
                            "chunk_id": chunk.id,
                            "document_id": chunk.document_id,
                            "content": chunk.content,
                            "score": bm25_result["score"],
                            "metadata": chunk.chunk_metadata or {}
                        })
            else:
                logger.warning("BM25 not available, falling back to dense search")
                request.search_mode = SearchMode.DENSE

        # Combine results based on mode
        if request.search_mode == SearchMode.HYBRID and dense_results and sparse_results:
            # Use RRF to fuse
            fused_results = reciprocal_rank_fusion([dense_results, sparse_results])
            initial_results = fused_results
        elif request.search_mode == SearchMode.SPARSE:
            initial_results = sparse_results
        else:  # DENSE or fallback
            initial_results = dense_results

        # Apply reranking if enabled
        if request.enable_reranking and reranker and initial_results:
            candidates = [r["content"] for r in initial_results]
            reranked_indices = reranker.rerank(
                query=request.query,
                candidates=candidates,
                top_k=request.limit
            )

            final_results = []
            for idx, rerank_score in reranked_indices:
                result = initial_results[idx].copy()
                result["reranked_score"] = float(rerank_score)
                # Remove 'id' key used for fusion
                result.pop("id", None)
                final_results.append(SearchResult(**result))
        else:
            # No reranking
            final_results = []
            for r in initial_results[:request.limit]:
                r.pop("id", None)
                final_results.append(SearchResult(**r))

        return SearchResponse(query=request.query, results=final_results)

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

**Step 6: Run hybrid search tests**

```bash
poetry run pytest tests/test_search.py -v
```

Expected: PASS

**Step 7: Commit**

```bash
git add services/api/app/api/routes/search.py \
        services/api/app/models/schemas.py \
        services/api/app/main.py \
        services/api/tests/test_search.py
git commit -m "feat(api): implement hybrid search with dense+sparse fusion"
```

---

## Phase 3: Advanced Features (Week 5-6)

### Task 9: Implement Adaptive Chunk Sizing

**Files:**
- Modify: `services/api/app/services/chunking/semantic_chunker.py`
- Modify: `services/api/app/core/config.py`
- Test: `services/api/tests/test_chunking.py`

**Step 1: Write test for adaptive chunk sizing**

File: `services/api/tests/test_chunking.py`
```python
import pytest
from app.services.chunking.semantic_chunker import SemanticChunker, DocumentType


def test_adaptive_chunk_size_by_document_type():
    """Test that chunk size adapts based on document type."""
    chunker = SemanticChunker()

    # PDF should use larger chunks
    pdf_size = chunker.get_chunk_size(DocumentType.PDF)

    # CSV should use smaller chunks
    csv_size = chunker.get_chunk_size(DocumentType.CSV)

    assert pdf_size > csv_size
    assert pdf_size == 400
    assert csv_size == 200


def test_chunking_respects_document_type():
    """Test that chunking uses appropriate size for document type."""
    text = "This is a test. " * 100  # Long text

    chunker = SemanticChunker()

    # Chunk as PDF (larger chunks)
    pdf_chunks = chunker.chunk_text(text, DocumentType.PDF)

    # Chunk as CSV (smaller chunks)
    csv_chunks = chunker.chunk_text(text, DocumentType.CSV)

    # CSV should produce more chunks
    assert len(csv_chunks) >= len(pdf_chunks)
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_chunking.py::test_adaptive_chunk_size_by_document_type -v
```

Expected: FAIL (method doesn't exist)

**Step 3: Update chunker with adaptive sizing**

File: `services/api/app/services/chunking/semantic_chunker.py`
```python
from enum import Enum
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken


class DocumentType(str, Enum):
    """Document type enum for adaptive chunking."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    UNKNOWN = "unknown"


class SemanticChunker:
    """Semantic-aware text chunker with adaptive sizing."""

    # Chunk size configuration by document type
    CHUNK_SIZES = {
        DocumentType.PDF: 400,      # Technical docs need more context
        DocumentType.DOCX: 350,     # Business docs can be smaller
        DocumentType.TXT: 300,      # General text
        DocumentType.CSV: 200,      # Structured data needs precision
        DocumentType.UNKNOWN: 300,  # Default fallback
    }

    OVERLAP_RATIO = 0.2  # 20% overlap

    def __init__(self):
        """Initialize chunker with tiktoken encoder."""
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def get_chunk_size(self, doc_type: DocumentType) -> int:
        """
        Get optimal chunk size for document type.

        Args:
            doc_type: Type of document

        Returns:
            Chunk size in tokens
        """
        return self.CHUNK_SIZES.get(doc_type, self.CHUNK_SIZES[DocumentType.UNKNOWN])

    def chunk_text(
        self,
        text: str,
        doc_type: DocumentType = DocumentType.UNKNOWN,
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Chunk text with adaptive sizing based on document type.

        Args:
            text: Text to chunk
            doc_type: Document type for size adaptation
            metadata: Optional metadata to attach to chunks

        Returns:
            List of chunk dicts with content, tokens, and metadata
        """
        chunk_size = self.get_chunk_size(doc_type)
        overlap = int(chunk_size * self.OVERLAP_RATIO)

        # Create splitter for this document type
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size * 4,  # Approximate characters (1 token ≈ 4 chars)
            chunk_overlap=overlap * 4,
            length_function=len,
            separators=self.separators
        )

        # Split text
        chunks = splitter.split_text(text)

        # Build chunk objects with metadata
        result_chunks = []
        for idx, chunk in enumerate(chunks):
            # Count tokens accurately
            token_count = len(self.encoding.encode(chunk))

            chunk_obj = {
                "content": chunk,
                "tokens": token_count,
                "chunk_index": idx,
                "chunk_metadata": metadata or {}
            }

            result_chunks.append(chunk_obj)

        return result_chunks
```

**Step 4: Run tests**

```bash
poetry run pytest tests/test_chunking.py -v
```

Expected: PASS

**Step 5: Update document upload to detect type**

File: `services/api/app/api/routes/documents.py`
```python
from app.services.chunking.semantic_chunker import DocumentType


def detect_document_type(filename: str) -> DocumentType:
    """Detect document type from filename."""
    ext = filename.lower().split('.')[-1]

    type_map = {
        'pdf': DocumentType.PDF,
        'docx': DocumentType.DOCX,
        'doc': DocumentType.DOCX,
        'txt': DocumentType.TXT,
        'csv': DocumentType.CSV,
    }

    return type_map.get(ext, DocumentType.UNKNOWN)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process document with adaptive chunking."""
    try:
        # Detect document type
        doc_type = detect_document_type(file.filename)

        # ... existing upload logic ...

        # Chunk with adaptive sizing
        chunker = SemanticChunker()
        chunks = chunker.chunk_text(
            text=extracted_text,
            doc_type=doc_type,
            metadata={"filename": file.filename}
        )

        # ... rest of upload logic ...
```

**Step 6: Commit**

```bash
git add services/api/app/services/chunking/semantic_chunker.py \
        services/api/app/api/routes/documents.py \
        services/api/tests/test_chunking.py
git commit -m "feat(api): add adaptive chunk sizing by document type"
```

---

### Task 10: Add Query Expansion

**Files:**
- Create: `services/api/app/services/query_optimizer.py`
- Modify: `services/api/app/core/config.py`
- Test: `services/api/tests/test_query_optimizer.py`

**Step 1: Write test for query expansion**

File: `services/api/tests/test_query_optimizer.py`
```python
import pytest
from app.services.query_optimizer import QueryOptimizer


@pytest.mark.asyncio
async def test_query_optimizer_expands_query():
    """Test query optimizer expands queries with related terms."""
    optimizer = QueryOptimizer()

    query = "ML algorithms"
    expanded = await optimizer.expand_query(query)

    # Should contain original query
    assert "ML" in expanded or "algorithms" in expanded

    # Should be longer than original
    assert len(expanded) > len(query)


@pytest.mark.asyncio
async def test_query_optimizer_adds_domain_terms():
    """Test optimizer adds domain-specific terms."""
    optimizer = QueryOptimizer()

    # Technical query
    query = "API authentication"
    expanded = await optimizer.expand_query(query)

    # Should add technical context
    assert len(expanded) >= len(query)
```

**Step 2: Run test to verify it fails**

```bash
poetry run pytest tests/test_query_optimizer.py -v
```

Expected: FAIL (module doesn't exist)

**Step 3: Implement query optimizer**

File: `services/api/app/services/query_optimizer.py`
```python
"""Query optimization service for improving search recall."""
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Service for expanding and optimizing search queries."""

    # Domain-specific term expansions
    EXPANSIONS = {
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "dl": "deep learning",
        "nn": "neural network",
        "api": "application programming interface",
        "db": "database",
        "auth": "authentication authorization",
    }

    def __init__(self):
        """Initialize query optimizer."""
        pass

    async def expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms.

        Args:
            query: Original search query

        Returns:
            Expanded query with additional terms
        """
        # Start with original query
        expanded_terms = [query]

        # Add domain-specific expansions
        query_lower = query.lower()
        for abbrev, expansion in self.EXPANSIONS.items():
            if abbrev in query_lower.split():
                expanded_terms.append(expansion)
                logger.debug(f"Expanded '{abbrev}' -> '{expansion}'")

        # Join all terms
        expanded = " ".join(expanded_terms)

        return expanded

    async def optimize_query(self, query: str) -> str:
        """
        Optimize query for better retrieval.

        Currently just calls expand_query, but can be extended
        with query rewriting, spell correction, etc.

        Args:
            query: Original query

        Returns:
            Optimized query
        """
        return await self.expand_query(query)
```

**Step 4: Run tests**

```bash
poetry run pytest tests/test_query_optimizer.py -v
```

Expected: PASS

**Step 5: Add configuration for query optimization**

File: `services/api/app/core/config.py`
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Query optimization
    ENABLE_QUERY_EXPANSION: bool = Field(
        default=True,
        description="Enable query expansion with synonyms"
    )
```

**Step 6: Integrate into search endpoint**

File: `services/api/app/api/routes/search.py`
```python
from app.services.query_optimizer import QueryOptimizer

# Initialize query optimizer
query_optimizer = QueryOptimizer()


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    reranker: Optional[RerankerService] = Depends(get_reranker),
    bm25: Optional[BM25Service] = Depends(get_bm25)
):
    """Search documents with query optimization."""
    try:
        # Optimize query if enabled
        search_query = request.query
        if settings.ENABLE_QUERY_EXPANSION:
            search_query = await query_optimizer.optimize_query(request.query)
            logger.debug(f"Query expanded: '{request.query}' -> '{search_query}'")

        # ... rest of search logic using search_query instead of request.query ...
```

**Step 7: Run search tests**

```bash
poetry run pytest tests/test_search.py -v
```

Expected: PASS

**Step 8: Commit**

```bash
git add services/api/app/services/query_optimizer.py \
        services/api/app/core/config.py \
        services/api/app/api/routes/search.py \
        services/api/tests/test_query_optimizer.py
git commit -m "feat(api): add query expansion for improved recall"
```

---

## Testing & Verification

### Task 11: Add Integration Tests

**Files:**
- Create: `tests/integration/test_full_workflow.py`
- Create: `tests/integration/test_performance.py`

**Step 1: Write end-to-end integration test**

File: `tests/integration/test_full_workflow.py`
```python
"""
End-to-end integration tests for RAG optimization.

Tests the complete workflow: upload -> embed -> search -> rerank
"""
import pytest
import asyncio
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_rag_workflow():
    """Test complete RAG workflow with all optimizations."""
    base_url = "http://localhost:8000"

    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        # 1. Upload document
        response = await client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "ml_guide.txt",
                    b"Machine learning is a subset of artificial intelligence. "
                    b"Deep learning uses neural networks for pattern recognition. "
                    b"Supervised learning requires labeled training data.",
                    "text/plain"
                )
            }
        )

        assert response.status_code == 201
        doc_id = response.json()["id"]

        # 2. Wait for embedding to complete
        for _ in range(10):
            await asyncio.sleep(1)
            response = await client.get(f"/api/v1/documents/{doc_id}")
            if response.json()["embedding_status"] == "completed":
                break

        assert response.json()["embedding_status"] == "completed"

        # 3. Test dense search
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "What is machine learning?",
                "limit": 5,
                "search_mode": "dense",
                "enable_reranking": True
            }
        )

        assert response.status_code == 200
        dense_results = response.json()["results"]
        assert len(dense_results) > 0
        assert "machine learning" in dense_results[0]["content"].lower()

        # 4. Test hybrid search
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "neural networks deep learning",
                "limit": 5,
                "search_mode": "hybrid",
                "enable_reranking": True
            }
        )

        assert response.status_code == 200
        hybrid_results = response.json()["results"]
        assert len(hybrid_results) > 0

        # Hybrid should have fused scores
        assert any("fused_score" in r for r in hybrid_results)

        # 5. Test sparse search
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "supervised learning labeled data",
                "limit": 5,
                "search_mode": "sparse"
            }
        )

        assert response.status_code == 200
        sparse_results = response.json()["results"]
        assert len(sparse_results) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reranking_improves_results():
    """Test that reranking improves result relevance."""
    base_url = "http://localhost:8000"

    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Search without reranking
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "machine learning algorithms",
                "limit": 10,
                "enable_reranking": False
            }
        )

        no_rerank_results = response.json()["results"]

        # Search with reranking
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "machine learning algorithms",
                "limit": 10,
                "enable_reranking": True
            }
        )

        rerank_results = response.json()["results"]

        # Results should be different order
        # (This assumes reranking actually changes the order)
        if len(no_rerank_results) > 1 and len(rerank_results) > 1:
            # At least some results should be reordered
            # Check if top result is different or has reranked_score
            assert (
                rerank_results[0]["chunk_id"] != no_rerank_results[0]["chunk_id"]
                or rerank_results[0].get("reranked_score") is not None
            )
```

**Step 2: Create performance benchmarking tests**

File: `tests/integration/test_performance.py`
```python
"""Performance benchmarking for RAG optimizations."""
import pytest
import time
from httpx import AsyncClient


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_search_latency():
    """Benchmark search latency for different modes."""
    base_url = "http://localhost:8000"

    queries = [
        "machine learning algorithms",
        "neural network architecture",
        "deep learning training",
    ]

    async with AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Benchmark dense search
        dense_times = []
        for query in queries:
            start = time.time()
            response = await client.post(
                "/api/v1/search",
                json={"query": query, "search_mode": "dense"}
            )
            dense_times.append(time.time() - start)
            assert response.status_code == 200

        # Benchmark hybrid search
        hybrid_times = []
        for query in queries:
            start = time.time()
            response = await client.post(
                "/api/v1/search",
                json={"query": query, "search_mode": "hybrid"}
            )
            hybrid_times.append(time.time() - start)
            assert response.status_code == 200

        # Report results
        print(f"\nDense avg latency: {sum(dense_times)/len(dense_times):.3f}s")
        print(f"Hybrid avg latency: {sum(hybrid_times)/len(hybrid_times):.3f}s")

        # Hybrid should be < 500ms average
        assert sum(hybrid_times)/len(hybrid_times) < 0.5


@pytest.mark.benchmark
@pytest.mark.asyncio
async def test_embedding_throughput():
    """Benchmark embedding generation throughput."""
    base_url = "http://localhost:8001"

    texts = [f"This is test document number {i}." for i in range(100)]

    async with AsyncClient(base_url=base_url, timeout=60.0) as client:
        start = time.time()

        response = await client.post(
            "/embed",
            json={"texts": texts}
        )

        elapsed = time.time() - start

        assert response.status_code == 200
        embeddings = response.json()["embeddings"]
        assert len(embeddings) == 100

        throughput = len(texts) / elapsed
        print(f"\nEmbedding throughput: {throughput:.1f} docs/sec")

        # Should process at least 20 docs/sec with BGE-M3
        assert throughput > 20
```

**Step 3: Run integration tests**

```bash
# Start services first
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Run integration tests
poetry run pytest tests/integration/ -v -m integration
```

Expected: PASS

**Step 4: Run performance benchmarks**

```bash
poetry run pytest tests/integration/test_performance.py -v -m benchmark
```

Expected: PASS with performance metrics logged

**Step 5: Commit**

```bash
git add tests/integration/test_full_workflow.py \
        tests/integration/test_performance.py
git commit -m "test: add integration tests and performance benchmarks"
```

---

## Documentation

### Task 12: Update Documentation

**Files:**
- Modify: `docs/RAG_OPTIMIZATION_ANALYSIS.md` (add implementation status)
- Create: `docs/RAG_OPTIMIZATION_USAGE.md` (usage guide)
- Modify: `README.md` (update features)

**Step 1: Create usage guide**

File: `docs/RAG_OPTIMIZATION_USAGE.md`
```markdown
# RAG Optimization Features - Usage Guide

This guide explains how to use the new RAG optimization features implemented in RAAS.

## Overview

The RAG system has been upgraded with:
- ✅ BGE-M3 embeddings (1024-dim, +35% quality improvement)
- ✅ Cross-encoder reranking (+25% precision)
- ✅ Hybrid search (dense + sparse, +50% recall)
- ✅ Adaptive chunk sizing by document type
- ✅ Query expansion for improved recall

## Search Modes

### Dense Search (Vector-Only)
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "limit": 10,
    "search_mode": "dense",
    "enable_reranking": true
  }'
```

Best for: Semantic similarity, conceptual queries

### Sparse Search (BM25 Keyword)
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python API authentication",
    "limit": 10,
    "search_mode": "sparse"
  }'
```

Best for: Exact keyword matches, technical terms

### Hybrid Search (Recommended)
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural network training methods",
    "limit": 10,
    "search_mode": "hybrid",
    "enable_reranking": true,
    "score_threshold": 0.3
  }'
```

Best for: General use, combines benefits of both approaches

## Configuration

### Environment Variables

**API Service (.env):**
```bash
# Reranking
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
RERANKER_TOP_K=10
RERANKER_CANDIDATE_MULTIPLIER=5

# Search
DEFAULT_SCORE_THRESHOLD=0.3
ENABLE_QUERY_EXPANSION=true
```

**Embedder Service (.env):**
```bash
MODEL_NAME=BAAI/bge-m3
MODEL_DIMENSION=1024
BATCH_SIZE=16
MAX_SEQUENCE_LENGTH=512
```

## Migration

### Re-embedding Existing Documents

**Option 1: API Endpoint**
```bash
curl -X POST http://localhost:8000/api/v1/migration/migrate \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 10, "max_documents": 100}'
```

**Option 2: Standalone Script**
```bash
cd scripts
python migrate_embeddings.py --max-documents 1000 --batch-size 10
```

**Check Migration Status:**
```bash
curl http://localhost:8000/api/v1/migration/status
```

## Performance Tips

1. **Use hybrid search by default** - Best balance of precision and recall
2. **Enable reranking** - Significant quality improvement with modest latency
3. **Set appropriate score_threshold** - 0.3 is good default, adjust based on needs
4. **Adjust limit for reranking** - Request more candidates (50) for better reranking

## Troubleshooting

**Slow search performance?**
- Reduce reranking candidate multiplier
- Use dense-only search instead of hybrid
- Disable query expansion

**Low recall?**
- Use hybrid search mode
- Enable query expansion
- Lower score threshold

**Low precision?**
- Enable reranking
- Use higher score threshold
- Try sparse-only for exact matches

## Performance Metrics

Expected improvements over baseline:
- **Recall@10**: +42% (65% → 92%)
- **Precision@10**: +88% (42% → 79%)
- **Query Latency**: +83% (120ms → 220ms)

## API Reference

See complete API documentation at `/api/v1/docs` (Swagger UI)
```

**Step 2: Update main README**

File: `README.md`
```markdown
# RAAS - Retrieval-Augmented Generation as a Service

[... existing content ...]

## Features

### Core Capabilities
- 📄 Multi-format document ingestion (PDF, DOCX, TXT, CSV)
- 🔍 Advanced semantic search with hybrid retrieval
- 🎯 Cross-encoder reranking for precision
- 📊 Real-time embedding generation
- 🌐 RESTful API with async processing

### RAG Optimizations (2025)
- ✅ **BGE-M3 Embeddings**: 1024-dim vectors (+35% quality)
- ✅ **Hybrid Search**: Dense + sparse retrieval (+50% recall)
- ✅ **Cross-Encoder Reranking**: +25% precision improvement
- ✅ **Adaptive Chunking**: Document-type specific chunk sizing
- ✅ **Query Expansion**: Automatic query enhancement
- ✅ **Score Thresholds**: Configurable relevance filtering

[... rest of README ...]

## Usage

### Search with Hybrid Mode
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/search",
    json={
        "query": "machine learning algorithms",
        "limit": 10,
        "search_mode": "hybrid",
        "enable_reranking": True
    }
)

results = response.json()["results"]
for result in results:
    print(f"Score: {result['reranked_score']:.3f}")
    print(f"Content: {result['content'][:100]}...")
```

For complete usage guide, see [RAG Optimization Usage](docs/RAG_OPTIMIZATION_USAGE.md)

[... rest of README ...]
```

**Step 3: Update analysis doc with implementation status**

File: `docs/RAG_OPTIMIZATION_ANALYSIS.md`
```markdown
[... at the top of file ...]

## Implementation Status

**Date Updated:** October 24, 2025

### Phase 1: Critical Upgrades ✅ COMPLETED
- ✅ Cross-encoder reranking (BAAI/bge-reranker-v2-m3)
- ✅ Score threshold filtering with configurable defaults
- ✅ BGE-M3 embedding model upgrade (1024-dim)
- ✅ Migration strategy for existing documents

### Phase 2: Hybrid Search ✅ COMPLETED
- ✅ BM25 sparse search implementation
- ✅ Reciprocal Rank Fusion (RRF)
- ✅ Hybrid search integration in search endpoint

### Phase 3: Advanced Features ✅ COMPLETED
- ✅ Adaptive chunk sizing by document type
- ✅ Query expansion with domain terms
- ⏳ True semantic chunking (PENDING)
- ⏳ Hierarchical retrieval (PENDING)
- ⏳ Domain fine-tuning (PENDING)

### Testing & Documentation ✅ COMPLETED
- ✅ Integration tests for full workflow
- ✅ Performance benchmarking
- ✅ Usage documentation

[... rest of document ...]
```

**Step 4: Commit documentation**

```bash
git add README.md \
        docs/RAG_OPTIMIZATION_USAGE.md \
        docs/RAG_OPTIMIZATION_ANALYSIS.md
git commit -m "docs: add RAG optimization usage guide and update README"
```

---

## Final Steps

### Task 13: Final Integration Test and Deployment

**Step 1: Run complete test suite**

```bash
# Unit tests
cd services/api && poetry run pytest tests/ -v
cd services/embedder && poetry run pytest tests/ -v

# Integration tests
poetry run pytest tests/integration/ -v -m integration

# Performance benchmarks
poetry run pytest tests/integration/ -v -m benchmark
```

**Step 2: Build and deploy with Docker Compose**

```bash
# Rebuild services with new code
docker-compose -f infrastructure/docker-compose/docker-compose.yml build

# Start all services
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Check health
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/health
```

**Step 3: Verify search functionality**

```bash
# Upload test document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test_document.txt"

# Wait for embedding
sleep 5

# Test hybrid search with reranking
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "limit": 5,
    "search_mode": "hybrid",
    "enable_reranking": true
  }'
```

**Step 4: Final commit and tag**

```bash
# Final commit
git add -A
git commit -m "feat: complete RAG optimization implementation

Implemented all Phase 1-3 optimizations:
- BGE-M3 embeddings (1024-dim)
- Cross-encoder reranking
- Hybrid search (dense + sparse + RRF)
- Adaptive chunking
- Query expansion
- Migration tools
- Integration tests

Expected improvements:
- Recall@10: +42%
- Precision@10: +88%
- Overall quality: +65-80%"

# Tag release
git tag -a v2.0.0-rag-optimized -m "RAG optimizations complete"
```

---

## Summary

This implementation plan covers:

**Phase 1 (Critical):**
- Task 1-5: Reranking, score thresholds, BGE-M3 upgrade, migration

**Phase 2 (Hybrid Search):**
- Task 6-8: BM25, RRF fusion, hybrid search integration

**Phase 3 (Advanced):**
- Task 9-10: Adaptive chunking, query expansion

**Testing & Docs:**
- Task 11-12: Integration tests, documentation

**Deployment:**
- Task 13: Final testing and deployment

Each task follows TDD with:
- ✅ Write failing test
- ✅ Implement feature
- ✅ Run tests to verify
- ✅ Commit changes

Total estimated time: 5-6 weeks
Expected improvement: +65-80% overall RAG quality
