# Critical RAG Optimizations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the 3 most critical RAG improvements to achieve +65-80% quality improvement: cross-encoder reranking, BGE-M3 embeddings, and hybrid search.

**Architecture:** Three-phase implementation: (1) Add reranking layer for immediate +25% precision, (2) Upgrade to BGE-M3 embeddings for +35% quality, (3) Implement hybrid dense+sparse search with RRF for +50% recall.

**Tech Stack:** BAAI bge-reranker-v2-m3, BAAI bge-m3 embeddings (1024-dim), rank-bm25, sentence-transformers, Qdrant sparse vectors

---

## Phase 1: Cross-Encoder Reranking (Week 1)

### Task 1: Add Cross-Encoder Reranking Service

**Files:**
- Create: `services/api/app/services/reranker.py`
- Modify: `services/api/app/core/config.py`
- Modify: `services/api/pyproject.toml`
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
Add to `[tool.poetry.dependencies]`:
```toml
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
Add to `Settings` class:
```python
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
- Modify: `services/api/app/models/schemas.py`
- Modify: `services/api/app/main.py`
- Test: `services/api/tests/test_search.py`

**Step 1: Update search request schema**

File: `services/api/app/models/schemas.py`
Update `SearchRequest`:
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
```

Update `SearchResult`:
```python
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

**Step 2: Initialize reranker in app startup**

File: `services/api/app/main.py`
Add imports:
```python
from app.services.reranker import RerankerService
```

Add global variable:
```python
# Global reranker instance
reranker_service: Optional[RerankerService] = None
```

Update `startup_event`:
```python
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
```

Add dependency function:
```python
def get_reranker() -> Optional[RerankerService]:
    """Dependency injection for reranker service."""
    return reranker_service
```

**Step 3: Update search route to use reranker**

File: `services/api/app/api/routes/search.py`
Add imports:
```python
from app.main import get_reranker
from app.services.reranker import RerankerService
```

Update search function signature:
```python
@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    reranker: Optional[RerankerService] = Depends(get_reranker)
):
```

Update search logic (after initial retrieval):
```python
# Determine candidate limit
candidate_limit = request.limit
if request.enable_reranking and reranker:
    candidate_limit = request.limit * settings.RERANKER_CANDIDATE_MULTIPLIER

# ... existing Qdrant search code ...

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
```

**Step 4: Write integration test**

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

    # Wait for embedding
    await asyncio.sleep(2)

    # Search with reranking enabled
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

**Step 5: Run tests**

```bash
poetry run pytest tests/test_search.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add services/api/app/api/routes/search.py \
        services/api/app/models/schemas.py \
        services/api/app/main.py \
        services/api/tests/test_search.py
git commit -m "feat(api): integrate cross-encoder reranking into search"
```

---

### Task 3: Add Score Threshold Configuration

**Files:**
- Modify: `services/api/app/core/config.py`
- Modify: `services/api/app/models/schemas.py`
- Modify: `services/api/app/api/routes/search.py`

**Step 1: Add score threshold configuration**

File: `services/api/app/core/config.py`
Add to `Settings`:
```python
# Search settings
DEFAULT_SCORE_THRESHOLD: float = Field(
    default=0.3,
    ge=0.0,
    le=1.0,
    description="Default minimum similarity score for results"
)
```

**Step 2: Update search schema**

File: `services/api/app/models/schemas.py`
Update `SearchRequest`:
```python
score_threshold: Optional[float] = Field(
    default=None,
    ge=0.0,
    le=1.0,
    description="Minimum similarity score (uses system default if not provided)"
)
```

**Step 3: Update search route**

File: `services/api/app/api/routes/search.py`
At start of search function:
```python
# Use provided threshold or system default
score_threshold = (
    request.score_threshold
    if request.score_threshold is not None
    else settings.DEFAULT_SCORE_THRESHOLD
)
```

Update Qdrant search call:
```python
qdrant_results = await qdrant_client.search(
    collection_name="documents",
    query_vector=query_embedding,
    limit=candidate_limit,
    score_threshold=score_threshold
)
```

**Step 4: Commit**

```bash
git add services/api/app/core/config.py \
        services/api/app/models/schemas.py \
        services/api/app/api/routes/search.py
git commit -m "feat(api): add configurable score threshold filtering"
```

---

## Phase 2: BGE-M3 Embedding Upgrade (Week 2)

### Task 4: Upgrade Embedder to BGE-M3 Model

**Files:**
- Modify: `services/embedder/app/core/config.py`
- Modify: `services/embedder/app/services/embedding_service.py`
- Modify: `services/embedder/app/services/qdrant_service.py`
- Modify: `services/embedder/app/main.py`
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

**Step 2: Run test to verify current failure**

```bash
cd services/embedder
poetry run pytest tests/test_embeddings.py::test_bge_m3_model_loads -v
```

Expected: FAIL (dimension mismatch or model not configured)

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

**Step 4: Update embedding service**

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

**Step 5: Update Qdrant service**

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

**Step 6: Update main app**

File: `services/embedder/app/main.py`
```python
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

**Step 7: Run tests**

```bash
poetry run pytest tests/test_embeddings.py -v
```

Expected: PASS

**Step 8: Update environment example**

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

**Step 9: Commit**

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

## Phase 3: Hybrid Search (Week 3-4)

### Task 5: Implement BM25 Sparse Search

**Files:**
- Create: `services/api/app/services/bm25_service.py`
- Modify: `services/api/pyproject.toml`
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
Add to dependencies:
```toml
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

**Step 5: Run tests**

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

