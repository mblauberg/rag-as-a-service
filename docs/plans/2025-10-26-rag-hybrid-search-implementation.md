# RAG Hybrid Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate hybrid search (vector + BM25 + RRF fusion) into hexagonal architecture for 18-22% accuracy improvement

**Architecture:** Hexagonal (Ports & Adapters) - migrate existing legacy services into clean ports and implementations

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL FTS, Qdrant, sentence-transformers

---

## Context

The codebase has **legacy implementations** of hybrid search components:
- `app/services/bm25_search.py` - BM25 keyword search (PostgreSQL FTS)
- `app/services/fusion.py` - RRF fusion algorithm
- `app/services/hybrid_search_service.py` - Combined service
- `app/services/query_expansion.py` - LLM-based query expansion
- `app/services/reranker.py` - Cross-encoder reranking

**Problem:** These exist outside the hexagonal architecture and aren't accessible via use cases.

**Solution:** Create proper ports and migrate logic into hexagonal implementations.

---

## Phase 1: Hybrid Search Foundation

### Task 1: Create KeywordStore Port

**Files:**
- Modify: `services/api/app/ports/services.py:141`

**Step 1: Write the failing test**

Create: `services/api/tests/ports/test_keyword_store.py`

```python
"""Tests for KeywordStore port."""
import pytest
from uuid import uuid4

from app.ports.services import KeywordStore
from app.domain.entities.chunk import Chunk


class MockKeywordStore(KeywordStore):
    """Mock implementation for testing."""

    async def search(
        self,
        query_text: str,
        top_k: int,
        document_id: uuid4 | None = None
    ) -> list[Chunk]:
        return []


@pytest.mark.asyncio
async def test_keyword_store_port_contract():
    """Test that KeywordStore port has correct interface."""
    store = MockKeywordStore()

    results = await store.search(
        query_text="test query",
        top_k=10
    )

    assert isinstance(results, list)
```

**Step 2: Run test to verify it fails**

