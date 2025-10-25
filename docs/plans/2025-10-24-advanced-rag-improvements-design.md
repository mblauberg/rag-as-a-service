# Advanced RAG System Improvements - Design Document

**Date:** 2025-10-24
**Status:** Design Approved
**Timeline:** 1-2 week sprint
**Focus:** Technical Complexity & Innovation

## Executive Summary

This design introduces three state-of-the-art RAG improvements to enhance retrieval quality and demonstrate advanced technical sophistication:

1. **Semantic Chunking** - Intelligent document segmentation based on semantic boundaries
2. **Hybrid Search** - Parallel BM25 + vector search with Reciprocal Rank Fusion
3. **Query Expansion** - LLM-based query reformulation for better coverage

**Expected Impact:** 25-40% improvement in retrieval quality (research-backed)

## Current System Analysis

### Architecture
- **Services:** API (FastAPI), Embedder, Generator, Frontend (React)
- **Data Stores:** PostgreSQL (metadata), Qdrant (vectors)
- **Current RAG Flow:** Upload → Chunk → Embed → Search → Generate

### Existing Chunking Strategy
- Fixed-size `RecursiveCharacterTextSplitter`
- 400 tokens per chunk, 80 token overlap
- Character-based boundaries (ignores semantic structure)

### Existing Retrieval
- Pure vector search (Qdrant cosine similarity)
- Optional cross-encoder reranking
- Single query processing

### Key Gaps
- Chunks split mid-concept (poor embedding quality)
- No lexical matching (misses exact keywords/abbreviations)
- Single query interpretation (misses synonyms)

---

## Component 1: Semantic Chunking

### Overview
Replace fixed-size chunking with semantic similarity-based segmentation using LangChain's research-proven `SemanticChunker`.

### Implementation

**Technology:**
```python
from langchain_experimental.text_splitter import SemanticChunker

chunker = SemanticChunker(
    embeddings=embeddings_model,           # Reuse: all-MiniLM-L6-v2
    breakpoint_threshold_type="percentile", # Adaptive per document
    breakpoint_threshold_amount=95.0,       # 95th percentile = natural boundaries
    min_chunk_size=128,                     # Avoid fragments
    max_chunk_size=512                      # Context limit
)
```

**How It Works:**
1. Split text into sentences
2. Generate embedding for each sentence
3. Calculate cosine similarity between adjacent sentences
4. Create chunk boundary when similarity drop exceeds 95th percentile
5. Result: Chunks of 256-400 tokens respecting semantic boundaries

**Research Validation:**
- AMI scores: 0.85-0.90 (superior vs fixed chunking)
- Optimal chunk range: 256-512 tokens for embedding models
- Percentile approach adapts automatically per document

**Integration Points:**
- Location: `services/api/app/services/chunking/semantic_chunker.py`
- Replace: Existing `RecursiveCharacterTextSplitter` usage
- Dependency: Add `langchain-experimental` to `pyproject.toml`
- Interface: Keep existing `chunk_document()` signature (minimal API changes)
- Migration: Existing chunks remain valid; new uploads use semantic chunking

**Configuration:**
```python
# services/api/app/config.py
CHUNKING_STRATEGY: str = "semantic"  # semantic | recursive
SEMANTIC_MIN_CHUNK: int = 128
SEMANTIC_MAX_CHUNK: int = 512
SEMANTIC_BREAKPOINT_PERCENTILE: float = 95.0
```

**Testing:**
- Unit tests: Verify boundary detection on sample documents
- Integration test: Upload → semantic chunk → verify coherence scores
- Comparison test: Same document with recursive vs semantic (measure quality)

**Expected Improvement:** 10-15% better retrieval (better embeddings from coherent chunks)

---

## Component 2: Hybrid Search

### Overview
Combine lexical search (BM25) with vector search (dense embeddings) using Reciprocal Rank Fusion to get best of both approaches.

### Architecture

```
Query → [BM25 Search (PostgreSQL)]  → Top 20 results (ranked)
     ↓                                ↓
     → [Vector Search (Qdrant)]    → Top 20 results (ranked)
                                      ↓
                                [RRF Fusion]
                                      ↓
                                Top 10 combined results
```

### BM25 Implementation (PostgreSQL Full-Text Search)