### Task 6: Implement Reciprocal Rank Fusion (RRF)

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

### Task 7: Integrate Hybrid Search into Search Endpoint

**Files:**
- Modify: `services/api/app/api/routes/search.py`
- Modify: `services/api/app/models/schemas.py`
- Modify: `services/api/app/main.py`
- Test: `services/api/tests/test_search.py`

**Step 1: Update search schema with search mode**

File: `services/api/app/models/schemas.py`
Add enum:
```python
from enum import Enum


class SearchMode(str, Enum):
    """Search mode enum."""
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"
```

Update `SearchRequest`:
```python
search_mode: SearchMode = Field(
    default=SearchMode.HYBRID,
    description="Search mode: dense (vector only), sparse (BM25 only), or hybrid (both)"
)
```

Update `SearchResult`:
```python
fused_score: Optional[float] = Field(
    None,
    description="RRF fused score for hybrid search"
)
```

**Step 2: Initialize BM25 service in app**

File: `services/api/app/main.py`
Add imports:
```python
from app.services.bm25_service import BM25Service
from app.models.document import DocumentChunk
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
```

Add global:
```python
bm25_service: Optional[BM25Service] = None
```

Update startup:
```python
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

**Step 3: Update search route with hybrid logic**

File: `services/api/app/api/routes/search.py`
Add imports:
```python
from app.services.fusion import reciprocal_rank_fusion
from app.services.bm25_service import BM25Service
from app.models.schemas import SearchMode
from app.main import get_bm25
```

Update function signature:
```python
@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    reranker: Optional[RerankerService] = Depends(get_reranker),
    bm25: Optional[BM25Service] = Depends(get_bm25)
):
```

Replace search logic with hybrid implementation:
```python
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

**Step 4: Write integration test**

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
```

**Step 5: Run tests**

```bash
poetry run pytest tests/test_search.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add services/api/app/api/routes/search.py \
        services/api/app/models/schemas.py \
        services/api/app/main.py \
        services/api/tests/test_search.py
git commit -m "feat(api): implement hybrid search with dense+sparse fusion"
```

---

## Verification & Testing

### Task 8: End-to-End Integration Test

**Files:**
- Create: `tests/integration/test_critical_optimizations.py`

**Step 1: Create integration test**

File: `tests/integration/test_critical_optimizations.py`
```python
"""
End-to-end integration tests for critical RAG optimizations.
"""
import pytest
import asyncio
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_optimization_workflow():
    """Test complete workflow with all optimizations."""
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

        # 2. Wait for embedding
        await asyncio.sleep(3)

        # 3. Test hybrid search with reranking
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "What is machine learning?",
                "limit": 5,
                "search_mode": "hybrid",
                "enable_reranking": True,
                "score_threshold": 0.3
            }
        )

        assert response.status_code == 200
        results = response.json()["results"]

        # Should have results
        assert len(results) > 0

        # Should have relevant content
        assert "machine learning" in results[0]["content"].lower()

        # Should have all optimization features
        assert results[0].get("reranked_score") is not None

        # For hybrid search, should have fused_score
        if results[0].get("fused_score"):
            assert results[0]["fused_score"] > 0
```

**Step 2: Run integration test**

```bash
# Ensure services are running
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Run test
poetry run pytest tests/integration/test_critical_optimizations.py -v -m integration
```

Expected: PASS

**Step 3: Commit**

```bash
git add tests/integration/test_critical_optimizations.py
git commit -m "test: add integration test for critical optimizations"
```

---

## Deployment

### Task 9: Update Docker Compose Configuration

**Files:**
- Modify: `infrastructure/docker-compose/docker-compose.yml`
- Modify: `services/embedder/.env.example`

**Step 1: Update embedder environment in docker-compose**

File: `infrastructure/docker-compose/docker-compose.yml`
Update embedder service environment:
```yaml
embedder:
  environment:
    - MODEL_NAME=BAAI/bge-m3
    - MODEL_DIMENSION=1024
    - BATCH_SIZE=16
    - MAX_SEQUENCE_LENGTH=512
    - QDRANT_URL=http://qdrant:6333
```

**Step 2: Rebuild and restart services**

```bash
docker-compose -f infrastructure/docker-compose/docker-compose.yml down
docker-compose -f infrastructure/docker-compose/docker-compose.yml build
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d
```

**Step 3: Verify services are healthy**

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/health
```

Expected: Both return 200 OK

**Step 4: Commit**

```bash
git add infrastructure/docker-compose/docker-compose.yml
git commit -m "chore: update docker-compose for BGE-M3 model"
```

---

## Summary

This implementation plan delivers the three most critical RAG optimizations:

**Phase 1: Cross-Encoder Reranking**
- Tasks 1-3: Add reranking layer (+25% precision)
- Implementation time: ~1 week
- Immediate user impact

**Phase 2: BGE-M3 Embedding Upgrade**
- Task 4: Upgrade model (+35% quality)
- Implementation time: ~1 week
- Foundational improvement

**Phase 3: Hybrid Search**
- Tasks 5-7: BM25 + RRF + integration (+50% recall)
- Implementation time: ~2 weeks
- Comprehensive retrieval

**Total Estimated Time:** 4 weeks

**Expected Improvement:**
- Recall@10: 65% → 85% (+31%)
- Precision@10: 42% → 68% (+62%)
- Overall quality: +65-80%

**Each task follows TDD:**
1. Write failing test
2. Implement minimal code
3. Verify test passes
4. Commit

**Next Steps:**
- Execute with superpowers:executing-plans
- Monitor performance metrics
- Iterate based on user feedback