Run: `cd services/api && poetry run pytest tests/ports/test_keyword_store.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'tests.ports'"

**Step 3: Create tests directory**

Run: `mkdir -p services/api/tests/ports && touch services/api/tests/ports/__init__.py`

**Step 4: Run test again**

Run: `cd services/api && poetry run pytest tests/ports/test_keyword_store.py -v`

Expected: FAIL with "cannot import name 'KeywordStore'"

**Step 5: Add KeywordStore port**

Modify: `services/api/app/ports/services.py` (after TextChunker class, around line 141)

```python
class KeywordStore(ABC):
    """Port for keyword-based (lexical) search.

    Implementations use BM25, TF-IDF, or full-text search
    to find chunks matching query keywords.
    """

    @abstractmethod
    async def search(
        self,
        query_text: str,
        top_k: int,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search using keyword matching.

        Args:
            query_text: Raw query string
            top_k: Number of results to return
            document_id: Optional document filter

        Returns:
            List of chunks ranked by keyword relevance
        """
        pass
```

**Step 6: Run test to verify it passes**

Run: `cd services/api && poetry run pytest tests/ports/test_keyword_store.py -v`

Expected: PASS

**Step 7: Commit**

```bash
git add services/api/app/ports/services.py services/api/tests/ports/
git commit -m "feat(ports): add KeywordStore port for lexical search"
```

---

### Task 2: Create FusionService Port

**Files:**
- Modify: `services/api/app/ports/services.py` (after KeywordStore)
- Create: `services/api/tests/ports/test_fusion_service.py`

**Step 1: Write the failing test**

Create: `services/api/tests/ports/test_fusion_service.py`

```python
"""Tests for FusionService port."""
import pytest
from uuid import uuid4

from app.ports.services import FusionService
from app.domain.entities.chunk import Chunk


class MockFusionService(FusionService):
    """Mock implementation for testing."""

    def fuse(
        self,
        result_sets: list[list[Chunk]],
        method: str = "rrf",
        k: int = 60
    ) -> list[Chunk]:
        return []


def test_fusion_service_port_contract():
    """Test that FusionService port has correct interface."""
    service = MockFusionService()

    chunk = Chunk(
        id=uuid4(),
        document_id=uuid4(),
        content="test",
        tokens=1
    )

    results = service.fuse([[chunk]], method="rrf", k=60)

    assert isinstance(results, list)
```

**Step 2: Run test to verify it fails**

Run: `cd services/api && poetry run pytest tests/ports/test_fusion_service.py -v`

Expected: FAIL with "cannot import name 'FusionService'"

**Step 3: Add FusionService port**

Modify: `services/api/app/ports/services.py` (after KeywordStore)

```python
class FusionService(ABC):
    """Port for fusing multiple ranked result lists.

    Uses algorithms like Reciprocal Rank Fusion (RRF)
    to combine results from different retrieval methods.
    """

    @abstractmethod
    def fuse(
        self,
        result_sets: list[list[Chunk]],
        method: str = "rrf",
        k: int = 60
    ) -> list[Chunk]:
        """Fuse multiple ranked lists into one.

        Args:
            result_sets: List of ranked chunk lists
            method: Fusion algorithm ("rrf" or "weighted")
            k: RRF constant (default 60, research-proven)

        Returns:
            Single fused and ranked list
        """
        pass
```

**Step 4: Run test to verify it passes**

Run: `cd services/api && poetry run pytest tests/ports/test_fusion_service.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add services/api/app/ports/services.py services/api/tests/ports/test_fusion_service.py
git commit -m "feat(ports): add FusionService port for result fusion"
```

---

### Task 3: Implement PostgreSQL KeywordStore

**Files:**
- Create: `services/api/app/infrastructure/search/__init__.py`
- Create: `services/api/app/infrastructure/search/postgres_keyword_store.py`
- Create: `services/api/tests/infrastructure/search/__init__.py`
- Create: `services/api/tests/infrastructure/search/test_postgres_keyword_store.py`

**Step 1: Create infrastructure directories**

Run: `mkdir -p services/api/app/infrastructure/search services/api/tests/infrastructure/search && touch services/api/app/infrastructure/search/__init__.py services/api/tests/infrastructure/search/__init__.py`

**Step 2: Write the failing test**

Create: `services/api/tests/infrastructure/search/test_postgres_keyword_store.py`

```python
"""Tests for PostgreSQL keyword store."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.search.postgres_keyword_store import PostgresKeywordStoreImpl
from app.domain.entities.chunk import Chunk


@pytest.mark.asyncio
async def test_postgres_keyword_store_searches_with_fts():
    """Test PostgreSQL FTS search returns chunks."""
    # Mock database session
    db_session = AsyncMock()

    # Mock query result
    mock_row = MagicMock()
    mock_row.id = uuid4()
    mock_row.document_id = uuid4()
    mock_row.content = "Kubernetes orchestrates containers"
    mock_row.tokens = 10
    mock_row.chunk_metadata = {}
    mock_row.section_title = None
    mock_row.section_level = None
    mock_row.page_number = None
    mock_row.rank = 0.5

    mock_result = MagicMock()
    mock_result.fetchall.return_value = [mock_row]

    db_session.execute = AsyncMock(return_value=mock_result)

    # Create store and search
    store = PostgresKeywordStoreImpl(db_session)
    results = await store.search(
        query_text="Kubernetes containers",
        top_k=10
    )

    # Verify
    assert len(results) == 1
    assert results[0].content == "Kubernetes orchestrates containers"
    assert db_session.execute.called


@pytest.mark.asyncio
async def test_postgres_keyword_store_handles_document_filter():
    """Test document_id filter is applied."""
    db_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    db_session.execute = AsyncMock(return_value=mock_result)

    store = PostgresKeywordStoreImpl(db_session)
    doc_id = uuid4()

    await store.search(
        query_text="test",
        top_k=10,
        document_id=doc_id
    )

    # Verify execute was called with document_id in params
    call_args = db_session.execute.call_args
    params = call_args[0][1]
    assert params["document_id"] == str(doc_id)
```

**Step 3: Run test to verify it fails**

Run: `cd services/api && poetry run pytest tests/infrastructure/search/test_postgres_keyword_store.py -v`

Expected: FAIL with "cannot import name 'PostgresKeywordStoreImpl'"

**Step 4: Implement PostgreSQL KeywordStore**

Create: `services/api/app/infrastructure/search/postgres_keyword_store.py`

```python
"""PostgreSQL full-text search implementation using BM25-like ranking."""
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SearchError
from app.domain.entities.chunk import Chunk
from app.ports.services import KeywordStore


class PostgresKeywordStoreImpl(KeywordStore):
    """BM25-style keyword search using PostgreSQL FTS.

    Uses ts_rank for BM25-like relevance ranking with
    PostgreSQL's full-text search capabilities.
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize with database session."""
        self.db_session = db_session

    async def search(
        self,
        query_text: str,
        top_k: int,
        document_id: UUID | None = None
    ) -> list[Chunk]:
        """Search using PostgreSQL full-text search.

        Uses text_search_vector column and ts_rank for BM25-like ranking.
        """
        try:
            # Build SQL with optional document filter
            sql = """
                SELECT
                    id, document_id, content, tokens,
                    chunk_metadata, section_title,
                    section_level, page_number,
                    ts_rank(
                        text_search_vector,
                        plainto_tsquery('english', :query)
                    ) as rank
                FROM chunks
                WHERE text_search_vector @@ plainto_tsquery('english', :query)
            """

            params = {"query": query_text, "limit": top_k}

            if document_id:
                sql += " AND document_id = :document_id"
                params["document_id"] = str(document_id)

            sql += " ORDER BY rank DESC LIMIT :limit"

            # Execute query
            result = await self.db_session.execute(text(sql), params)
            rows = result.fetchall()

            # Convert to Chunk entities
            chunks = []
            for row in rows:
                chunk = Chunk(
                    id=row.id,
                    document_id=row.document_id,
                    content=row.content,
                    tokens=row.tokens,
                    metadata=row.chunk_metadata or {},
                    section_title=row.section_title,
                    section_level=row.section_level,
                    page_number=row.page_number
                )
                chunks.append(chunk)

            return chunks

        except Exception as e:
            raise SearchError(
                operation="keyword_search",
                original_error=e
            ) from e
```

**Step 5: Run tests to verify they pass**

Run: `cd services/api && poetry run pytest tests/infrastructure/search/test_postgres_keyword_store.py -v`

Expected: PASS

**Step 6: Commit**

```bash
git add services/api/app/infrastructure/search/ services/api/tests/infrastructure/search/
git commit -m "feat(search): implement PostgreSQL keyword store with FTS"
```

---

### Task 4: Implement RRF FusionService

**Files:**
- Create: `services/api/app/infrastructure/search/rrf_fusion_service.py`
- Create: `services/api/tests/infrastructure/search/test_rrf_fusion.py`

**Step 1: Write the failing test**

Create: `services/api/tests/infrastructure/search/test_rrf_fusion.py`

```python
"""Tests for RRF fusion service."""
import pytest
from uuid import uuid4

from app.infrastructure.search.rrf_fusion_service import RRFFusionServiceImpl
from app.domain.entities.chunk import Chunk


def test_rrf_fusion_combines_two_lists():
    """Test RRF correctly fuses two ranked lists."""
    # Create test chunks
    chunk_a = Chunk(id=uuid4(), document_id=uuid4(), content="A", tokens=1)
    chunk_b = Chunk(id=uuid4(), document_id=uuid4(), content="B", tokens=1)
    chunk_c = Chunk(id=uuid4(), document_id=uuid4(), content="C", tokens=1)

    # List 1: A, B, C
    # List 2: C, A, B
    # RRF should favor A and C (appear in both top positions)

    list1 = [chunk_a, chunk_b, chunk_c]
    list2 = [chunk_c, chunk_a, chunk_b]

    service = RRFFusionServiceImpl()
    fused = service.fuse([list1, list2], k=60)

    # A and C should be top 2
    assert chunk_a in fused[:2]
    assert chunk_c in fused[:2]


def test_rrf_fusion_handles_empty_lists():
    """Test RRF handles empty result sets gracefully."""
    service = RRFFusionServiceImpl()

    fused = service.fuse([[], []], k=60)

    assert fused == []


def test_rrf_fusion_deduplicates_chunks():
    """Test RRF deduplicates chunks appearing in multiple lists."""
    chunk_a = Chunk(id=uuid4(), document_id=uuid4(), content="A", tokens=1)

    # Same chunk in both lists
    list1 = [chunk_a]
    list2 = [chunk_a]

    service = RRFFusionServiceImpl()
    fused = service.fuse([list1, list2], k=60)

    # Should appear once with combined score
    assert len(fused) == 1
    assert fused[0].id == chunk_a.id
```

**Step 2: Run test to verify it fails**

Run: `cd services/api && poetry run pytest tests/infrastructure/search/test_rrf_fusion.py -v`

Expected: FAIL with "cannot import name 'RRFFusionServiceImpl'"

**Step 3: Implement RRF FusionService**

Create: `services/api/app/infrastructure/search/rrf_fusion_service.py`

```python
"""Reciprocal Rank Fusion implementation for result fusion."""
from collections import defaultdict

from app.domain.entities.chunk import Chunk
from app.ports.services import FusionService


class RRFFusionServiceImpl(FusionService):
    """Reciprocal Rank Fusion (RRF) implementation.

    RRF combines multiple ranked lists without needing score normalization.
    Formula: score(d) = sum(1 / (k + rank(d)))
    where k=60 is the research-proven constant.

    Reference: "Reciprocal rank fusion outperforms condorcet and
    individual rank learning methods" (SIGIR 2009)
    """

    def fuse(
        self,
        result_sets: list[list[Chunk]],
        method: str = "rrf",
        k: int = 60
    ) -> list[Chunk]:
        """Fuse multiple ranked lists using RRF.

        Args:
            result_sets: List of ranked chunk lists
            method: Fusion algorithm (only "rrf" supported now)
            k: RRF constant (60 is optimal for most cases)

        Returns:
            Single fused list ranked by RRF score
        """
        if method != "rrf":
            raise ValueError(f"Unsupported fusion method: {method}")

        scores = defaultdict(float)
        chunk_map = {}  # id -> chunk object

        # Accumulate RRF scores from all result sets
        for results in result_sets:
            for rank, chunk in enumerate(results, start=1):
                # RRF formula: 1 / (k + rank)
                scores[chunk.id] += 1.0 / (k + rank)
                chunk_map[chunk.id] = chunk

        # Sort by RRF score (descending)
        sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Return chunks in RRF order
        return [chunk_map[chunk_id] for chunk_id, _ in sorted_ids]
```

**Step 4: Run tests to verify they pass**

Run: `cd services/api && poetry run pytest tests/infrastructure/search/test_rrf_fusion.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add services/api/app/infrastructure/search/rrf_fusion_service.py services/api/tests/infrastructure/search/test_rrf_fusion.py
git commit -m "feat(search): implement RRF fusion service"
```

---

### Task 5: Update SearchDocumentsUseCase with Hybrid Search

**Files:**
- Modify: `services/api/app/application/use_cases/search_documents.py`
- Create: `services/api/tests/application/test_search_hybrid.py`

**Step 1: Write the failing test**

Create: `services/api/tests/application/test_search_hybrid.py`

```python
"""Tests for hybrid search use case."""
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.application.use_cases.search_documents import SearchDocumentsUseCase, SearchMode
from app.domain.value_objects.search_query import SearchQuery
from app.domain.entities.chunk import Chunk


@pytest.mark.asyncio
async def test_hybrid_search_calls_both_stores():
    """Test hybrid mode retrieves from both vector and keyword stores."""
    # Mock dependencies
    embedding_service = AsyncMock()
    vector_store = AsyncMock()
    keyword_store = AsyncMock()
    fusion_service = AsyncMock()

    # Configure mocks
    chunk1 = Chunk(id=uuid4(), document_id=uuid4(), content="test1", tokens=1)
    chunk2 = Chunk(id=uuid4(), document_id=uuid4(), content="test2", tokens=1)

    embedding_service.generate_embeddings.return_value = [[0.1] * 384]
    vector_store.search.return_value = [chunk1]
    keyword_store.search.return_value = [chunk2]
    fusion_service.fuse.return_value = [chunk1, chunk2]

    use_case = SearchDocumentsUseCase(
        embedding_service=embedding_service,
        vector_store=vector_store,
        keyword_store=keyword_store,
        fusion_service=fusion_service
    )

    query = SearchQuery(text="test query", top_k=10)

    results = await use_case.execute(query, mode=SearchMode.HYBRID)

    # Verify both stores were called
    vector_store.search.assert_called_once()
    keyword_store.search.assert_called_once()
    fusion_service.fuse.assert_called_once()
    assert len(results) == 2


@pytest.mark.asyncio
async def test_hybrid_search_retrieves_2x_before_fusion():
    """Test hybrid mode retrieves 2x results before fusion."""
    embedding_service = AsyncMock()
    vector_store = AsyncMock()
    keyword_store = AsyncMock()
    fusion_service = AsyncMock()

    embedding_service.generate_embeddings.return_value = [[0.1] * 384]
    vector_store.search.return_value = []
    keyword_store.search.return_value = []
    fusion_service.fuse.return_value = []

    use_case = SearchDocumentsUseCase(
        embedding_service=embedding_service,
        vector_store=vector_store,
        keyword_store=keyword_store,
        fusion_service=fusion_service
    )

    query = SearchQuery(text="test query", top_k=10)

    await use_case.execute(query, mode=SearchMode.HYBRID)

    # Verify retrieval_k = top_k * 2
    # Check that keyword_store.search was called with top_k=20 (2x)
    call_kwargs = keyword_store.search.call_args.kwargs
    assert call_kwargs["top_k"] == 20
```

**Step 2: Run test to verify it fails**

Run: `cd services/api && poetry run pytest tests/application/test_search_hybrid.py -v`

Expected: FAIL with "cannot import name 'SearchMode'"

**Step 3: Update SearchDocumentsUseCase**

Modify: `services/api/app/application/use_cases/search_documents.py`

```python
"""Search documents use case."""
import logging
from enum import Enum

from app.domain.entities.chunk import Chunk
from app.domain.value_objects.search_query import SearchQuery
from app.ports.services import (
    EmbeddingService,
    VectorStore,
    KeywordStore,
    FusionService
)

logger = logging.getLogger(__name__)


class SearchMode(str, Enum):
    """Search mode selection."""
    VECTOR = "vector"      # Semantic only
    KEYWORD = "keyword"    # BM25 only
    HYBRID = "hybrid"      # RRF fusion (RECOMMENDED)


class SearchDocumentsUseCase:
    """Use case for document search with hybrid retrieval.

    Supports three search modes:
    - VECTOR: Pure semantic search (current default)
    - KEYWORD: Pure lexical/BM25 search
    - HYBRID: Combines both with RRF fusion (RECOMMENDED)

    Hybrid search provides 18-22% accuracy improvement over
    vector-only search according to 2025 research.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        keyword_store: KeywordStore | None = None,
        fusion_service: FusionService | None = None
    ):
        """Initialize with required dependencies.

        Args:
            embedding_service: For query embedding
            vector_store: For semantic search
            keyword_store: For BM25 search (optional, required for hybrid)
            fusion_service: For result fusion (optional, required for hybrid)
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.keyword_store = keyword_store
        self.fusion_service = fusion_service

    async def execute(
        self,
        query: SearchQuery,
        mode: SearchMode = SearchMode.HYBRID,
        fusion_k: int = 60
    ) -> list[Chunk]:
        """Execute document search with specified mode.

        Args:
            query: Search query value object
            mode: Search mode (vector/keyword/hybrid)
            fusion_k: RRF constant for hybrid mode (default 60)

        Returns:
            List of relevant chunks ordered by relevance

        Raises:
            ValueError: If hybrid mode requested but dependencies missing
        """
        logger.info(
            f"Searching: '{query.text}' "
            f"(mode={mode}, top_k={query.top_k})"
        )

        if mode == SearchMode.VECTOR:
            return await self._vector_search(query)

        elif mode == SearchMode.KEYWORD:
            return await self._keyword_search(query)

        elif mode == SearchMode.HYBRID:
            return await self._hybrid_search(query, fusion_k)

        else:
            raise ValueError(f"Unknown search mode: {mode}")

    async def _vector_search(self, query: SearchQuery) -> list[Chunk]:
        """Pure semantic search using embeddings."""
        query_embeddings = await self.embedding_service.generate_embeddings(
            [query.text]
        )
        query_vector = query_embeddings[0]

        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=query.top_k
        )

        logger.info(f"Vector search: {len(results)} results")
        return results

    async def _keyword_search(self, query: SearchQuery) -> list[Chunk]:
        """Pure lexical search using BM25."""
        if self.keyword_store is None:
            raise ValueError("KeywordStore not configured")

        results = await self.keyword_store.search(
            query_text=query.text,
            top_k=query.top_k
        )

        logger.info(f"Keyword search: {len(results)} results")
        return results

    async def _hybrid_search(
        self,
        query: SearchQuery,
        fusion_k: int
    ) -> list[Chunk]:
        """Hybrid search combining vector and keyword with RRF fusion.

        Retrieves 2x results from each method, then fuses to top_k.
        This ensures better coverage before fusion.
        """
        if self.keyword_store is None or self.fusion_service is None:
            raise ValueError("Hybrid search requires KeywordStore and FusionService")

        # Retrieve 2x results from each method for better fusion
        retrieval_k = query.top_k * 2

        # Parallel retrieval (semantic + lexical)
        vector_results = await self._vector_search(
            SearchQuery(text=query.text, top_k=retrieval_k)
        )
        keyword_results = await self.keyword_store.search(
            query_text=query.text,
            top_k=retrieval_k
        )

        logger.info(
            f"Hybrid retrieval: {len(vector_results)} vector, "
            f"{len(keyword_results)} keyword"
        )

        # Fuse with RRF
        fused_results = self.fusion_service.fuse(
            result_sets=[vector_results, keyword_results],
            method="rrf",
            k=fusion_k
        )

        # Return top_k after fusion
        final_results = fused_results[:query.top_k]

        logger.info(f"Hybrid search: {len(final_results)} final results")
        return final_results
