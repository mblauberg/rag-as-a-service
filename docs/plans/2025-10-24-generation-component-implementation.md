# Generation Component Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add RAG (Retrieval-Augmented Generation) capability to RAAS by integrating Ollama LLM with a new Generator microservice that produces cited summaries from search results.

**Architecture:** Build a new Generator microservice (FastAPI, port 8002) that receives search chunks from the API service, formats them with citation markers, calls Ollama for synthesis, and returns summaries with inline citations. Frontend displays summary at top with clickable citation links to corresponding chunks below.

**Tech Stack:** FastAPI, Ollama, ollama-python, Poetry, Docker, Kubernetes, React, TypeScript

---

## Phase 1: Generator Service Core (Tasks 1-8)

### Task 1: Create Generator Service Structure

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/pyproject.toml`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/__init__.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/main.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/config.py`

**Step 1: Create service directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator/app`

**Step 2: Create pyproject.toml**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/pyproject.toml`:

```toml
[tool.poetry]
name = "raas-generator"
version = "0.1.0"
description = "RAG generation service for RAAS"
authors = ["RAAS Team"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"
ollama = "^0.3.0"
httpx = "^0.25.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
httpx = "^0.25.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Step 3: Create config.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/config.py`:

```python
"""Configuration for Generator service."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"
    max_chunks: int = 5
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 4: Create main.py with basic app**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/main.py`:

```python
"""Main FastAPI application for Generator service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RAAS Generator Service",
    description="RAG generation service using Ollama",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    return {"status": "ready"}
```

**Step 5: Create __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/__init__.py`:

```python
"""Generator service package."""
```

**Step 6: Install dependencies**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && poetry install`

**Step 7: Test basic app**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8002 &`
Run: `sleep 2 && curl http://localhost:8002/health`
Expected: `{"status":"healthy"}`
Run: `pkill -f "uvicorn app.main:app"`

**Step 8: Commit**

```bash
git add services/generator/
git commit -m "feat: initialize Generator service with FastAPI structure"
```

---

### Task 2: Create Pydantic Schemas

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/models/__init__.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/models/schemas.py`

**Step 1: Create models directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator/app/models`

**Step 2: Create schemas.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/models/schemas.py`:

```python
"""Pydantic schemas for Generator service."""
from pydantic import BaseModel, Field
from typing import List, Optional


class ChunkInput(BaseModel):
    """Input chunk for generation."""
    text: str = Field(..., description="Chunk text content")
    document_id: str = Field(..., description="Document ID")
    chunk_index: int = Field(..., description="Chunk index in document")


class GenerateRequest(BaseModel):
    """Request for text generation."""
    query: str = Field(..., description="User query")
    chunks: List[ChunkInput] = Field(..., description="Context chunks")
    model: str = Field(default="llama3.2", description="Model to use")


class GenerateResponse(BaseModel):
    """Response from generation."""
    summary: str = Field(..., description="Generated summary with citations")
    model_used: str = Field(..., description="Model that was used")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")


class ModelInfo(BaseModel):
    """Information about an available model."""
    name: str = Field(..., description="Model name")
    size: str = Field(..., description="Model size")
    modified_at: str = Field(..., description="Last modified timestamp")


class ModelsResponse(BaseModel):
    """Response listing available models."""
    models: List[ModelInfo] = Field(..., description="Available models")
```

**Step 3: Create __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/models/__init__.py`:

```python
"""Models package."""
from .schemas import (
    ChunkInput,
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ModelsResponse
)

__all__ = [
    'ChunkInput',
    'GenerateRequest',
    'GenerateResponse',
    'ModelInfo',
    'ModelsResponse'
]
```

**Step 4: Commit**

```bash
git add services/generator/app/models/
git commit -m "feat: add Pydantic schemas for Generator service"
```

---

### Task 3: Create Ollama Client Service

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/services/__init__.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/services/ollama_client.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/test_ollama_client.py`

**Step 1: Create services directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator/app/services`

**Step 2: Create tests directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator/tests`

**Step 3: Write failing test**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/test_ollama_client.py`:

```python
"""Tests for Ollama client."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.ollama_client import OllamaClient


@pytest.mark.asyncio
async def test_generate_calls_ollama():
    """Test that generate calls Ollama with correct parameters."""
    client = OllamaClient(url="http://localhost:11434")

    with patch('ollama.AsyncClient.generate', new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = {
            'response': 'Test response',
            'eval_count': 100
        }

        result = await client.generate(
            prompt="Test prompt",
            model="llama3.2"
        )

        assert result['response'] == 'Test response'
        assert result['eval_count'] == 100
        mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_list_models():
    """Test listing available models."""
    client = OllamaClient(url="http://localhost:11434")

    with patch('ollama.AsyncClient.list', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {
            'models': [
                {'name': 'llama3.2', 'size': 2000000000, 'modified_at': '2024-01-01T00:00:00Z'}
            ]
        }

        models = await client.list_models()

        assert len(models) == 1
        assert models[0]['name'] == 'llama3.2'


@pytest.mark.asyncio
async def test_check_health_success():
    """Test health check when Ollama is available."""
    client = OllamaClient(url="http://localhost:11434")

    with patch('ollama.AsyncClient.list', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {'models': []}

        is_healthy = await client.check_health()

        assert is_healthy is True


@pytest.mark.asyncio
async def test_check_health_failure():
    """Test health check when Ollama is unavailable."""
    client = OllamaClient(url="http://localhost:11434")

    with patch('ollama.AsyncClient.list', new_callable=AsyncMock) as mock_list:
        mock_list.side_effect = Exception("Connection failed")

        is_healthy = await client.check_health()

        assert is_healthy is False
```

**Step 4: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && poetry run pytest tests/test_ollama_client.py -v`
Expected: FAIL - "No module named 'app.services.ollama_client'"

**Step 5: Implement Ollama client**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/services/ollama_client.py`:

```python
"""Ollama client wrapper."""
import logging
from typing import Dict, List, Any
import ollama

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for Ollama API."""

    def __init__(self, url: str = "http://localhost:11434"):
        """Initialize Ollama client."""
        self.url = url
        self.client = ollama.AsyncClient(host=url)

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generation result with 'response' and 'eval_count'
        """
        try:
            response = await self.client.generate(
                model=model,
                prompt=prompt,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )
            return response
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.

        Returns:
            List of model dictionaries
        """
        try:
            response = await self.client.list()
            return response.get('models', [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise

    async def check_health(self) -> bool:
        """
        Check if Ollama is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            await self.client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
```

**Step 6: Create __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/services/__init__.py`:

```python
"""Services package."""
from .ollama_client import OllamaClient

__all__ = ['OllamaClient']
```

**Step 7: Run tests to verify they pass**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && poetry run pytest tests/test_ollama_client.py -v`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add services/generator/app/services/ services/generator/tests/
git commit -m "feat: add Ollama client with async API wrapper"
```

---

### Task 4: Create Prompt Service

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/services/prompt_service.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/test_prompt_service.py`

**Step 1: Write failing test**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/test_prompt_service.py`:

```python
"""Tests for prompt service."""
import pytest
from app.services.prompt_service import PromptService
from app.models.schemas import ChunkInput


def test_format_chunks_with_citations():
    """Test formatting chunks with citation markers."""
    service = PromptService()
    chunks = [
        ChunkInput(text="First chunk content", document_id="doc1", chunk_index=0),
        ChunkInput(text="Second chunk content", document_id="doc2", chunk_index=1),
    ]

    formatted = service.format_chunks_with_citations(chunks)

    assert "[1]" in formatted
    assert "[2]" in formatted
    assert "First chunk content" in formatted
    assert "Second chunk content" in formatted


def test_build_prompt():
    """Test building complete RAG prompt."""
    service = PromptService()
    chunks = [
        ChunkInput(text="Chunk about cats", document_id="doc1", chunk_index=0),
    ]
    query = "What are cats?"

    prompt = service.build_prompt(query, chunks)

    assert query in prompt
    assert "Chunk about cats" in prompt
    assert "[1]" in prompt
    assert "Answer with inline citations" in prompt or "cite" in prompt.lower()


