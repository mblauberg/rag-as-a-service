# API Guide

Workflow examples, SDK code, and best practices for the RAaS API.

**Interactive API Documentation:** http://localhost:8000/docs (Swagger UI)
**Base URL:** `http://localhost:8000/api/v1`

> For detailed request/response schemas and interactive testing, use the Swagger UI at `/docs`. This guide focuses on common workflows, integration patterns, and SDK examples.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Common Workflows](#common-workflows)
- [SDK Examples](#sdk-examples)
- [Search Strategies](#search-strategies)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Performance Tips](#performance-tips)

---

## Quick Start

### 1. Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@research_paper.pdf" \
  -F "title=Machine Learning Research 2024" \
  -F "description=Survey of transformer architectures"
```

### 2. Search Documents

```bash
curl -X POST "http://localhost:8000/api/v1/search?mode=hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what are transformer architectures",
    "top_k": 5
  }'
```

### 3. Generate AI Summary

```bash
curl -X POST "http://localhost:8000/api/v1/generate/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what are transformer architectures",
    "chunk_ids": ["660e8400-e29b-41d4-a716-446655440111"],
    "model": "openai:gpt-4o-mini"
  }'
```

---

## Common Workflows

### Complete RAG Pipeline (Upload → Search → Generate)

This is the most common workflow: upload documents, search them, and generate AI summaries.

```python
import httpx
from typing import List, Dict

async def rag_workflow(
    file_path: str,
    query: str,
    base_url: str = "http://localhost:8000/api/v1"
) -> str:
    """Complete RAG workflow: upload, search, generate."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Upload document
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"title": "Research Paper", "description": "ML research"}

            upload_response = await client.post(
                f"{base_url}/documents/upload",
                files=files,
                data=data
            )
            upload_response.raise_for_status()
            doc_id = upload_response.json()["document"]["id"]
            print(f"✓ Uploaded: {doc_id}")

        # Step 2: Search for relevant content
        search_response = await client.post(
            f"{base_url}/search?mode=hybrid&use_reranking=true",
            json={"query": query, "top_k": 5}
        )
        search_response.raise_for_status()
        results = search_response.json()["results"]
        chunk_ids = [r["chunk_id"] for r in results]
        print(f"✓ Found {len(chunk_ids)} relevant chunks")

        # Step 3: Generate AI summary
        generate_response = await client.post(
            f"{base_url}/generate/summary",
            json={
                "query": query,
                "chunk_ids": chunk_ids,
                "model": "openai:gpt-4o-mini"
            }
        )
        generate_response.raise_for_status()
        summary = generate_response.json()["summary"]
        print(f"✓ Generated summary ({len(summary)} chars)")

        return summary

# Usage
summary = await rag_workflow("paper.pdf", "what are transformers?")
print(summary)
```

### Search-Only Workflow (Existing Documents)

When documents are already uploaded, skip to search:

```python
async def search_existing_documents(
    query: str,
    mode: str = "hybrid",
    use_reranking: bool = True
) -> List[Dict]:
    """Search already-uploaded documents."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/search",
            params={
                "mode": mode,
                "use_reranking": use_reranking,
                "use_expansion": True
            },
            json={"query": query, "top_k": 10}
        )
        response.raise_for_status()
        return response.json()["results"]

# Compare search modes
vector_results = await search_existing_documents(query, mode="vector")
keyword_results = await search_existing_documents(query, mode="keyword")
hybrid_results = await search_existing_documents(query, mode="hybrid")
```

### Batch Document Upload

Upload multiple documents efficiently:

```python
import asyncio
from pathlib import Path