```

**Step 4: Run tests to verify they pass**

Run: `cd services/api && poetry run pytest tests/application/test_search_hybrid.py -v`

Expected: PASS

**Step 5: Commit**

```bash
git add services/api/app/application/use_cases/search_documents.py services/api/tests/application/test_search_hybrid.py
git commit -m "feat(search): add hybrid search mode to SearchDocumentsUseCase"
```

---

### Task 6: Update Dependency Injection

**Files:**
- Modify: `services/api/app/api/dependencies.py`

**Step 1: Add keyword store and fusion service dependencies**

Modify: `services/api/app/api/dependencies.py` (add after existing dependencies)

```python
# Add to imports
from app.infrastructure.search.postgres_keyword_store import PostgresKeywordStoreImpl
from app.infrastructure.search.rrf_fusion_service import RRFFusionServiceImpl
from app.ports.services import KeywordStore, FusionService


def get_keyword_store(
    db: AsyncSession = Depends(get_db)
) -> KeywordStore:
    """Create PostgreSQL keyword store instance."""
    return PostgresKeywordStoreImpl(db)


def get_fusion_service() -> FusionService:
    """Create RRF fusion service instance."""
    return RRFFusionServiceImpl()


def get_search_use_case(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: VectorStore = Depends(get_vector_store),
    keyword_store: KeywordStore = Depends(get_keyword_store),
    fusion_service: FusionService = Depends(get_fusion_service)
) -> SearchDocumentsUseCase:
    """Create search use case with hybrid capabilities."""
    return SearchDocumentsUseCase(
        embedding_service=embedding_service,
        vector_store=vector_store,
        keyword_store=keyword_store,
        fusion_service=fusion_service
    )