**Schema Changes:**
```sql
-- Add tsvector column for full-text search
ALTER TABLE document_chunks
ADD COLUMN text_search_vector tsvector
GENERATED ALWAYS AS (to_tsvector('english', text)) STORED;

-- Create GIN index for fast lexical search
CREATE INDEX idx_text_search ON document_chunks
USING GIN (text_search_vector);
```

**Query Implementation:**
```python
async def bm25_search(query: str, limit: int = 20) -> List[SearchResult]:
    """
    PostgreSQL ts_rank provides BM25-like ranking
    """
    sql = """
        SELECT
            id,
            document_id,
            text,
            ts_rank(text_search_vector, plainto_tsquery('english', :query)) as score
        FROM document_chunks
        WHERE text_search_vector @@ plainto_tsquery('english', :query)
        ORDER BY score DESC
        LIMIT :limit
    """
    result = await db.execute(sql, {"query": query, "limit": limit})
    return result.fetchall()
```

**Why PostgreSQL FTS:**
- Already in stack (no new service dependency)
- GIN index provides fast lexical search
- BM25-like ranking via `ts_rank`
- Handles 10k+ documents efficiently
- Natural language query parsing via `plainto_tsquery`

### Vector Search (Existing)

No changes to existing Qdrant vector search; leverage as-is.

### Reciprocal Rank Fusion

**Algorithm:**
```python
def reciprocal_rank_fusion(
    bm25_results: List[SearchResult],
    vector_results: List[SearchResult],
    k: int = 60  # Research-proven constant
) -> List[SearchResult]:
    """
    RRF formula: score = sum(1 / (k + rank))
    where k=60 balances different scoring scales
    """
    scores = defaultdict(float)

    # Score from BM25 ranking
    for rank, result in enumerate(bm25_results, start=1):
        scores[result.id] += 1 / (k + rank)

    # Score from vector ranking
    for rank, result in enumerate(vector_results, start=1):
        scores[result.id] += 1 / (k + rank)

    # Combine and sort by RRF score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Why RRF:**
- No parameter tuning needed (k=60 is standard)
- Handles different score scales (BM25 vs cosine similarity)
- Proven in information retrieval research
- Simple and fast

### Parallel Execution

```python
async def hybrid_search(query: str, limit: int = 10) -> SearchResponse:
    """
    Execute BM25 and vector search in parallel, then fuse results
    """
    # Run both searches concurrently
    bm25_task = asyncio.create_task(bm25_search(query, limit=20))
    vector_task = asyncio.create_task(vector_search(query, limit=20))

    bm25_results, vector_results = await asyncio.gather(bm25_task, vector_task)

    # Fuse results using RRF
    fused_ids = reciprocal_rank_fusion(bm25_results, vector_results)

    # Fetch full chunk data for top-K
    top_chunks = await fetch_chunks(fused_ids[:limit])

    return SearchResponse(
        chunks=top_chunks,
        retrieval_method="hybrid",
        metadata={
            "bm25_count": len(bm25_results),
            "vector_count": len(vector_results),
            "overlap_count": len(set(bm25_results) & set(vector_results))
        }
    )
```

### API Endpoint

**New Endpoint:**
```python
@router.post("/search/hybrid", response_model=SearchResponse)
async def search_hybrid(request: SearchRequest):
    """
    Hybrid search combining BM25 and vector retrieval
    """
    return await hybrid_search(
        query=request.query,
        limit=request.limit or 10
    )