async def batch_upload(directory: Path) -> List[str]:
    """Upload all PDFs in a directory."""

    async with httpx.AsyncClient(timeout=120.0) as client:
        tasks = []

        for pdf_file in directory.glob("*.pdf"):
            async def upload_file(file_path):
                with open(file_path, "rb") as f:
                    files = {"file": f}
                    data = {
                        "title": file_path.stem,
                        "description": f"Auto-uploaded from {file_path.name}"
                    }
                    response = await client.post(
                        f"{base_url}/documents/upload",
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    return response.json()["document"]["id"]

            tasks.append(upload_file(pdf_file))

        # Upload in parallel (limit concurrency)
        doc_ids = []
        for i in range(0, len(tasks), 3):  # 3 concurrent uploads
            batch = tasks[i:i+3]
            results = await asyncio.gather(*batch)
            doc_ids.extend(results)
            print(f"Uploaded batch {i//3 + 1}: {len(results)} documents")

        return doc_ids

# Usage
doc_ids = await batch_upload(Path("./research_papers/"))
print(f"Uploaded {len(doc_ids)} documents")
```

### Multi-Query Generation

Generate summaries for multiple queries against the same document set:

```python
async def multi_query_generation(queries: List[str]) -> Dict[str, str]:
    """Generate summaries for multiple queries."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        summaries = {}

        for query in queries:
            # Search
            search_response = await client.post(
                f"{base_url}/search",
                json={"query": query, "top_k": 5}
            )
            results = search_response.json()["results"]
            chunk_ids = [r["chunk_id"] for r in results]

            # Generate
            gen_response = await client.post(
                f"{base_url}/generate/summary",
                json={
                    "query": query,
                    "chunk_ids": chunk_ids,
                    "model": "openai:gpt-4o-mini"
                }
            )
            summaries[query] = gen_response.json()["summary"]

            # Rate limiting - avoid overwhelming LLM API
            await asyncio.sleep(1)

        return summaries

# Usage
queries = [
    "What are the main findings?",
    "What methodology was used?",
    "What are the limitations?"
]
results = await multi_query_generation(queries)
```

---

## SDK Examples

### Python Client Class

Complete client with error handling:

```python
import httpx
from typing import List, Dict, Optional
from pathlib import Path

class RaasClient:
    """Production-ready RAaS API client."""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def upload_document(
        self,
        file_path: Path,
        title: str,
        description: Optional[str] = None
    ) -> Dict:
        """Upload a document for processing."""
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"title": title}
            if description:
                data["description"] = description

            response = await self.client.post(
                f"{self.base_url}/documents/upload",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()

    async def search(
        self,
        query: str,
        top_k: int = 10,
        mode: str = "hybrid",
        use_reranking: bool = True,
        use_expansion: bool = True
    ) -> List[Dict]:
        """Search documents with configurable strategy."""
        response = await self.client.post(
            f"{self.base_url}/search",
            params={
                "mode": mode,
                "use_reranking": use_reranking,
                "use_expansion": use_expansion
            },
            json={"query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json()["results"]

    async def generate_summary(
        self,
        query: str,
        chunk_ids: List[str],
        model: str = "openai:gpt-4o-mini"
    ) -> str:
        """Generate AI summary from chunks."""
        response = await self.client.post(
            f"{self.base_url}/generate/summary",
            json={
                "query": query,
                "chunk_ids": chunk_ids,
                "model": model
            }
        )
        response.raise_for_status()
        return response.json()["summary"]

    async def list_documents(
        self,
        page: int = 1,
        limit: int = 20
    ) -> Dict:
        """List uploaded documents with pagination."""
        response = await self.client.get(
            f"{self.base_url}/documents",
            params={"page": page, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def delete_document(self, document_id: str) -> None:
        """Delete a document permanently."""
        response = await self.client.delete(
            f"{self.base_url}/documents/{document_id}"
        )
        response.raise_for_status()

    async def get_available_models(self) -> List[Dict]:
        """Get list of available LLM models."""
        response = await self.client.get(f"{self.base_url}/models")
        response.raise_for_status()
        return response.json()["models"]

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Usage example
async def main():
    client = RaasClient()
    try:
        # Upload
        doc = await client.upload_document(
            Path("paper.pdf"),
            title="Research Paper",
            description="ML research"
        )
        print(f"Uploaded: {doc['document']['id']}")

        # Search
        results = await client.search("transformer architecture", top_k=5)
        chunk_ids = [r["chunk_id"] for r in results]

        # Generate
        summary = await client.generate_summary(
            "what are transformers?",
            chunk_ids
        )
        print(f"Summary: {summary}")
    finally:
        await client.close()
```

### TypeScript/JavaScript Client

```typescript
class RaasClient {
  constructor(private baseUrl: string = 'http://localhost:8000/api/v1') {}

  async uploadDocument(
    file: File,
    title: string,
    description?: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) formData.append('description', description);

    const response = await fetch(`${this.baseUrl}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }
    return response.json();
  }

  async search(
    query: string,
    options: {
      topK?: number;
      mode?: 'vector' | 'keyword' | 'hybrid';
      useReranking?: boolean;
      useExpansion?: boolean;
    } = {}
  ): Promise<any[]> {
    const {
      topK = 10,
      mode = 'hybrid',
      useReranking = true,
      useExpansion = true,
    } = options;

    const url = new URL(`${this.baseUrl}/search`);
    url.searchParams.set('mode', mode);
    url.searchParams.set('use_reranking', String(useReranking));
    url.searchParams.set('use_expansion', String(useExpansion));

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK }),
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.status}`);
    }
    const data = await response.json();
    return data.results;
  }

  async generateSummary(
    query: string,
    chunkIds: string[],
    model: string = 'openai:gpt-4o-mini'
  ): Promise<string> {
    const response = await fetch(`${this.baseUrl}/generate/summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, chunk_ids: chunkIds, model }),
    });

    if (!response.ok) {
      throw new Error(`Generation failed: ${response.status}`);
    }
    const data = await response.json();
    return data.summary;
  }

  async ragWorkflow(
    file: File,
    query: string,
    title: string
  ): Promise<string> {
    // Upload
    const uploadResult = await this.uploadDocument(file, title);
    console.log('✓ Uploaded:', uploadResult.document.id);

    // Search
    const results = await this.search(query, { topK: 5 });
    const chunkIds = results.map((r) => r.chunk_id);
    console.log('✓ Found chunks:', chunkIds.length);

    // Generate
    const summary = await this.generateSummary(query, chunkIds);
    console.log('✓ Generated summary');

    return summary;
  }
}

// React hook example
function useRaasSearch(query: string) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!query) return;

    const client = new RaasClient();
    setLoading(true);

    client
      .search(query)
      .then(setResults)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [query]);

  return { results, loading, error };
}
```

---

## Search Strategies

### When to Use Each Mode

**Vector Search (`mode=vector`):**
- **Best for:** Conceptual queries, paraphrasing, semantic understanding
- **Example:** "machine learning approaches" finds "neural networks," "deep learning"
- **Weakness:** Misses exact terminology, proper nouns

```bash
curl -X POST "http://localhost:8000/api/v1/search?mode=vector" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence techniques", "top_k": 10}'
```

**Keyword Search (`mode=keyword`):**
- **Best for:** Specific terms, names, acronyms, exact phrases
- **Example:** "GPT-4" finds exact matches, not "language models"
- **Weakness:** No semantic understanding, no synonyms

```bash
curl -X POST "http://localhost:8000/api/v1/search?mode=keyword" \
  -H "Content-Type: application/json" \
  -d '{"query": "BERT GPT-4 RoBERTa", "top_k": 10}'
```

**Hybrid Search (`mode=hybrid`)** - RECOMMENDED:
- **Best for:** Most queries (18-22% better than single methods)
- **Combines:** Semantic understanding + exact matching
- **How:** Reciprocal Rank Fusion (RRF) merges both result sets

```bash
curl -X POST "http://localhost:8000/api/v1/search?mode=hybrid" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer architecture BERT", "top_k": 10}'
```

### Performance vs. Accuracy Trade-offs

```python
# Fastest (50ms) - Vector only, no extras
results = await client.search(
    query,
    mode="vector",
    use_reranking=False,
    use_expansion=False
)

# Balanced (100ms) - Hybrid, no reranking
results = await client.search(
    query,
    mode="hybrid",
    use_reranking=False,
    use_expansion=True
)

# Best Quality (200ms) - Hybrid with all optimizations
results = await client.search(
    query,
    mode="hybrid",
    use_reranking=True,
    use_expansion=True
)
```

---

## Error Handling

### Retry Logic with Exponential Backoff

```python
import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> T:
    """Retry failed requests with exponential backoff."""

    for attempt in range(max_retries):
        try:
            return await func()
        except httpx.HTTPStatusError as e:
            # Don't retry client errors (4xx)
            if 400 <= e.response.status_code < 500:
                raise

            # Retry server errors (5xx) and network errors
            if attempt == max_retries - 1:
                raise

            delay = initial_delay * (backoff_factor ** attempt)
            print(f"Retry {attempt + 1}/{max_retries} after {delay}s")
            await asyncio.sleep(delay)
        except httpx.RequestError as e:
            # Network errors - always retry
            if attempt == max_retries - 1:
                raise

            delay = initial_delay * (backoff_factor ** attempt)
            await asyncio.sleep(delay)

# Usage
result = await retry_with_backoff(
    lambda: client.post(url, json=data)
)
```

### Error-Specific Handling

```python
from httpx import HTTPStatusError

async def safe_api_call():
    """Handle different error scenarios."""

    try:
        response = await client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    except HTTPStatusError as e:
        if e.response.status_code == 400:
            # Bad request - check your input
            print(f"Invalid request: {e.response.json()['detail']}")
            raise

        elif e.response.status_code == 404:
            # Resource not found
            print("Document or chunk not found")
            return None

        elif e.response.status_code == 503:
            # Service unavailable - retry
            print("Service temporarily unavailable")
            await asyncio.sleep(5)
            return await retry_with_backoff(lambda: client.post(url, json=data))

        else:
            # Unexpected error
            print(f"API error {e.response.status_code}: {e}")
            raise

    except httpx.RequestError as e:
        # Network error
        print(f"Network error: {e}")
        return await retry_with_backoff(lambda: client.post(url, json=data))
```

---

## Best Practices

### 1. Always Use Pagination

```python
# Bad - may load thousands of documents
documents = await client.get("/api/v1/documents")

# Good - paginate results
async def get_all_documents():
    all_docs = []
    page = 1

    while True:
        response = await client.get(
            f"/api/v1/documents?page={page}&limit=20"
        )
        data = response.json()
        all_docs.extend(data["documents"])

        if len(all_docs) >= data["total"]:
            break

        page += 1

    return all_docs
```

### 2. Cache Query Embeddings

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_query_hash(query: str) -> str:
    """Cache key for query."""
    return hashlib.md5(query.encode()).hexdigest()

# Client-side cache
query_cache = {}

async def cached_search(query: str, **kwargs):
    """Search with client-side caching."""
    cache_key = f"{get_query_hash(query)}:{kwargs}"

    if cache_key in query_cache:
        return query_cache[cache_key]

    results = await client.search(query, **kwargs)
    query_cache[cache_key] = results
    return results
```

### 3. Optimize Chunk Selection

```python
async def smart_generate(query: str, search_results: List[Dict]) -> str:
    """Intelligently select chunks for generation."""

    # Filter high-quality results only
    quality_threshold = 0.7
    good_results = [
        r for r in search_results
        if r["score"] >= quality_threshold
    ]

    # Limit total tokens to avoid context overflow
    max_tokens = 6000
    total_tokens = 0
    selected_chunks = []

    for result in good_results:
        chunk_tokens = result.get("metadata", {}).get("token_count", 500)
        if total_tokens + chunk_tokens <= max_tokens:
            selected_chunks.append(result["chunk_id"])
            total_tokens += chunk_tokens
        else:
            break

    return await client.generate_summary(
        query,
        selected_chunks,
        model="openai:gpt-4o-mini"
    )
```

### 4. Validate Documents Before Upload

```python
from pathlib import Path

def validate_document(file_path: Path) -> bool:
    """Validate document before upload."""

    # Check file exists
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return False

    # Check file size (max 100MB)
    max_size = 100 * 1024 * 1024
    if file_path.stat().st_size > max_size:
        print(f"File too large: {file_path.stat().st_size / 1024 / 1024:.1f}MB")
        return False

    # Check file type
    allowed_extensions = {".pdf", ".docx", ".txt", ".md", ".csv"}
    if file_path.suffix.lower() not in allowed_extensions:
        print(f"Unsupported format: {file_path.suffix}")
        return False

    return True

# Usage
if validate_document(Path("paper.pdf")):
    await client.upload_document(Path("paper.pdf"), title="Paper")
```

---

## Performance Tips

### 1. Use Connection Pooling

```python
# Create one client, reuse for all requests
client = httpx.AsyncClient(
    timeout=120.0,
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100
    )
)

# Reuse across requests
for query in queries:
    results = await client.post(url, json={"query": query})
```

### 2. Batch Operations

```python
# Bad - sequential uploads
for file in files:
    await upload_document(file)

# Good - parallel uploads (limit concurrency)
async def batch_upload_limited(files: List[Path], max_concurrent: int = 3):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def upload_with_limit(file):
        async with semaphore:
            return await upload_document(file)

    return await asyncio.gather(*[upload_with_limit(f) for f in files])
```

### 3. Choose Appropriate Model

```python
def select_model_by_complexity(query: str, chunks: List[Dict]) -> str:
    """Choose cost-effective model based on complexity."""

    total_tokens = sum(
        chunk.get("metadata", {}).get("token_count", 500)
        for chunk in chunks
    )

    # Simple queries, short context
    if len(query.split()) < 10 and total_tokens < 2000:
        return "openai:gpt-4o-mini"  # $0.15/1M tokens

    # Long context
    if total_tokens > 20000:
        return "anthropic:claude-3-5-sonnet-20241022"  # Better long context

    # Default balanced option
    return "openai:gpt-4o-mini"
```

### 4. Monitor Rate Limits

```python
from collections import deque
from time import time

class RateLimiter:
    """Client-side rate limiter."""

    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    async def acquire(self):
        """Wait if rate limit exceeded."""
        now = time()

        # Remove old requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # Wait if at limit
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.requests.append(now)

# Usage: 10 requests per second
rate_limiter = RateLimiter(max_requests=10, time_window=1.0)

async def rate_limited_search(query: str):
    await rate_limiter.acquire()
    return await client.search(query)
```

---

## Advanced Patterns

### Streaming Results (Future Feature)

```python
# When streaming is implemented
async def stream_generation(query: str, chunk_ids: List[str]):
    """Stream LLM responses as they generate."""

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{base_url}/generate/summary/stream",
            json={"query": query, "chunk_ids": chunk_ids}
        ) as response:
            async for chunk in response.aiter_text():
                # Display partial results in real-time
                print(chunk, end="", flush=True)
```

### Multi-Document Comparison

```python
async def compare_documents(doc_ids: List[str], query: str) -> Dict[str, str]:
    """Generate summaries for specific documents."""

    results = {}

    for doc_id in doc_ids:
        # Search within specific document
        search_results = await client.search(
            query,
            document_filter=doc_id  # If implemented
        )

        chunk_ids = [r["chunk_id"] for r in search_results[:5]]

        summary = await client.generate_summary(query, chunk_ids)
        results[doc_id] = summary

    return results
```

---

## Testing

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_search_workflow():
    """Test search workflow."""

    client = RaasClient()

    # Mock HTTP responses
    with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = {
            "results": [
                {"chunk_id": "test-id", "score": 0.9, "content": "test"}
            ]
        }

        results = await client.search("test query")

        assert len(results) == 1
        assert results[0]["chunk_id"] == "test-id"
        mock_post.assert_called_once()
```

---

## Support

- **Interactive API Docs:** http://localhost:8000/docs
- **Issues:** https://github.com/your-repo/issues
- **Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md)