def test_empty_chunks():
    """Test handling empty chunks list."""
    service = PromptService()
    prompt = service.build_prompt("Test query", [])

    assert "Test query" in prompt
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && poetry run pytest tests/test_prompt_service.py -v`
Expected: FAIL - Module not found

**Step 3: Implement prompt service**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/services/prompt_service.py`:

```python
"""Prompt template service for RAG."""
from typing import List
from app.models.schemas import ChunkInput


class PromptService:
    """Service for building RAG prompts with citations."""

    RAG_TEMPLATE = """You are a helpful assistant. Answer the user's question based ONLY on the provided context.
Cite sources using [1], [2], etc. to reference the document chunks.

Context:
{context}

Question: {query}

Answer with inline citations:"""

    def format_chunks_with_citations(self, chunks: List[ChunkInput]) -> str:
        """
        Format chunks with citation markers.

        Args:
            chunks: List of chunk inputs

        Returns:
            Formatted context string with citations
        """
        if not chunks:
            return "No context available."

        formatted_chunks = []
        for idx, chunk in enumerate(chunks, start=1):
            formatted_chunks.append(f"[{idx}] {chunk.text}")

        return "\n\n".join(formatted_chunks)

    def build_prompt(self, query: str, chunks: List[ChunkInput]) -> str:
        """
        Build complete RAG prompt.

        Args:
            query: User query
            chunks: Context chunks

        Returns:
            Complete prompt string
        """
        context = self.format_chunks_with_citations(chunks)
        prompt = self.RAG_TEMPLATE.format(
            context=context,
            query=query
        )
        return prompt
```

**Step 4: Update services __init__.py**

Edit `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/services/__init__.py`:

```python
"""Services package."""
from .ollama_client import OllamaClient
from .prompt_service import PromptService

__all__ = ['OllamaClient', 'PromptService']
```

**Step 5: Run tests to verify they pass**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && poetry run pytest tests/test_prompt_service.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add services/generator/app/services/ services/generator/tests/
git commit -m "feat: add prompt service with RAG template and citations"
```

---

### Task 5: Create Generation Endpoint

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/__init__.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/routes/__init__.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/routes/generate.py`
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/main.py`

**Step 1: Create API directory structure**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator/app/api/routes`

**Step 2: Create generation route**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/routes/generate.py`:

```python
"""Generation endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services.ollama_client import OllamaClient
from app.services.prompt_service import PromptService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
ollama_client = OllamaClient(url=settings.ollama_url)
prompt_service = PromptService()


@router.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest) -> GenerateResponse:
    """
    Generate summary from chunks using RAG.

    Args:
        request: Generation request with query and chunks

    Returns:
        Generated summary with citations
    """
    try:
        # Limit chunks to max_chunks
        chunks = request.chunks[:settings.max_chunks]

        # Build prompt
        prompt = prompt_service.build_prompt(request.query, chunks)

        # Generate response
        model = request.model or settings.default_model
        result = await ollama_client.generate(
            prompt=prompt,
            model=model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )

        return GenerateResponse(
            summary=result['response'],
            model_used=model,
            tokens_used=result.get('eval_count')
        )

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )
```

**Step 3: Create routes __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/routes/__init__.py`:

```python
"""API routes package."""
```

**Step 4: Create api __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/__init__.py`:

```python
"""API package."""
```

**Step 5: Update main.py to include router**

Edit `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/main.py`:

```python
"""Main FastAPI application for Generator service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import generate