```

**Backward Compatibility:**
- Keep existing `/search` endpoint (pure vector)
- Add new `/search/hybrid` endpoint
- Frontend can choose method via configuration

### Integration Points

**Files to Modify:**
- `services/api/app/api/routes/search.py` - Add hybrid endpoint
- `services/api/app/services/search_service.py` - Add hybrid_search()
- `services/api/app/db/models.py` - Add text_search_vector column
- `services/api/app/db/migrations/` - Create migration for FTS setup

**Dependencies:**
- No new packages (PostgreSQL FTS is built-in)

### Performance Characteristics

**Latency:**
- BM25 search: ~10-20ms (GIN index)
- Vector search: ~40-60ms (existing Qdrant)
- Parallel execution: ~50-100ms total (not additive)
- RRF fusion: <5ms (in-memory ranking)

**Storage:**
- GIN index size: ~20% of text corpus size
- Example: 1GB text → ~200MB index

**Scalability:**
- PostgreSQL FTS scales to millions of documents
- GIN index handles high query load
- Async execution prevents blocking

### Testing Strategy

**Unit Tests:**
- Test RRF with known rankings
- Test BM25 query parsing
- Test async gather behavior

**Integration Tests:**
- Upload docs → verify FTS index populated
- Search with exact keywords → verify BM25 catches them
- Search with synonyms → verify vector catches them
- Compare hybrid vs vector-only on test queries

**Performance Tests:**
- Measure latency under load
- Verify parallel execution (not sequential)

**Expected Improvement:** 18-22% better retrieval (research-backed for hybrid)

---

## Component 3: Query Expansion

### Overview
Use LLM to generate 2-3 alternative query phrasings, then search with all variants to improve recall.

### Implementation

**Query Expansion via Generator Service:**
```python
async def expand_query(query: str) -> List[str]:
    """
    Generate 2 alternative query phrasings using existing generator service
    Returns: [original_query, alternative_1, alternative_2]
    """
    prompt = f"""Given this search query, generate 2 alternative phrasings that:
- Add technical synonyms and related terms
- Expand abbreviations (e.g., k8s → kubernetes)
- Clarify vague terms
- Keep the same search intent

Query: "{query}"

Output format (one per line):
Alternative 1:
Alternative 2:"""

    response = await generator_client.generate(
        prompt=prompt,
        model="gpt-4o-mini",  # Fast and cheap
        max_tokens=150,
        temperature=0.3  # Low temp for consistency
    )

    alternatives = parse_alternatives(response.text)
    return [query] + alternatives  # Total: 3 queries
```

**Multi-Query Retrieval:**
```python
async def search_with_expansion(query: str, limit: int = 10) -> SearchResponse:
    """
    Expand query into variants, search with each, merge results
    """
    # Step 1: Expand query (3 variants)
    expanded_queries = await expand_query(query)

    # Step 2: Search with all variants in parallel
    search_tasks = [
        hybrid_search(q, limit=15) for q in expanded_queries
    ]
    all_results = await asyncio.gather(*search_tasks)

    # Step 3: Apply RRF across all result sets
    merged = reciprocal_rank_fusion_multi(all_results)

    # Step 4: Return top-K
    return SearchResponse(
        chunks=merged[:limit],
        expanded_queries=expanded_queries,
        retrieval_method="hybrid_with_expansion"
    )
```

**Multi-Set RRF:**
```python
def reciprocal_rank_fusion_multi(
    result_sets: List[List[SearchResult]],
    k: int = 60
) -> List[SearchResult]:
    """
    Apply RRF across multiple result sets (one per query variant)
    """
    scores = defaultdict(float)

    for result_set in result_sets:
        for rank, result in enumerate(result_set, start=1):
            scores[result.id] += 1 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### API Endpoint

**New Endpoint:**
```python
@router.post("/search/advanced", response_model=SearchResponse)
async def search_advanced(request: SearchRequest):
    """
    Advanced search with query expansion, hybrid retrieval, and result fusion
    Full pipeline: Expand → Hybrid Search (per variant) → Merge
    """
    return await search_with_expansion(
        query=request.query,
        limit=request.limit or 10
    )
```

**Response Schema:**
```python
class SearchResponse(BaseModel):
    chunks: List[ChunkResult]
    retrieval_method: str
    expanded_queries: Optional[List[str]] = None  # New field
    metadata: Dict[str, Any]
```

### Integration Points

**Files to Modify:**
- `services/api/app/api/routes/search.py` - Add advanced endpoint
- `services/api/app/services/search_service.py` - Add expansion logic
- `services/api/app/clients/generator_client.py` - Ensure supports expansion calls

**Dependencies:**
- Reuses existing generator service (no new packages)

### Performance Characteristics

**Latency:**
- Query expansion (LLM): ~200-300ms
- 3x hybrid searches (parallel): ~100-150ms
- Multi-set RRF fusion: <10ms
- **Total: ~300-450ms** (acceptable for quality gain)

**Cost:**
- ~150 tokens per expansion (gpt-4o-mini: $0.00002)
- Negligible cost per query