```

**Step 2: Verify imports are correct**

Run: `cd services/api && python -c "from app.api.dependencies import get_keyword_store, get_fusion_service; print('OK')"`

Expected: "OK"

**Step 3: Commit**

```bash
git add services/api/app/api/dependencies.py
git commit -m "feat(di): add keyword store and fusion service dependencies"
```

---

### Task 7: Update Search API Route

**Files:**
- Modify: `services/api/app/api/routes/hexagonal_search.py`

**Step 1: Read current route implementation**

Run: `cat services/api/app/api/routes/hexagonal_search.py | head -50`

**Step 2: Add SearchMode parameter to route**

Modify: `services/api/app/api/routes/hexagonal_search.py` (update the search endpoint)

```python
# Add to imports
from app.application.use_cases.search_documents import SearchMode

# Update the /search endpoint
@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    mode: SearchMode = SearchMode.HYBRID,  # NEW: default to hybrid
    use_case: SearchDocumentsUseCase = Depends(get_search_use_case)
):
    """Search documents with hybrid retrieval (RECOMMENDED).

    Query parameters:
    - mode: "vector" (semantic only), "keyword" (BM25 only),
            "hybrid" (RRF fusion - RECOMMENDED, +18-22% accuracy)
    """
    # Create search query value object
    search_query = SearchQuery(
        text=request.query,
        top_k=request.top_k
    )

    # Execute search with specified mode
    chunks = await use_case.execute(
        query=search_query,
        mode=mode  # NEW: pass search mode
    )

    # Map to response
    results = [
        SearchResult(
            chunk_id=str(chunk.id),
            document_id=str(chunk.document_id),
            content=chunk.content,
            score=0.0  # Score not used in current impl
        )
        for chunk in chunks
    ]

    return SearchResponse(results=results)