app = FastAPI(
    title="RAAS Generator Service",
    description="RAG generation service using Ollama",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router, prefix="/api/v1", tags=["generation"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    from app.services.ollama_client import OllamaClient
    from app.config import settings

    client = OllamaClient(url=settings.ollama_url)
    is_healthy = await client.check_health()

    if not is_healthy:
        return {"status": "not_ready", "reason": "Ollama unavailable"}

    return {"status": "ready"}
```

**Step 6: Commit**

```bash
git add services/generator/app/api/ services/generator/app/main.py
git commit -m "feat: add generation endpoint with RAG logic"
```

---

### Task 6: Create Models Endpoint

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/routes/models.py`
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/main.py`

**Step 1: Create models route**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/api/routes/models.py`:

```python
"""Models listing endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ModelsResponse, ModelInfo
from app.services.ollama_client import OllamaClient
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
ollama_client = OllamaClient(url=settings.ollama_url)


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    """
    List available Ollama models.

    Returns:
        List of available models
    """
    try:
        models_data = await ollama_client.list_models()

        models = [
            ModelInfo(
                name=model['name'],
                size=_format_size(model.get('size', 0)),
                modified_at=model.get('modified_at', 'unknown')
            )
            for model in models_data
        ]

        return ModelsResponse(models=models)

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


def _format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"
```

**Step 2: Update main.py**

Edit `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/app/main.py`:

```python
"""Main FastAPI application for Generator service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import generate, models

app = FastAPI(
    title="RAAS Generator Service",
    description="RAG generation service using Ollama",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router, prefix="/api/v1", tags=["generation"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    from app.services.ollama_client import OllamaClient
    from app.config import settings

    client = OllamaClient(url=settings.ollama_url)
    is_healthy = await client.check_health()

    if not is_healthy:
        return {"status": "not_ready", "reason": "Ollama unavailable"}

    return {"status": "ready"}
```

**Step 3: Commit**

```bash
git add services/generator/app/api/routes/models.py services/generator/app/main.py
git commit -m "feat: add models listing endpoint"
```

---

### Task 7: Create Generator Dockerfile

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/Dockerfile`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/.dockerignore`

**Step 1: Create Dockerfile**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --no-dev

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8002

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

**Step 2: Create .dockerignore**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/.dockerignore`:

```
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.env
tests/
*.md
.git/
```

**Step 3: Test build**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && docker build -t raas-generator:test .`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add services/generator/Dockerfile services/generator/.dockerignore
git commit -m "feat: add Dockerfile for Generator service"
```

---

### Task 8: Create Generator Tests

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/__init__.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/conftest.py`
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/test_api.py`

**Step 1: Create __init__.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/__init__.py`:

```python
"""Tests package."""
```

**Step 2: Create conftest.py**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/conftest.py`:

```python
"""Pytest configuration."""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def client():
    """Test client fixture."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

**Step 3: Create API tests**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/services/generator/tests/test_api.py`:

```python
"""API endpoint tests."""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_generate_endpoint(client):
    """Test generate endpoint."""
    with patch('app.api.routes.generate.ollama_client.generate', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {
            'response': 'Test summary [1]',
            'eval_count': 50
        }

        request_data = {
            "query": "What is this about?",
            "chunks": [
                {"text": "Test chunk", "document_id": "doc1", "chunk_index": 0}
            ],
            "model": "llama3.2"
        }

        response = await client.post("/api/v1/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data["model_used"] == "llama3.2"


@pytest.mark.asyncio
async def test_list_models_endpoint(client):
    """Test models listing endpoint."""
    with patch('app.api.routes.models.ollama_client.list_models', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {'name': 'llama3.2', 'size': 2000000000, 'modified_at': '2024-01-01T00:00:00Z'}
        ]

        response = await client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 1
```

**Step 4: Run tests**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/services/generator && poetry run pytest tests/test_api.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/generator/tests/
git commit -m "test: add API endpoint tests for Generator service"
```

---

## Phase 2: Infrastructure - Docker Compose & Kubernetes (Tasks 9-17)

### Task 9: Update Docker Compose - Add Ollama Service

**Files:**
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/docker-compose/docker-compose.yml`

**Step 1: Read current docker-compose.yml**

Run: `cat /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/infrastructure/docker-compose/docker-compose.yml`

**Step 2: Add Ollama service**

Add to `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/docker-compose/docker-compose.yml` in the `services:` section:

```yaml
  ollama:
    image: ollama/ollama:latest
    container_name: raas-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - raas-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

**Step 3: Add volume for Ollama**

Add to the `volumes:` section:

```yaml
  ollama-data:
```

**Step 4: Commit**

```bash
git add infrastructure/docker-compose/docker-compose.yml
git commit -m "feat: add Ollama service to docker-compose"
```

---

### Task 10: Update Docker Compose - Add Generator Service

**Files:**
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/docker-compose/docker-compose.yml`

**Step 1: Add Generator service**

Add to `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/docker-compose/docker-compose.yml` in the `services:` section:

```yaml
  generator:
    build:
      context: ../../services/generator
      dockerfile: Dockerfile
    container_name: raas-generator
    ports:
      - "8002:8002"
    environment:
      - OLLAMA_URL=http://ollama:11434
      - DEFAULT_MODEL=llama3.2
      - MAX_CHUNKS=5
      - TEMPERATURE=0.1
      - MAX_TOKENS=2000
      - TIMEOUT=30
    depends_on:
      ollama:
        condition: service_healthy
    networks:
      - raas-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s
```

**Step 2: Test docker-compose configuration**

Run: `cd /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/infrastructure/docker-compose && docker-compose config`
Expected: No errors in YAML syntax

**Step 3: Commit**

```bash
git add infrastructure/docker-compose/docker-compose.yml
git commit -m "feat: add Generator service to docker-compose"
```

---

### Task 11: Update Docker Compose - Update API Service

**Files:**
- Modify: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/docker-compose/docker-compose.yml`

**Step 1: Add GENERATOR_URL to API service environment**

Update the `api:` service in `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/docker-compose/docker-compose.yml`:

Find the `environment:` section under `api:` and add:

```yaml
      - GENERATOR_URL=http://generator:8002
```

**Step 2: Add dependency on generator**

Update the `depends_on:` section under `api:` to include:

```yaml
      generator:
        condition: service_healthy
```

**Step 3: Commit**

```bash
git add infrastructure/docker-compose/docker-compose.yml
git commit -m "feat: configure API service to use Generator service"
```

---

### Task 12: Create Ollama Init Script

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/scripts/init-ollama.sh`

**Step 1: Create init script**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/scripts/init-ollama.sh`:

```bash
#!/bin/bash
# Initialize Ollama with default models

set -e

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
DEFAULT_MODELS="${DEFAULT_MODELS:-llama3.2}"

echo "Waiting for Ollama to be ready..."
until curl -sf "$OLLAMA_URL/api/tags" > /dev/null; do
  echo "Ollama not ready, waiting..."
  sleep 5
done

echo "Ollama is ready. Pulling models..."

IFS=',' read -ra MODELS <<< "$DEFAULT_MODELS"
for model in "${MODELS[@]}"; do
  echo "Pulling model: $model"
  curl -X POST "$OLLAMA_URL/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$model\"}" \
    --max-time 600
  echo "Model $model pulled successfully"
done

echo "All models initialized"
```

**Step 2: Make executable**

Run: `chmod +x /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/infrastructure/scripts/init-ollama.sh`

**Step 3: Commit**

```bash
git add infrastructure/scripts/init-ollama.sh
git commit -m "feat: add Ollama initialization script"
```

---

### Task 13: Create Kubernetes - Ollama PVC

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/ollama/pvc.yaml`

**Step 1: Create ollama directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/infrastructure/k8s/base/ollama`

**Step 2: Create PVC manifest**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/ollama/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-data
  namespace: raas
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
```

**Step 3: Commit**

```bash
git add infrastructure/k8s/base/ollama/
git commit -m "feat: add Ollama PVC for Kubernetes"
```

---

### Task 14: Create Kubernetes - Ollama Deployment

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/ollama/deployment.yaml`

**Step 1: Create deployment manifest**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/ollama/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: raas
  labels:
    app: ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      initContainers:
      - name: init-models
        image: curlimages/curl:latest
        command: ["/bin/sh"]
        args:
          - -c
          - |
            echo "Waiting for Ollama to be ready..."
            until curl -sf http://localhost:11434/api/tags > /dev/null; do
              echo "Waiting..."
              sleep 5
            done

            echo "Pulling default model: llama3.2"
            curl -X POST http://localhost:11434/api/pull \
              -H "Content-Type: application/json" \
              -d '{"name": "llama3.2"}' \
              --max-time 600

            echo "Model pulled successfully"
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
          name: http
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
        resources:
          requests:
            cpu: 1000m
            memory: 2Gi
          limits:
            cpu: 4000m
            memory: 8Gi
        livenessProbe:
          httpGet:
            path: /api/tags
            port: 11434
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /api/tags
            port: 11434
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
      volumes:
      - name: ollama-data
        persistentVolumeClaim:
          claimName: ollama-data
```

**Step 2: Commit**

```bash
git add infrastructure/k8s/base/ollama/deployment.yaml
git commit -m "feat: add Ollama deployment for Kubernetes"
```

---

### Task 15: Create Kubernetes - Ollama Service

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/ollama/service.yaml`

**Step 1: Create service manifest**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/ollama/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: raas
  labels:
    app: ollama
spec:
  type: ClusterIP
  ports:
  - port: 11434
    targetPort: 11434
    protocol: TCP
    name: http
  selector:
    app: ollama
```

**Step 2: Commit**

```bash
git add infrastructure/k8s/base/ollama/service.yaml
git commit -m "feat: add Ollama service for Kubernetes"
```

---

### Task 16: Create Kubernetes - Generator ConfigMap

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/generator/configmap.yaml`

**Step 1: Create generator directory**

Run: `mkdir -p /Users/user/Documents/01_Active/UQ/INFS3208/Individual\ Project/raas/infrastructure/k8s/base/generator`

**Step 2: Create ConfigMap**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/generator/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: generator-config
  namespace: raas
data:
  OLLAMA_URL: "http://ollama:11434"
  DEFAULT_MODEL: "llama3.2"
  MAX_CHUNKS: "5"
  TEMPERATURE: "0.1"
  MAX_TOKENS: "2000"
  TIMEOUT: "30"
```

**Step 3: Commit**

```bash
git add infrastructure/k8s/base/generator/configmap.yaml
git commit -m "feat: add Generator ConfigMap for Kubernetes"
```

---

### Task 17: Create Kubernetes - Generator Deployment

**Files:**
- Create: `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/generator/deployment.yaml`

**Step 1: Create deployment manifest**

Create `/Users/user/Documents/01_Active/UQ/INFS3208/Individual Project/raas/infrastructure/k8s/base/generator/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: generator
  namespace: raas
  labels:
    app: generator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: generator
  template:
    metadata:
      labels:
        app: generator
    spec:
      containers:
      - name: generator
        image: raas-generator:latest
        imagePullPolicy: Never  # For local development
        ports:
        - containerPort: 8002
          name: http
        envFrom:
        - configMapRef:
            name: generator-config
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /ready
            port: 8002
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
```

**Step 2: Commit**

```bash
git add infrastructure/k8s/base/generator/deployment.yaml
git commit -m "feat: add Generator deployment for Kubernetes"
```

---

## Summary

This plan implements the Generation Component infrastructure in two phases:

**Phase 1 (Tasks 1-8):** Core Generator service
- Service structure with FastAPI
- Pydantic schemas
- Ollama client wrapper
- Prompt service with RAG template
- Generation and models endpoints
- Dockerfile and tests

**Phase 2 (Tasks 9-17):** Infrastructure
- Docker Compose: Ollama + Generator services
- Kubernetes: PVC, Deployments, Services, ConfigMaps
- Initialization scripts

**Not included in this plan:**
- API service modifications (Tasks 18-20)
- Frontend integration (Tasks 21-25)
- End-to-end testing (Tasks 26-27)

**Execution Time:**
- Phase 1: ~2-3 hours
- Phase 2: ~1-2 hours

**Total:** ~3-5 hours for infrastructure setup