**Optimization:**
- Cache expansions for common queries
- Optional: Run expansion in parallel with first search

### Testing Strategy

**Unit Tests:**
- Mock LLM responses → verify parsing
- Test multi-set RRF with known rankings

**Integration Tests:**
- Query with abbreviation (e.g., "k8s") → verify expansion includes "kubernetes"
- Compare expanded vs non-expanded recall

**Example Test Cases:**
```python
test_cases = [
    {
        "query": "k8s pod fails",
        "expected_expansions": ["kubernetes", "deployment", "container"]
    },
    {
        "query": "db query slow",
        "expected_expansions": ["database", "performance", "optimization"]
    }
]
```

**Expected Improvement:** 15-25% better recall (research-backed for query expansion)

---

## Combined System Architecture

### End-to-End Flow

```
1. Document Upload
   ↓
2. Semantic Chunking (LangChain SemanticChunker)
   ↓
3. Embed Chunks (existing embedder service)
   ↓
4. Store: PostgreSQL (metadata + FTS) + Qdrant (vectors)

---

5. User Search Query
   ↓
6. Query Expansion (LLM generates 2 alternatives → 3 total queries)
   ↓
7. For Each Query Variant (parallel):
   ├─ BM25 Search (PostgreSQL FTS) → Top 15
   ├─ Vector Search (Qdrant) → Top 15
   └─ RRF Fusion → Top 15 per variant
   ↓
8. Multi-Set RRF Across All Variants
   ↓
9. Return Top 10 Final Results
   ↓
10. Optional: Generate Summary (existing generator)
```

### API Endpoints

```
Existing:
POST /search                    - Pure vector search (backward compatible)

New:
POST /search/hybrid             - BM25 + Vector + RRF
POST /search/advanced           - Query expansion + Hybrid + Multi-RRF (full pipeline)
```

### Configuration

```python
# services/api/app/config.py

# Chunking
CHUNKING_STRATEGY: str = "semantic"  # semantic | recursive
SEMANTIC_MIN_CHUNK: int = 128
SEMANTIC_MAX_CHUNK: int = 512
SEMANTIC_BREAKPOINT_PERCENTILE: float = 95.0

# Hybrid Search
ENABLE_BM25_SEARCH: bool = True
BM25_LIMIT: int = 20  # Retrieve 2x for fusion
VECTOR_LIMIT: int = 20
RRF_K: int = 60

# Query Expansion
ENABLE_QUERY_EXPANSION: bool = True
EXPANSION_COUNT: int = 2  # Generate 2 alternatives
EXPANSION_MODEL: str = "gpt-4o-mini"
EXPANSION_TEMPERATURE: float = 0.3
```

---

## Implementation Plan Overview

### Phase 1: Semantic Chunking (3-4 days)
1. Add `langchain-experimental` dependency
2. Implement `SemanticChunkerV2` class
3. Add configuration flags
4. Create migration path (backward compatible)
5. Unit + integration tests
6. Document chunking comparison

### Phase 2: Hybrid Search (3-4 days)
1. Create PostgreSQL FTS migration (add tsvector column + GIN index)
2. Implement BM25 search service method
3. Implement RRF fusion algorithm
4. Create `/search/hybrid` endpoint
5. Add parallel execution with asyncio.gather
6. Unit + integration + performance tests
7. Document hybrid vs vector comparison

### Phase 3: Query Expansion (2-3 days)
1. Implement query expansion via generator client
2. Implement multi-query search orchestration
3. Implement multi-set RRF
4. Create `/search/advanced` endpoint
5. Add query caching (optional optimization)
6. Integration tests with real LLM
7. Document expansion examples

### Phase 4: Integration & Testing (1-2 days)
1. End-to-end integration tests (upload → semantic chunk → hybrid search → expand query)
2. Performance testing and optimization
3. Frontend integration (add endpoint selection)
4. Documentation updates (README, API docs)
5. Migration guide for existing deployments

### Phase 5: Documentation & Polish (1 day)
1. Update architecture diagrams
2. Write deployment guide
3. Create comparison benchmarks (optional)
4. Code review and cleanup

**Total Estimated Time:** 10-14 days

---

## Expected Outcomes