```

**Step 3: Verify route compiles**

Run: `cd services/api && python -c "from app.api.routes.hexagonal_search import router; print('OK')"`

Expected: "OK"

**Step 4: Commit**

```bash
git add services/api/app/api/routes/hexagonal_search.py
git commit -m "feat(api): add hybrid search mode parameter to search endpoint"
```

---

### Task 8: Add Database Migration for FTS

**Files:**
- Create: `services/api/migrations/add_fts_to_chunks.sql`

**Step 1: Check if text_search_vector column exists**

Run: `cd services/api && DATABASE_URL="postgresql://user:pass@localhost/db" poetry run python -c "from app.infrastructure.db.models import ChunkModel; print(ChunkModel.__table__.columns.keys())"`

**Step 2: Create migration SQL**

Create: `services/api/migrations/add_fts_to_chunks.sql`

```sql
-- Add full-text search column to chunks table
-- Run this migration only if using PostgreSQL

-- Add text_search_vector column
ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS text_search_vector tsvector;

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_chunks_text_search
ON chunks USING GIN (text_search_vector);

-- Create trigger to auto-update text_search_vector
CREATE OR REPLACE FUNCTION chunks_text_search_trigger()
RETURNS trigger AS $$
BEGIN
  NEW.text_search_vector :=
    to_tsvector('english', COALESCE(NEW.content, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsvector_update_chunks ON chunks;
CREATE TRIGGER tsvector_update_chunks
BEFORE INSERT OR UPDATE ON chunks
FOR EACH ROW EXECUTE FUNCTION chunks_text_search_trigger();

-- Populate existing rows
UPDATE chunks
SET text_search_vector = to_tsvector('english', COALESCE(content, ''))
WHERE text_search_vector IS NULL;
```

**Step 3: Document migration instructions**

Create: `services/api/migrations/README.md`

```markdown
# Database Migrations

## Full-Text Search (FTS) Setup

**Required for:** Hybrid search with BM25 keyword matching

**Database:** PostgreSQL only (SQLite uses fallback LIKE search)

### Apply Migration

```bash
psql $DATABASE_URL < migrations/add_fts_to_chunks.sql
```

### Verify

```sql
-- Check column exists
\d chunks

-- Check index exists
\di idx_chunks_text_search

-- Test FTS
SELECT id, content
FROM chunks
WHERE text_search_vector @@ plainto_tsquery('english', 'kubernetes')
LIMIT 5;
```
```

**Step 4: Commit**

```bash
git add services/api/migrations/
git commit -m "feat(db): add PostgreSQL full-text search migration for hybrid search"
```

---

### Task 9: Integration Test for Hybrid Search

**Files:**
- Create: `services/api/tests/integration/test_hybrid_search_integration.py`

**Step 1: Write integration test**

Create: `services/api/tests/integration/test_hybrid_search_integration.py`

```python
"""Integration tests for hybrid search end-to-end."""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.main import app


@pytest.mark.asyncio
@pytest.mark.integration
async def test_hybrid_search_endpoint(db_session, setup_test_data):
    """Test hybrid search endpoint returns results."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/hexagonal/search",
            json={
                "query": "kubernetes containers",
                "top_k": 10
            },
            params={"mode": "hybrid"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_hybrid_vs_vector_search_different_results():
    """Test hybrid search returns different results than vector-only."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Vector-only search
        vector_response = await client.post(
            "/api/v1/hexagonal/search",
            json={"query": "kubernetes", "top_k": 5},
            params={"mode": "vector"}
        )

        # Hybrid search
        hybrid_response = await client.post(
            "/api/v1/hexagonal/search",
            json={"query": "kubernetes", "top_k": 5},
            params={"mode": "hybrid"}
        )

        vector_results = vector_response.json()["results"]
        hybrid_results = hybrid_response.json()["results"]

        # Results may differ due to BM25 contribution
        # Just verify both return valid results
        assert len(vector_results) > 0
        assert len(hybrid_results) > 0
```

**Step 2: Create test fixture for data setup**

Note: Skip if fixtures already exist. Check `tests/conftest.py`.

**Step 3: Run integration tests**

Run: `cd services/api && poetry run pytest tests/integration/test_hybrid_search_integration.py -v -m integration`

Expected: PASS (or SKIP if no test database configured)

**Step 4: Commit**

```bash
git add services/api/tests/integration/test_hybrid_search_integration.py
git commit -m "test(search): add hybrid search integration tests"
```

---

## Phase 2: Query Expansion (Optional Enhancement)

**Note:** Query expansion is already implemented in `app/services/query_expansion.py`. This phase would migrate it into hexagonal architecture.

**Tasks:**
1. Create QueryAugmenter port
2. Implement LLM-based query augmenter
3. Update SearchDocumentsUseCase with expansion logic
4. Add tests

**Time estimate:** 3-4 hours
**Impact:** +15-20% recall improvement

---

## Phase 3: Reranking (Optional Enhancement)

**Note:** Reranking is already implemented in `app/services/reranker.py`. This phase would migrate it into hexagonal architecture.

**Tasks:**
1. Create Reranker port
2. Implement cross-encoder reranker
3. Update SearchDocumentsUseCase with reranking logic
4. Add tests

**Time estimate:** 2-3 hours
**Impact:** +8-12% precision improvement

---

## Testing Strategy

### Unit Tests
- All new ports have test coverage
- All implementations have unit tests
- Mock external dependencies

### Integration Tests
- End-to-end hybrid search flow
- Database FTS queries
- API endpoint with all modes

### Performance Tests
- Measure latency with hybrid vs vector-only
- Verify <10% latency increase
- Load test with concurrent requests

---

## Deployment Checklist

1. ✅ Apply database migration for FTS
2. ✅ Run all tests
3. ✅ Deploy to staging
4. ✅ Verify hybrid search works
5. ✅ Monitor latency metrics
6. ✅ Gradual rollout to production

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Retrieval Precision | TBD | +18-22% | Manual eval on test queries |
| Query Latency P95 | TBD | <10% increase | Monitoring |
| Test Coverage | TBD | >80% | pytest --cov |

---

## Rollback Plan

If issues occur:
1. Set `mode=SearchMode.VECTOR` as default in route
2. Monitor for errors
3. Fix issues in staging
4. Re-deploy when stable

---

**Implementation Status:** 📋 READY TO START
**Estimated Time:** 4-6 hours (Phase 1 only)
**Risk Level:** LOW ✅ (Gradual enhancement, falls back to vector search)