### Quantitative Improvements (Research-Backed)

| Improvement | Expected Gain | Mechanism |
|-------------|---------------|-----------|
| Semantic Chunking | +10-15% retrieval quality | Better embeddings from coherent chunks |
| Hybrid Search | +18-22% retrieval quality | Lexical + semantic complementarity |
| Query Expansion | +15-25% recall | Captures synonyms and alternative phrasings |
| **Combined** | **+25-40%** | Multiplicative effect across pipeline |

### Qualitative Benefits

**Technical Sophistication:**
- Demonstrates state-of-the-art RAG techniques (2025 best practices)
- Shows understanding of information retrieval theory (RRF, BM25)
- Leverages modern LLM capabilities for query understanding

**Production Readiness:**
- Backward compatible (existing endpoints remain functional)
- Performance optimized (parallel execution, indexing)
- Configurable (feature flags for gradual rollout)

**Academic Merit:**
- Research-backed approaches (citations available)
- Measurable improvements (before/after comparison possible)
- Demonstrates advanced understanding of RAG systems

---

## Risks & Mitigations

### Risk 1: Semantic Chunking Performance
**Issue:** Embedding every sentence adds latency to document upload

**Mitigation:**
- Async processing with progress tracking
- Cache sentence embeddings
- Batch process 50 sentences at a time
- Background job queue for large documents (future)

### Risk 2: Query Expansion Latency
**Issue:** LLM call adds 200-300ms to search

**Mitigation:**
- Use fast model (gpt-4o-mini)
- Cache expansions for common queries
- Make optional via API flag
- Run expansion in parallel with first search (optimization)

### Risk 3: BM25 Index Size
**Issue:** GIN index adds storage overhead

**Mitigation:**
- Index size ~20% of text (acceptable)
- Monitor with PostgreSQL stats
- Optional: Compress old documents

### Risk 4: Increased Complexity
**Issue:** More moving parts = more potential failures

**Mitigation:**
- Comprehensive test coverage
- Feature flags for gradual rollout
- Fallback to existing vector search on errors
- Monitoring and logging at each stage

---

## Success Criteria

### Must Have (MVP)
- [ ] Semantic chunking implemented and tested
- [ ] Hybrid search (BM25 + vector + RRF) working
- [ ] Query expansion with LLM functional
- [ ] All new endpoints deployed and documented
- [ ] Backward compatibility maintained

### Should Have
- [ ] Integration tests covering full pipeline
- [ ] Performance benchmarks (latency, throughput)
- [ ] Frontend integration with endpoint selection
- [ ] Migration guide for existing deployments

### Nice to Have
- [ ] Before/after comparison metrics
- [ ] Query expansion caching
- [ ] Background processing for semantic chunking
- [ ] Monitoring dashboard for retrieval methods

---

## References

### Research Papers & Articles
1. "Enhancing Retrieval-Augmented Generation: A Study of Best Practices" (arXiv:2501.07391, 2025)
2. "Max-Min Semantic Chunking for RAG" (Springer, 2025)
3. "Optimizing RAG with Hybrid Search & Reranking" (VectorHub, 2025)
4. LangChain SemanticChunker Documentation (2025)

### Best Practices
- Semantic chunking achieves 0.85-0.90 AMI scores
- Hybrid search shows 18-22% retrieval improvement
- Optimal chunk size: 256-512 tokens for embedding models
- RRF with k=60 is research-proven standard
- Query expansion improves recall by 15-25%

---

## Appendix: Technical Decisions

### Why LangChain SemanticChunker?
- Battle-tested implementation (used in production systems)
- Active maintenance and community support
- Percentile-based approach adapts per document
- No manual threshold tuning required

### Why PostgreSQL FTS over Elasticsearch?
- Already in stack (no new service)
- Sufficient for 10k-100k documents
- BM25-like ranking via ts_rank
- Lower operational complexity

### Why RRF over Weighted Average?
- No hyperparameter tuning needed
- Handles different score scales automatically
- Research-proven effective (k=60 standard)
- Simple and fast

### Why LLM Expansion over WordNet/Embeddings?
- Better handles domain-specific terminology
- Understands context and intent
- Expands abbreviations intelligently
- Reuses existing infrastructure

---

**End of Design Document**
