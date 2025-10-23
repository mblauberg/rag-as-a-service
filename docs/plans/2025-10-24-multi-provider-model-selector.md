# Multi-Provider Model Selector Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate model selector into search bar with multi-provider architecture supporting Ollama, OpenAI, Anthropic, and Google models.

**Architecture:** Provider abstraction layer with registry pattern on backend, enhanced TypeScript types and Radix UI dropdown on frontend. Environment-based provider configuration enables gradual rollout.

**Tech Stack:** FastAPI, Pydantic, OpenAI SDK, Anthropic SDK, Google GenAI SDK, React, TypeScript, Radix UI, Tailwind CSS

---

## Phase 1: Backend Foundation

### Task 1: Create Provider Abstract Base Class

**Files:**
- Create: `services/generator/app/providers/__init__.py`
- Create: `services/generator/app/providers/base.py`
- Create: `tests/unit/providers/__init__.py`
- Create: `tests/unit/providers/test_base.py`

**Step 1: Write the failing test**

Create `tests/unit/providers/test_base.py`:

```python
import pytest
from app.providers.base import ModelProvider


def test_model_provider_is_abstract():
    """ModelProvider cannot be instantiated directly"""
    with pytest.raises(TypeError):
        ModelProvider()


def test_model_provider_requires_list_models():
    """Subclass must implement list_models"""
    class IncompleteProvider(ModelProvider):
        async def generate(self, model: str, prompt: str, context: str) -> str:
            return ""

        def is_available(self) -> bool:
            return True

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_model_provider_requires_generate():
    """Subclass must implement generate"""
    class IncompleteProvider(ModelProvider):
        async def list_models(self):
            return []

        def is_available(self) -> bool:
            return True

    with pytest.raises(TypeError):
        IncompleteProvider()


def test_model_provider_requires_is_available():
    """Subclass must implement is_available"""
    class IncompleteProvider(ModelProvider):
        async def list_models(self):
            return []

        async def generate(self, model: str, prompt: str, context: str) -> str:
            return ""

    with pytest.raises(TypeError):
        IncompleteProvider()
```

**Step 2: Run test to verify it fails**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_base.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.providers.base'"

**Step 3: Write minimal implementation**

Create `services/generator/app/providers/__init__.py`:

```python
"""Provider abstraction layer for multi-LLM support."""
```

Create `services/generator/app/providers/base.py`:

```python
"""Abstract base class for model providers."""
from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import Model


class ModelProvider(ABC):
    """Abstract base class for LLM providers (Ollama, OpenAI, Anthropic, Google)."""

    @abstractmethod
    async def list_models(self) -> List[Model]:
        """
        Return list of available models from this provider.

        Returns:
            List of Model objects with provider-specific metadata
        """
        pass

    @abstractmethod
    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using provider's API.

        Args:
            model: Model identifier (e.g., "llama3.3:70b", "openai:gpt-5")
            prompt: User query or instruction
            context: Retrieved document chunks as context

        Returns:
            Generated summary text

        Raises:
            ValueError: If model not found
            RuntimeError: If generation fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is configured and accessible.

        Returns:
            True if provider can be used, False otherwise
        """
        pass
```

Create `tests/unit/providers/__init__.py`:

```python
"""Unit tests for provider implementations."""
```

**Step 4: Run test to verify it passes**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_base.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add services/generator/app/providers/ services/generator/tests/unit/providers/
git commit -m "feat(generator): add provider abstract base class

- Define ModelProvider ABC with list_models, generate, is_available
- Add comprehensive tests for abstract interface enforcement
- Foundation for multi-provider architecture"
```

---

### Task 2: Enhance Model Schema

**Files:**
- Modify: `services/generator/app/models/schemas.py`
- Modify: `tests/test_schemas.py`

**Step 1: Write the failing test**

Add to `tests/test_schemas.py`:

```python
def test_model_info_with_provider_fields():
    """Model schema includes provider, display_name, description, capabilities"""
    model = Model(
        name="openai:gpt-5",
        display_name="GPT-5",
        provider="openai",
        size="N/A",
        description="Best intelligence, coding/math excellence",
        capabilities=["reasoning", "coding", "creative"],
        modified_at="2025-10-24T10:00:00Z"
    )

    assert model.name == "openai:gpt-5"
    assert model.display_name == "GPT-5"
    assert model.provider == "openai"
    assert model.description == "Best intelligence, coding/math excellence"
    assert "reasoning" in model.capabilities
    assert len(model.capabilities) == 3
```

**Step 2: Run test to verify it fails**

```bash
cd services/generator
poetry run pytest tests/test_schemas.py::test_model_info_with_provider_fields -v
```

Expected: FAIL with validation error or missing fields

**Step 3: Update Model schema**

In `services/generator/app/models/schemas.py`, update the Model class:

```python
class Model(BaseModel):
    """Model information with provider details."""
    name: str  # Unique identifier (e.g., "llama3.3:70b", "openai:gpt-5")
    display_name: str  # Human-readable name (e.g., "Llama 3.3 70B", "GPT-5")
    provider: str  # Provider name: "ollama", "openai", "anthropic", "google"
    size: str  # Model size (e.g., "8B", "70B", "N/A" for API models)
    description: str = ""  # Capability description
    capabilities: List[str] = []  # ["reasoning", "coding", "creative"]
    modified_at: str  # ISO 8601 timestamp
```

**Step 4: Run test to verify it passes**

```bash
cd services/generator
poetry run pytest tests/test_schemas.py::test_model_info_with_provider_fields -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/generator/app/models/schemas.py services/generator/tests/test_schemas.py
git commit -m "feat(generator): enhance Model schema with provider fields

- Add display_name, provider, description, capabilities
- Update tests to verify new fields
- Backward compatible with optional defaults"
```

---

### Task 3: Create Provider Registry

**Files:**
- Create: `services/generator/app/providers/registry.py`
- Create: `tests/unit/providers/test_registry.py`

**Step 1: Write the failing test**

Create `tests/unit/providers/test_registry.py`:

```python
import pytest
from app.providers.registry import ProviderRegistry
from app.providers.base import ModelProvider
from app.models.schemas import Model


class MockProvider(ModelProvider):
    """Mock provider for testing."""

    def __init__(self, name: str, models: list, available: bool = True):
        self._name = name
        self._models = models
        self._available = available

    async def list_models(self):
        return self._models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        return f"Generated by {self._name}"

    def is_available(self) -> bool:
        return self._available


@pytest.mark.asyncio
async def test_registry_initialization():
    """Registry starts empty"""
    registry = ProviderRegistry()
    assert len(registry.providers) == 0


@pytest.mark.asyncio
async def test_register_available_provider():
    """Register provider that is available"""
    registry = ProviderRegistry()
    provider = MockProvider("test", [], available=True)

    registry.register("test", provider)

    assert "test" in registry.providers
    assert registry.providers["test"] == provider


@pytest.mark.asyncio
async def test_skip_unavailable_provider():
    """Do not register provider that is unavailable"""
    registry = ProviderRegistry()
    provider = MockProvider("test", [], available=False)

    registry.register("test", provider)

    assert "test" not in registry.providers


@pytest.mark.asyncio
async def test_list_all_models_aggregates():
    """list_all_models aggregates from all providers"""
    model1 = Model(
        name="test1:model1",
        display_name="Model 1",
        provider="test1",
        size="8B",
        description="Test model 1",
        modified_at="2025-10-24T10:00:00Z"
    )
    model2 = Model(
        name="test2:model2",
        display_name="Model 2",
        provider="test2",
        size="70B",
        description="Test model 2",
        modified_at="2025-10-24T10:00:00Z"
    )

    registry = ProviderRegistry()
    registry.register("test1", MockProvider("test1", [model1]))
    registry.register("test2", MockProvider("test2", [model2]))

    models = await registry.list_all_models()

    assert len(models) == 2
    assert model1 in models
    assert model2 in models


@pytest.mark.asyncio
async def test_generate_routes_to_provider():
    """generate routes to correct provider based on model name"""
    registry = ProviderRegistry()
    registry.register("test", MockProvider("test", []))

    result = await registry.generate("test:model", "prompt", "context")

    assert result == "Generated by test"


@pytest.mark.asyncio
async def test_generate_raises_on_unknown_provider():
    """generate raises ValueError for unknown provider"""
    registry = ProviderRegistry()

    with pytest.raises(ValueError, match="Provider not found"):
        await registry.generate("unknown:model", "prompt", "context")
```

**Step 2: Run test to verify it fails**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_registry.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `services/generator/app/providers/registry.py`:

```python
"""Provider registry for managing multiple model providers."""
from typing import Dict, List, Tuple
from app.providers.base import ModelProvider
from app.models.schemas import Model


class ProviderRegistry:
    """Registry for managing and routing between model providers."""

    def __init__(self):
        """Initialize empty registry."""
        self.providers: Dict[str, ModelProvider] = {}

    def register(self, name: str, provider: ModelProvider) -> None:
        """
        Register a provider if it's available.

        Args:
            name: Provider identifier (e.g., "ollama", "openai")
            provider: ModelProvider instance
        """
        if provider.is_available():
            self.providers[name] = provider

    async def list_all_models(self) -> List[Model]:
        """
        Aggregate models from all registered providers.

        Returns:
            Combined list of models from all providers
        """
        models = []
        for provider in self.providers.values():
            provider_models = await provider.list_models()
            models.extend(provider_models)
        return models

    async def generate(self, model_name: str, prompt: str, context: str) -> Tuple[str, str]:
        """
        Route generation request to appropriate provider.

        Args:
            model_name: Full model identifier (e.g., "openai:gpt-5")
            prompt: User query
            context: Retrieved context

        Returns:
            Tuple of (generated_summary, provider_name)

        Raises:
            ValueError: If provider not found
        """
        provider_name = self._extract_provider(model_name)

        if provider_name not in self.providers:
            raise ValueError(f"Provider not found: {provider_name}")

        summary = await self.providers[provider_name].generate(model_name, prompt, context)
        return summary, provider_name

    def _extract_provider(self, model_name: str) -> str:
        """
        Extract provider name from model identifier.

        Args:
            model_name: Full model name (e.g., "openai:gpt-5", "llama3.3:70b")

        Returns:
            Provider name (defaults to "ollama" if no prefix)
        """
        if ":" in model_name:
            parts = model_name.split(":")
            # Check if first part is a provider name
            if parts[0] in ["openai", "anthropic", "google"]:
                return parts[0]

        # Default to ollama for unprefixed models
        return "ollama"
```

**Step 4: Run test to verify it passes**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_registry.py -v
```

Expected: PASS (7 tests)

**Step 5: Commit**

```bash
git add services/generator/app/providers/registry.py services/generator/tests/unit/providers/test_registry.py
git commit -m "feat(generator): add provider registry

- Implement ProviderRegistry for managing multiple providers
- Auto-registration only for available providers
- Model aggregation and routing logic
- Comprehensive unit tests"
```

---

### Task 4: Refactor Ollama as Provider

**Files:**
- Create: `services/generator/app/providers/ollama_provider.py`
- Create: `tests/unit/providers/test_ollama_provider.py`
- Modify: `services/generator/app/services/ollama_client.py` (reference only)

**Step 1: Write the failing test**

Create `tests/unit/providers/test_ollama_provider.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.providers.ollama_provider import OllamaProvider
from app.models.schemas import Model


@pytest.fixture
def ollama_provider():
    """Create OllamaProvider instance for testing."""
    return OllamaProvider(base_url="http://localhost:11434")


@pytest.mark.asyncio
async def test_is_available_when_healthy(ollama_provider):
    """is_available returns True when Ollama is healthy"""
    with patch.object(ollama_provider.client, 'check_health', new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True

        assert ollama_provider.is_available() is True


@pytest.mark.asyncio
async def test_is_available_when_unhealthy(ollama_provider):
    """is_available returns False when Ollama is unhealthy"""
    with patch.object(ollama_provider.client, 'check_health', new_callable=AsyncMock) as mock_health:
        mock_health.return_value = False

        assert ollama_provider.is_available() is False


@pytest.mark.asyncio
async def test_list_models_returns_enhanced_schema(ollama_provider):
    """list_models returns models with enhanced schema"""
    mock_ollama_models = [
        {
            "name": "llama3.3:70b",
            "size": "70B",
            "modified_at": "2025-10-24T10:00:00Z"
        }
    ]

    with patch.object(ollama_provider.client, 'list_models', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_ollama_models

        models = await ollama_provider.list_models()

        assert len(models) == 1
        assert isinstance(models[0], Model)
        assert models[0].name == "llama3.3:70b"
        assert models[0].display_name == "Llama 3.3 70B"
        assert models[0].provider == "ollama"
        assert models[0].size == "70B"
        assert "local" in models[0].description.lower()


@pytest.mark.asyncio
async def test_generate_calls_ollama_client(ollama_provider):
    """generate delegates to ollama_client.generate"""
    with patch.object(ollama_provider.client, 'generate', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Generated summary"

        result = await ollama_provider.generate("llama3.3:70b", "prompt", "context")

        assert result == "Generated summary"
        mock_gen.assert_called_once_with(
            model="llama3.3:70b",
            prompt="prompt",
            context="context"
        )
```

**Step 2: Run test to verify it fails**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_ollama_provider.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `services/generator/app/providers/ollama_provider.py`:

```python
"""Ollama provider implementation."""
from typing import List
from app.providers.base import ModelProvider
from app.models.schemas import Model
from app.services.ollama_client import OllamaClient


class OllamaProvider(ModelProvider):
    """Provider for locally-hosted Ollama models."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama API endpoint
        """
        self.client = OllamaClient(base_url=base_url)

    def is_available(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            # Sync wrapper for async health check
            import asyncio
            return asyncio.run(self.client.check_health())
        except Exception:
            return False

    async def list_models(self) -> List[Model]:
        """
        List available Ollama models with enhanced schema.

        Returns:
            List of Model objects with Ollama-specific metadata
        """
        ollama_models = await self.client.list_models()

        models = []
        for om in ollama_models:
            model = Model(
                name=om["name"],
                display_name=self._format_display_name(om["name"]),
                provider="ollama",
                size=om.get("size", "Unknown"),
                description=self._generate_description(om["name"]),
                capabilities=["local", "offline"],
                modified_at=om.get("modified_at", "")
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using Ollama.

        Args:
            model: Ollama model name (e.g., "llama3.3:70b")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary
        """
        return await self.client.generate(model=model, prompt=prompt, context=context)

    def _format_display_name(self, name: str) -> str:
        """
        Format Ollama model name for display.

        Args:
            name: Raw model name (e.g., "llama3.3:70b")

        Returns:
            Formatted name (e.g., "Llama 3.3 70B")
        """
        # "llama3.3:70b" -> "Llama 3.3 70B"
        parts = name.split(":")
        model_name = parts[0].replace("llama", "Llama").replace("qwen", "Qwen")
        size = parts[1].upper() if len(parts) > 1 else ""
        return f"{model_name} {size}".strip()

    def _generate_description(self, name: str) -> str:
        """
        Generate description based on model name.

        Args:
            name: Model name

        Returns:
            Description string
        """
        name_lower = name.lower()

        if "llama" in name_lower:
            if "70b" in name_lower or "405b" in name_lower:
                return "Large local model, excellent reasoning and coding"
            else:
                return "Fast local model, good for general queries"
        elif "qwen" in name_lower:
            return "Multilingual local model, strong reasoning"
        else:
            return "Local Ollama model"
```

**Step 4: Run test to verify it passes**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_ollama_provider.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add services/generator/app/providers/ollama_provider.py services/generator/tests/unit/providers/test_ollama_provider.py
git commit -m "feat(generator): implement OllamaProvider

- Wrap existing ollama_client in provider interface
- Add display name formatting and description generation
- Comprehensive tests for provider behavior"
```

---

## Phase 2: API Provider Implementations

### Task 5: Add Dependencies for API Providers

**Files:**
- Modify: `services/generator/pyproject.toml`

**Step 1: Add dependencies to pyproject.toml**

In `services/generator/pyproject.toml`, add to `[tool.poetry.dependencies]`:

```toml
openai = "^1.54.0"
anthropic = "^0.39.0"
google-generativeai = "^0.8.3"
```

**Step 2: Update lock file and install**

```bash
cd services/generator
poetry lock
poetry install
```

Expected: Dependencies installed successfully

**Step 3: Commit**

```bash
git add services/generator/pyproject.toml services/generator/poetry.lock
git commit -m "feat(generator): add API provider dependencies

- Add openai, anthropic, google-generativeai SDKs
- Update poetry.lock"
```

---

### Task 6: Implement OpenAI Provider

**Files:**
- Create: `services/generator/app/providers/openai_provider.py`
- Create: `tests/unit/providers/test_openai_provider.py`

**Step 1: Write the failing test**

Create `tests/unit/providers/test_openai_provider.py`:

```python
import pytest
from unittest.mock import Mock, patch
from app.providers.openai_provider import OpenAIProvider
from app.models.schemas import Model


@pytest.fixture
def openai_provider():
    """Create OpenAIProvider for testing."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        return OpenAIProvider()


def test_is_available_with_api_key():
    """is_available returns True when API key is set"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        provider = OpenAIProvider()
        assert provider.is_available() is True


def test_is_available_without_api_key():
    """is_available returns False when API key is missing"""
    with patch.dict('os.environ', {}, clear=True):
        provider = OpenAIProvider()
        assert provider.is_available() is False


@pytest.mark.asyncio
async def test_list_models_returns_openai_models(openai_provider):
    """list_models returns predefined OpenAI models"""
    models = await openai_provider.list_models()

    assert len(models) >= 3  # gpt-5, gpt-5-mini, gpt-4.1

    gpt5 = next(m for m in models if m.name == "openai:gpt-5")
    assert gpt5.display_name == "GPT-5"
    assert gpt5.provider == "openai"
    assert "intelligence" in gpt5.description.lower()


@pytest.mark.asyncio
async def test_generate_calls_openai_api(openai_provider):
    """generate calls OpenAI API with correct parameters"""
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated summary"))]

    with patch.object(openai_provider.client.chat.completions, 'create', return_value=mock_response) as mock_create:
        result = await openai_provider.generate("openai:gpt-5", "query", "context")

        assert result == "Generated summary"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-5"  # Strip prefix
        assert len(call_kwargs["messages"]) >= 1
```

**Step 2: Run test to verify it fails**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_openai_provider.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `services/generator/app/providers/openai_provider.py`:

```python
"""OpenAI provider implementation."""
import os
from typing import List
from openai import AsyncOpenAI
from app.providers.base import ModelProvider
from app.models.schemas import Model


class OpenAIProvider(ModelProvider):
    """Provider for OpenAI models (GPT-5, GPT-4.1, etc)."""

    # Predefined OpenAI models (2025)
    MODELS = [
        {
            "name": "openai:gpt-5",
            "display_name": "GPT-5",
            "size": "N/A",
            "description": "Best intelligence, coding/math excellence, 94.6% AIME",
            "capabilities": ["reasoning", "coding", "creative", "multimodal"]
        },
        {
            "name": "openai:gpt-5-mini",
            "display_name": "GPT-5 Mini",
            "size": "N/A",
            "description": "Balanced performance and cost",
            "capabilities": ["reasoning", "coding", "fast"]
        },
        {
            "name": "openai:gpt-4.1",
            "display_name": "GPT-4.1",
            "size": "N/A",
            "description": "1M context, excellent long-form comprehension",
            "capabilities": ["reasoning", "long-context", "coding"]
        }
    ]

    def __init__(self):
        """Initialize OpenAI provider with API key from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured."""
        return self.client is not None

    async def list_models(self) -> List[Model]:
        """
        Return predefined OpenAI models.

        Returns:
            List of OpenAI Model objects
        """
        from datetime import datetime

        models = []
        for m in self.MODELS:
            model = Model(
                name=m["name"],
                display_name=m["display_name"],
                provider="openai",
                size=m["size"],
                description=m["description"],
                capabilities=m["capabilities"],
                modified_at=datetime.utcnow().isoformat() + "Z"
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using OpenAI API.

        Args:
            model: OpenAI model name (e.g., "openai:gpt-5")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary

        Raises:
            RuntimeError: If API call fails
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Strip "openai:" prefix for API call
        api_model = model.replace("openai:", "")

        # Construct messages
        system_message = "You are a helpful assistant that summarizes document search results."
        user_message = f"""Based on the following context, answer this query: {prompt}

Context:
{context}

Provide a concise, accurate summary."""

        try:
            response = await self.client.chat.completions.create(
                model=api_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {str(e)}")
```

**Step 4: Run test to verify it passes**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_openai_provider.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add services/generator/app/providers/openai_provider.py services/generator/tests/unit/providers/test_openai_provider.py
git commit -m "feat(generator): implement OpenAIProvider

- Support GPT-5, GPT-5 Mini, GPT-4.1
- Environment-based API key configuration
- Async API calls with error handling
- Comprehensive tests"
```

---

### Task 7: Implement Anthropic Provider

**Files:**
- Create: `services/generator/app/providers/anthropic_provider.py`
- Create: `tests/unit/providers/test_anthropic_provider.py`

**Step 1: Write the failing test**

Create `tests/unit/providers/test_anthropic_provider.py`:

```python
import pytest
from unittest.mock import Mock, patch
from app.providers.anthropic_provider import AnthropicProvider
from app.models.schemas import Model


@pytest.fixture
def anthropic_provider():
    """Create AnthropicProvider for testing."""
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        return AnthropicProvider()


def test_is_available_with_api_key():
    """is_available returns True when API key is set"""
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        provider = AnthropicProvider()
        assert provider.is_available() is True


def test_is_available_without_api_key():
    """is_available returns False when API key is missing"""
    with patch.dict('os.environ', {}, clear=True):
        provider = AnthropicProvider()
        assert provider.is_available() is False


@pytest.mark.asyncio
async def test_list_models_returns_claude_models(anthropic_provider):
    """list_models returns predefined Claude models"""
    models = await anthropic_provider.list_models()

    assert len(models) >= 3  # Opus, Sonnet, Haiku

    opus = next(m for m in models if m.name == "anthropic:claude-opus-4-1")
    assert opus.display_name == "Claude Opus 4.1"
    assert opus.provider == "anthropic"
    assert "powerful" in opus.description.lower()


@pytest.mark.asyncio
async def test_generate_calls_anthropic_api(anthropic_provider):
    """generate calls Anthropic API with correct parameters"""
    mock_response = Mock()
    mock_response.content = [Mock(text="Generated summary")]

    with patch.object(anthropic_provider.client.messages, 'create', return_value=mock_response) as mock_create:
        result = await anthropic_provider.generate("anthropic:claude-sonnet-4-5", "query", "context")

        assert result == "Generated summary"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "claude-sonnet-4-5"  # Strip prefix
```

**Step 2: Run test to verify it fails**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_anthropic_provider.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `services/generator/app/providers/anthropic_provider.py`:

```python
"""Anthropic Claude provider implementation."""
import os
from typing import List
from anthropic import AsyncAnthropic
from app.providers.base import ModelProvider
from app.models.schemas import Model


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic Claude models."""

    # Predefined Claude models (2025)
    MODELS = [
        {
            "name": "anthropic:claude-opus-4-1",
            "display_name": "Claude Opus 4.1",
            "size": "N/A",
            "description": "Most powerful Claude model, best reasoning",
            "capabilities": ["reasoning", "coding", "analysis", "multimodal"]
        },
        {
            "name": "anthropic:claude-sonnet-4-5",
            "display_name": "Claude Sonnet 4.5",
            "size": "N/A",
            "description": "Best coding model in the world",
            "capabilities": ["coding", "reasoning", "fast"]
        },
        {
            "name": "anthropic:claude-haiku-4-5",
            "display_name": "Claude Haiku 4.5",
            "size": "N/A",
            "description": "Fast and cost-effective",
            "capabilities": ["fast", "efficient", "reasoning"]
        }
    ]

    def __init__(self):
        """Initialize Anthropic provider with API key from environment."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = AsyncAnthropic(api_key=api_key) if api_key else None

    def is_available(self) -> bool:
        """Check if Anthropic API key is configured."""
        return self.client is not None

    async def list_models(self) -> List[Model]:
        """
        Return predefined Claude models.

        Returns:
            List of Claude Model objects
        """
        from datetime import datetime

        models = []
        for m in self.MODELS:
            model = Model(
                name=m["name"],
                display_name=m["display_name"],
                provider="anthropic",
                size=m["size"],
                description=m["description"],
                capabilities=m["capabilities"],
                modified_at=datetime.utcnow().isoformat() + "Z"
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using Anthropic API.

        Args:
            model: Claude model name (e.g., "anthropic:claude-sonnet-4-5")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary

        Raises:
            RuntimeError: If API call fails
        """
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        # Strip "anthropic:" prefix for API call
        api_model = model.replace("anthropic:", "")

        # Construct user message
        user_message = f"""Based on the following context, answer this query: {prompt}

Context:
{context}

Provide a concise, accurate summary."""

        try:
            response = await self.client.messages.create(
                model=api_model,
                max_tokens=500,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Anthropic generation failed: {str(e)}")
```

**Step 4: Run test to verify it passes**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_anthropic_provider.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add services/generator/app/providers/anthropic_provider.py services/generator/tests/unit/providers/test_anthropic_provider.py
git commit -m "feat(generator): implement AnthropicProvider

- Support Claude Opus 4.1, Sonnet 4.5, Haiku 4.5
- Environment-based API key configuration
- Async API calls with error handling
- Comprehensive tests"
```

---

### Task 8: Implement Google Provider

**Files:**
- Create: `services/generator/app/providers/google_provider.py`
- Create: `tests/unit/providers/test_google_provider.py`

**Step 1: Write the failing test**

Create `tests/unit/providers/test_google_provider.py`:

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.providers.google_provider import GoogleProvider
from app.models.schemas import Model


@pytest.fixture
def google_provider():
    """Create GoogleProvider for testing."""
    with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
        with patch('google.generativeai.configure'):
            return GoogleProvider()


def test_is_available_with_api_key():
    """is_available returns True when API key is set"""
    with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
        with patch('google.generativeai.configure'):
            provider = GoogleProvider()
            assert provider.is_available() is True


def test_is_available_without_api_key():
    """is_available returns False when API key is missing"""
    with patch.dict('os.environ', {}, clear=True):
        provider = GoogleProvider()
        assert provider.is_available() is False


@pytest.mark.asyncio
async def test_list_models_returns_gemini_models(google_provider):
    """list_models returns predefined Gemini models"""
    models = await google_provider.list_models()

    assert len(models) >= 2  # Pro, Flash

    pro = next(m for m in models if m.name == "google:gemini-2-5-pro")
    assert pro.display_name == "Gemini 2.5 Pro"
    assert pro.provider == "google"
    assert "2M context" in pro.description


@pytest.mark.asyncio
async def test_generate_calls_gemini_api(google_provider):
    """generate calls Google Gemini API with correct parameters"""
    mock_response = Mock()
    mock_response.text = "Generated summary"

    mock_model = Mock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    with patch('google.generativeai.GenerativeModel', return_value=mock_model):
        result = await google_provider.generate("google:gemini-2-5-flash", "query", "context")

        assert result == "Generated summary"
        mock_model.generate_content_async.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_google_provider.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `services/generator/app/providers/google_provider.py`:

```python
"""Google Gemini provider implementation."""
import os
from typing import List
import google.generativeai as genai
from app.providers.base import ModelProvider
from app.models.schemas import Model


class GoogleProvider(ModelProvider):
    """Provider for Google Gemini models."""

    # Predefined Gemini models (2025)
    MODELS = [
        {
            "name": "google:gemini-2-5-pro",
            "display_name": "Gemini 2.5 Pro",
            "size": "N/A",
            "description": "2M context, adaptive thinking capabilities",
            "capabilities": ["reasoning", "long-context", "multimodal"]
        },
        {
            "name": "google:gemini-2-5-flash",
            "display_name": "Gemini 2.5 Flash",
            "size": "N/A",
            "description": "Efficient, improved tool use, 54% SWE-Bench",
            "capabilities": ["fast", "tool-use", "reasoning"]
        }
    ]

    def __init__(self):
        """Initialize Google provider with API key from environment."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.api_key = api_key
        else:
            self.api_key = None

    def is_available(self) -> bool:
        """Check if Google API key is configured."""
        return self.api_key is not None

    async def list_models(self) -> List[Model]:
        """
        Return predefined Gemini models.

        Returns:
            List of Gemini Model objects
        """
        from datetime import datetime

        models = []
        for m in self.MODELS:
            model = Model(
                name=m["name"],
                display_name=m["display_name"],
                provider="google",
                size=m["size"],
                description=m["description"],
                capabilities=m["capabilities"],
                modified_at=datetime.utcnow().isoformat() + "Z"
            )
            models.append(model)

        return models

    async def generate(self, model: str, prompt: str, context: str) -> str:
        """
        Generate summary using Google Gemini API.

        Args:
            model: Gemini model name (e.g., "google:gemini-2-5-pro")
            prompt: User query
            context: Retrieved context

        Returns:
            Generated summary

        Raises:
            RuntimeError: If API call fails
        """
        if not self.api_key:
            raise RuntimeError("Google API key not configured")

        # Strip "google:" prefix and convert to API format
        # "google:gemini-2-5-pro" -> "gemini-2.5-pro"
        api_model = model.replace("google:", "").replace("-", ".", 1).replace("-", ".", 1)

        # Construct prompt
        full_prompt = f"""Based on the following context, answer this query: {prompt}

Context:
{context}

Provide a concise, accurate summary."""

        try:
            model_instance = genai.GenerativeModel(api_model)
            response = await model_instance.generate_content_async(
                full_prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 500
                }
            )

            return response.text

        except Exception as e:
            raise RuntimeError(f"Google Gemini generation failed: {str(e)}")
```

**Step 4: Run test to verify it passes**

```bash
cd services/generator
poetry run pytest tests/unit/providers/test_google_provider.py -v
```

Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add services/generator/app/providers/google_provider.py services/generator/tests/unit/providers/test_google_provider.py
git commit -m "feat(generator): implement GoogleProvider

- Support Gemini 2.5 Pro and Flash
- Environment-based API key configuration
- Async API calls with error handling
- Comprehensive tests"
```

---

### Task 9: Integrate Registry into Main Application

**Files:**
- Modify: `services/generator/app/main.py`
- Modify: `services/generator/app/api/routes/generation.py`
- Create: `services/generator/app/config.py`

**Step 1: Create configuration module**

Create `services/generator/app/config.py`:

```python
"""Application configuration."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Ollama Configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    enable_ollama: bool = os.getenv("ENABLE_OLLAMA", "true").lower() == "true"

    # OpenAI Configuration
    enable_openai: bool = os.getenv("ENABLE_OPENAI", "false").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Anthropic Configuration
    enable_anthropic: bool = os.getenv("ENABLE_ANTHROPIC", "false").lower() == "true"
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Google Configuration
    enable_google: bool = os.getenv("ENABLE_GOOGLE", "false").lower() == "true"
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 2: Update main.py to initialize registry**

In `services/generator/app/main.py`, add after imports:

```python
from app.config import settings
from app.providers.registry import ProviderRegistry
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider

# Global provider registry
provider_registry = ProviderRegistry()


@app.on_event("startup")
async def startup_event():
    """Initialize provider registry on startup."""
    logger.info("Initializing provider registry...")

    # Register Ollama if enabled
    if settings.enable_ollama:
        try:
            ollama = OllamaProvider(base_url=settings.ollama_base_url)
            provider_registry.register("ollama", ollama)
            logger.info("Registered Ollama provider")
        except Exception as e:
            logger.warning(f"Failed to register Ollama: {e}")

    # Register OpenAI if enabled
    if settings.enable_openai:
        try:
            openai = OpenAIProvider()
            provider_registry.register("openai", openai)
            logger.info("Registered OpenAI provider")
        except Exception as e:
            logger.warning(f"Failed to register OpenAI: {e}")

    # Register Anthropic if enabled
    if settings.enable_anthropic:
        try:
            anthropic = AnthropicProvider()
            provider_registry.register("anthropic", anthropic)
            logger.info("Registered Anthropic provider")
        except Exception as e:
            logger.warning(f"Failed to register Anthropic: {e}")

    # Register Google if enabled
    if settings.enable_google:
        try:
            google = GoogleProvider()
            provider_registry.register("google", google)
            logger.info("Registered Google provider")
        except Exception as e:
            logger.warning(f"Failed to register Google: {e}")

    active_providers = list(provider_registry.providers.keys())
    logger.info(f"Provider registry initialized with: {active_providers}")
```

**Step 3: Update routes to use registry**

In `services/generator/app/api/routes/generation.py`, update the `/models` endpoint:

```python
from app.main import provider_registry

@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """List all available models from all providers."""
    try:
        models = await provider_registry.list_all_models()
        return ModelsResponse(models=models)
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

Update the `/generate` endpoint:

```python
@router.post("/generate", response_model=GenerateResponse)
async def generate_summary(request: GenerateRequest):
    """Generate summary using specified model via provider registry."""
    try:
        # Use registry to route to appropriate provider
        summary, provider_used = await provider_registry.generate(
            model_name=request.model,
            prompt=request.prompt,
            context=request.context
        )

        return GenerateResponse(
            summary=summary,
            model_used=request.model
        )
    except ValueError as e:
        logger.error(f"Provider not found: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Test manually**

```bash
cd services/generator
# Set environment for testing
export ENABLE_OLLAMA=true
export ENABLE_OPENAI=false
export ENABLE_ANTHROPIC=false
export ENABLE_GOOGLE=false

# Run server
poetry run uvicorn app.main:app --reload --port 8002
```

In another terminal:
```bash
curl http://localhost:8002/models
```

Expected: JSON response with Ollama models enhanced with new schema

**Step 5: Commit**

```bash
git add services/generator/app/config.py services/generator/app/main.py services/generator/app/api/routes/generation.py
git commit -m "feat(generator): integrate provider registry into app

- Add environment-based configuration
- Initialize registry with enabled providers on startup
- Update /models and /generate endpoints to use registry
- Graceful fallback if providers fail to initialize"
```

---

## Phase 3: Frontend Integration

### Task 10: Update Frontend TypeScript Types

**Files:**
- Modify: `services/frontend/src/types/index.ts`

**Step 1: Update Model interface**

In `services/frontend/src/types/index.ts`, replace the existing `Model` interface:

```typescript
export interface Model {
  name: string;              // Unique identifier (e.g., "llama3.3:70b", "openai:gpt-5")
  display_name: string;      // Human-readable name (e.g., "Llama 3.3 70B")
  provider: string;          // "ollama", "openai", "anthropic", "google"
  size: string;              // "8B", "70B", "N/A"
  description: string;       // Capability description
  capabilities: string[];    // ["reasoning", "coding"]
  modified_at: string;       // ISO timestamp
}
```

**Step 2: Verify TypeScript compilation**

```bash
cd services/frontend
npx tsc --noEmit
```

Expected: No errors

**Step 3: Commit**

```bash
git add services/frontend/src/types/index.ts
git commit -m "feat(frontend): update Model type with provider fields

- Add display_name, provider, description, capabilities
- Matches backend schema exactly"
```

---

### Task 11: Add Radix Dropdown Menu Dependency

**Files:**
- Modify: `services/frontend/package.json`

**Step 1: Install dependency**

```bash
cd services/frontend
npm install @radix-ui/react-dropdown-menu
```

**Step 2: Verify installation**

```bash
npm list @radix-ui/react-dropdown-menu
```

Expected: Shows installed version

**Step 3: Commit**

```bash
git add services/frontend/package.json services/frontend/package-lock.json
git commit -m "feat(frontend): add Radix dropdown menu dependency

- Install @radix-ui/react-dropdown-menu for model selector"
```

---

### Task 12: Create Model Name Abbreviation Utility

**Files:**
- Create: `services/frontend/src/utils/modelUtils.ts`
- Create: `services/frontend/src/utils/__tests__/modelUtils.test.ts`

**Step 1: Write the failing test**

Create `services/frontend/src/utils/__tests__/modelUtils.test.ts`:

```typescript
import { abbreviateModelName, groupModelsByProvider } from '../modelUtils';
import { Model } from '../../types';

describe('abbreviateModelName', () => {
  it('abbreviates Llama models', () => {
    expect(abbreviateModelName('Llama 3.3 70B')).toBe('Llama 3.3');
  });

  it('keeps short names as-is', () => {
    expect(abbreviateModelName('GPT-5')).toBe('GPT-5');
    expect(abbreviateModelName('GPT-5 Mini')).toBe('GPT-5 Mini');
  });

  it('abbreviates Claude Sonnet models', () => {
    expect(abbreviateModelName('Claude Sonnet 4.5')).toBe('Sonnet 4.5');
  });

  it('abbreviates Gemini models', () => {
    expect(abbreviateModelName('Gemini 2.5 Pro')).toBe('Gemini 2.5');
  });
});

describe('groupModelsByProvider', () => {
  const models: Model[] = [
    {
      name: 'llama3.3:70b',
      display_name: 'Llama 3.3 70B',
      provider: 'ollama',
      size: '70B',
      description: 'Test',
      capabilities: [],
      modified_at: '2025-10-24T10:00:00Z'
    },
    {
      name: 'openai:gpt-5',
      display_name: 'GPT-5',
      provider: 'openai',
      size: 'N/A',
      description: 'Test',
      capabilities: [],
      modified_at: '2025-10-24T10:00:00Z'
    }
  ];

  it('groups models by provider', () => {
    const grouped = groupModelsByProvider(models);

    expect(grouped.ollama).toHaveLength(1);
    expect(grouped.openai).toHaveLength(1);
    expect(grouped.ollama[0].name).toBe('llama3.3:70b');
  });

  it('handles empty model list', () => {
    const grouped = groupModelsByProvider([]);
    expect(Object.keys(grouped)).toHaveLength(0);
  });
});
```

**Step 2: Run test to verify it fails**

```bash
cd services/frontend
npm test -- modelUtils.test.ts
```

Expected: FAIL with "Cannot find module"

**Step 3: Write minimal implementation**

Create `services/frontend/src/utils/modelUtils.ts`:

```typescript
import { Model } from '../types';

/**
 * Abbreviate model display name for compact UI.
 *
 * @param displayName - Full model display name
 * @returns Abbreviated name
 */
export function abbreviateModelName(displayName: string): string {
  // "Llama 3.3 70B" -> "Llama 3.3"
  // "GPT-5" -> "GPT-5" (keep short)
  // "Claude Sonnet 4.5" -> "Sonnet 4.5"
  // "Gemini 2.5 Pro" -> "Gemini 2.5"

  // Claude models: extract everything after "Claude "
  if (displayName.startsWith('Claude ')) {
    return displayName.replace('Claude ', '');
  }

  // Remove size suffix (e.g., " 70B", " 8B")
  const withoutSize = displayName.replace(/\s+\d+B$/i, '');

  // If name is short (<=10 chars), keep as-is
  if (withoutSize.length <= 10) {
    return withoutSize;
  }

  // For Gemini, remove "Pro"/"Flash" suffix
  if (displayName.startsWith('Gemini')) {
    return displayName.replace(/ (Pro|Flash)$/i, '');
  }

  return withoutSize;
}

/**
 * Group models by provider for dropdown menu.
 *
 * @param models - List of models
 * @returns Models grouped by provider
 */
export function groupModelsByProvider(models: Model[]): Record<string, Model[]> {
  const grouped: Record<string, Model[]> = {};

  models.forEach(model => {
    if (!grouped[model.provider]) {
      grouped[model.provider] = [];
    }
    grouped[model.provider].push(model);
  });

  return grouped;
}
```

**Step 4: Run test to verify it passes**

```bash
cd services/frontend
npm test -- modelUtils.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add services/frontend/src/utils/modelUtils.ts services/frontend/src/utils/__tests__/modelUtils.test.ts
git commit -m "feat(frontend): add model name abbreviation utilities

- abbreviateModelName for compact display
- groupModelsByProvider for dropdown organization
- Comprehensive tests"
```

---

### Task 13: Refactor EnhancedSearchBar with Model Dropdown

**Files:**
- Modify: `services/frontend/src/components/search/EnhancedSearchBar.tsx`

**Step 1: Update EnhancedSearchBar component**

Replace contents of `services/frontend/src/components/search/EnhancedSearchBar.tsx`:

```typescript
import React, { useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, ChevronDownIcon, CheckIcon } from '@radix-ui/react-icons';
import { Cpu } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { Model } from '../../types';
import { abbreviateModelName, groupModelsByProvider } from '../../utils/modelUtils';

interface EnhancedSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  selectedModel: string | null;
  onModelChange: (model: string) => void;
  models: Model[];
  modelsLoading: boolean;
  autoFocus?: boolean;
  placeholder?: string;
}

/**
 * Enhanced SearchBar component with integrated model selector.
 *
 * Features:
 * - Press "/" to focus from anywhere
 * - Press "Escape" to clear and blur
 * - Glassmorphism styling with backdrop-blur
 * - Integrated model dropdown on right side
 */
export const EnhancedSearchBar: React.FC<EnhancedSearchBarProps> = ({
  value,
  onChange,
  selectedModel,
  onModelChange,
  models,
  modelsLoading,
  autoFocus = false,
  placeholder = 'Search documents...'
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Focus search on "/" key
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }

      // Clear on Escape
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        onChange('');
        inputRef.current?.blur();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onChange]);

  // Get current model for display
  const currentModel = models.find(m => m.name === selectedModel);
  const displayName = currentModel
    ? abbreviateModelName(currentModel.display_name)
    : 'Select model';

  // Group models by provider
  const groupedModels = groupModelsByProvider(models);
  const providerOrder = ['ollama', 'openai', 'anthropic', 'google'];

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-6 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
          className="
            w-full pl-14 pr-48 py-4 text-lg
            bg-white/70 backdrop-blur-md
            border border-gray-200/50
            rounded-full shadow-lg
            focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400
          "
        />

        {/* Model Dropdown */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2">
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button
                className="
                  flex items-center gap-2 px-3 py-2
                  bg-white/70 backdrop-blur-md
                  border border-gray-200/50
                  rounded-full
                  hover:bg-white/90
                  transition-all duration-200
                  text-sm font-medium text-gray-700
                "
                disabled={modelsLoading}
              >
                <Cpu className="h-4 w-4" />
                <span>{modelsLoading ? 'Loading...' : displayName}</span>
                <ChevronDownIcon className="h-3 w-3" />
              </button>
            </DropdownMenu.Trigger>

            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="
                  min-w-[320px] max-h-[400px] overflow-y-auto
                  bg-white/90 backdrop-blur-md
                  border border-gray-200/50
                  rounded-lg shadow-lg
                  p-2
                "
                sideOffset={8}
                align="end"
              >
                {providerOrder.map((provider, idx) => {
                  const providerModels = groupedModels[provider];
                  if (!providerModels || providerModels.length === 0) return null;

                  return (
                    <React.Fragment key={provider}>
                      {idx > 0 && <DropdownMenu.Separator className="h-px bg-gray-200 my-2" />}

                      <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">
                        {provider}
                      </div>

                      {providerModels.map((model) => (
                        <DropdownMenu.Item
                          key={model.name}
                          className="
                            px-3 py-2.5 rounded-md
                            hover:bg-gray-100/80
                            cursor-pointer
                            outline-none
                            transition-colors
                          "
                          onSelect={() => onModelChange(model.name)}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-gray-900">
                                  {model.display_name}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {model.size}
                                </span>
                              </div>
                              <p className="text-xs text-gray-600 mt-0.5">
                                {model.description}
                              </p>
                            </div>
                            {selectedModel === model.name && (
                              <CheckIcon className="h-4 w-4 text-primary-600 flex-shrink-0 mt-1" />
                            )}
                          </div>
                        </DropdownMenu.Item>
                      ))}
                    </React.Fragment>
                  );
                })}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
      </div>
    </div>
  );
};
```

**Step 2: Verify TypeScript compilation**

```bash
cd services/frontend
npx tsc --noEmit
```

Expected: No errors

**Step 3: Commit**

```bash
git add services/frontend/src/components/search/EnhancedSearchBar.tsx
git commit -m "feat(frontend): integrate model selector into search bar

- Add Radix dropdown menu on right side
- Replace keyboard hint with model selector
- Group models by provider with separators
- Show model description and selection state
- Glassmorphism styling consistent with search bar"
```

---

### Task 14: Update MainPage to Use New SearchBar Props

**Files:**
- Modify: `services/frontend/src/pages/MainPage.tsx`
- Modify: `services/frontend/src/hooks/useModels.ts` (create if doesn't exist)

**Step 1: Create useModels hook**

Create `services/frontend/src/hooks/useModels.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { Model } from '../types';

/**
 * Hook to fetch and cache available models.
 */
export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const response = await api.listModels();
      return response.models;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1
  });
}
```

**Step 2: Update MainPage to pass model props**

In `services/frontend/src/pages/MainPage.tsx`, update imports and component:

```typescript
import { useModels } from '../hooks/useModels';

// Inside MainPage component, after existing state declarations:
const models = useModels();

// Update EnhancedSearchBar usage (around line 74):
<EnhancedSearchBar
  value={searchQuery}
  onChange={setSearchQuery}
  selectedModel={selectedModel}
  onModelChange={setSelectedModel}
  models={models.data || []}
  modelsLoading={models.isLoading}
  autoFocus
/>
```

Remove the old ModelSelector component (lines 68-73):

```typescript
// DELETE these lines:
<div className="flex justify-center">
  <ModelSelector
    selectedModel={selectedModel}
    onModelChange={setSelectedModel}
  />
</div>
```

**Step 3: Verify TypeScript compilation**

```bash
cd services/frontend
npx tsc --noEmit
```

Expected: No errors

**Step 4: Commit**

```bash
git add services/frontend/src/hooks/useModels.ts services/frontend/src/pages/MainPage.tsx
git commit -m "feat(frontend): update MainPage for integrated model selector

- Create useModels hook with React Query caching
- Pass model data to EnhancedSearchBar
- Remove old standalone ModelSelector component"
```

---

### Task 15: Remove Old ModelSelector Component

**Files:**
- Delete: `services/frontend/src/components/search/ModelSelector.tsx`

**Step 1: Delete old component**

```bash
cd services/frontend
git rm src/components/search/ModelSelector.tsx
```

**Step 2: Verify no imports remain**

```bash
grep -r "ModelSelector" src/
```

Expected: No matches (or only in git history)

**Step 3: Commit**

```bash
git commit -m "refactor(frontend): remove old ModelSelector component

- Replaced by integrated dropdown in EnhancedSearchBar
- Clean up obsolete code"
```

---

## Phase 4: Testing & Documentation

### Task 16: Add Integration Test for Multi-Provider Flow

**Files:**
- Create: `tests/integration/test_multi_provider.sh`

**Step 1: Create integration test script**

Create `tests/integration/test_multi_provider.sh`:

```bash
#!/bin/bash

set -e

echo "=== Multi-Provider Integration Test ==="

# Start services
echo "Starting services..."
cd infrastructure/docker-compose
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services..."
sleep 10

# Test 1: List models (Ollama only)
echo "Test 1: List models with Ollama only"
MODELS=$(curl -s http://localhost:8002/models)
echo "$MODELS" | jq -e '.models | length > 0' || { echo "FAIL: No models returned"; exit 1; }
echo "✓ Models endpoint working"

# Test 2: Verify enhanced schema
echo "Test 2: Verify enhanced model schema"
echo "$MODELS" | jq -e '.models[0] | has("display_name")' || { echo "FAIL: Missing display_name"; exit 1; }
echo "$MODELS" | jq -e '.models[0] | has("provider")' || { echo "FAIL: Missing provider"; exit 1; }
echo "$MODELS" | jq -e '.models[0] | has("description")' || { echo "FAIL: Missing description"; exit 1; }
echo "✓ Enhanced schema present"

# Test 3: Generate summary
echo "Test 3: Generate summary with default model"
MODEL_NAME=$(echo "$MODELS" | jq -r '.models[0].name')
RESPONSE=$(curl -s -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"$MODEL_NAME\", \"prompt\": \"test query\", \"context\": \"test context\"}")
echo "$RESPONSE" | jq -e '.summary' || { echo "FAIL: No summary generated"; exit 1; }
echo "✓ Generation working"

# Test 4: Frontend models endpoint
echo "Test 4: Frontend can fetch models via API"
API_MODELS=$(curl -s http://localhost:8000/api/v1/models)
echo "$API_MODELS" | jq -e '.models | length > 0' || { echo "FAIL: API models endpoint broken"; exit 1; }
echo "✓ API passthrough working"

# Cleanup
echo "Cleaning up..."
docker-compose down

echo "=== All tests passed ==="
```

**Step 2: Make executable and run**

```bash
chmod +x tests/integration/test_multi_provider.sh
./tests/integration/test_multi_provider.sh
```

Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/integration/test_multi_provider.sh
git commit -m "test: add multi-provider integration tests

- Test model listing with enhanced schema
- Test generation routing
- Test API passthrough
- Verify all services communicate correctly"
```

---

### Task 17: Update Documentation

**Files:**
- Modify: `README.md`
- Create: `docs/MULTI_PROVIDER_SETUP.md`

**Step 1: Create setup guide**

Create `docs/MULTI_PROVIDER_SETUP.md`:

```markdown
# Multi-Provider Setup Guide

## Overview

The generator service supports multiple LLM providers:
- **Ollama** (local models, default enabled)
- **OpenAI** (GPT-5, GPT-4.1, requires API key)
- **Anthropic** (Claude models, requires API key)
- **Google** (Gemini models, requires API key)

## Configuration

### Environment Variables

Set these in your `.env` file or docker-compose:

\`\`\`bash
# Ollama (enabled by default)
ENABLE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI (optional)
ENABLE_OPENAI=true
OPENAI_API_KEY=sk-...

# Anthropic (optional)
ENABLE_ANTHROPIC=true
ANTHROPIC_API_KEY=sk-ant-...

# Google (optional)
ENABLE_GOOGLE=true
GOOGLE_API_KEY=AIza...
\`\`\`

### Docker Compose

Update `infrastructure/docker-compose/docker-compose.yml`:

\`\`\`yaml
generator:
  environment:
    - ENABLE_OLLAMA=true
    - ENABLE_OPENAI=${ENABLE_OPENAI:-false}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - ENABLE_ANTHROPIC=${ENABLE_ANTHROPIC:-false}
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    - ENABLE_GOOGLE=${ENABLE_GOOGLE:-false}
    - GOOGLE_API_KEY=${GOOGLE_API_KEY}
\`\`\`

## Testing

### Test Individual Providers

\`\`\`bash
# List all available models
curl http://localhost:8002/models | jq

# Generate with specific model
curl -X POST http://localhost:8002/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "openai:gpt-5",
    "prompt": "Summarize this",
    "context": "Context text here"
  }' | jq
\`\`\`

## Frontend Integration

The model dropdown in the search bar automatically displays all available models grouped by provider. No frontend configuration needed.

## Troubleshooting

### Provider Not Showing Up

1. Check environment variable is set: `echo $OPENAI_API_KEY`
2. Check logs: `docker-compose logs generator`
3. Verify API key is valid

### Generation Failing

1. Check provider is registered: Look for "Registered X provider" in logs
2. Test API key directly with provider's CLI
3. Check rate limits on provider account
\`\`\`

**Step 2: Update main README**

In `README.md`, add section after "Development Commands":

\`\`\`markdown
## Multi-Provider Model Support

The system supports multiple LLM providers for summary generation:

- **Ollama** (local, default)
- **OpenAI** (GPT-5, GPT-4.1)
- **Anthropic** (Claude models)
- **Google** (Gemini models)

See [Multi-Provider Setup Guide](docs/MULTI_PROVIDER_SETUP.md) for configuration details.

To enable additional providers, set environment variables:

\`\`\`bash
export ENABLE_OPENAI=true
export OPENAI_API_KEY=sk-...
\`\`\`

Models from all enabled providers appear automatically in the frontend dropdown.
\`\`\`

**Step 3: Commit**

```bash
git add docs/MULTI_PROVIDER_SETUP.md README.md
git commit -m "docs: add multi-provider setup guide

- Document environment variables for each provider
- Add troubleshooting section
- Update main README with provider info"
```

---

### Task 18: Final Verification and Cleanup

**Step 1: Run all tests**

```bash
# Backend tests
cd services/generator
poetry run pytest -v

# Frontend type check
cd ../frontend
npx tsc --noEmit

# Integration test
cd ../..
./tests/integration/test_multi_provider.sh
```

Expected: All pass

**Step 2: Build and test Docker containers**

```bash
cd infrastructure/docker-compose
docker-compose build
docker-compose up -d
docker-compose logs -f
```

Check logs for:
- "Registered ollama provider"
- "Provider registry initialized"
- No errors

**Step 3: Manual frontend test**

1. Open http://localhost:3000
2. Click model dropdown in search bar
3. Verify models are grouped by provider
4. Select a model
5. Perform a search
6. Verify summary generated with correct model

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete multi-provider model selector implementation

- Provider abstraction layer with registry
- OpenAI, Anthropic, Google provider implementations
- Integrated model dropdown in search bar
- Environment-based configuration
- Comprehensive tests and documentation

Implements design from docs/plans/2025-10-24-multi-provider-model-selector-design.md"
```

---

## Summary

**Total Tasks**: 18
**Estimated Time**: 4-6 hours with testing
**Key Deliverables**:
- ✅ Provider abstraction layer (base, registry)
- ✅ Ollama, OpenAI, Anthropic, Google providers
- ✅ Enhanced Model schema
- ✅ Integrated frontend dropdown
- ✅ Environment-based configuration
- ✅ Comprehensive tests
- ✅ Documentation

**Next Steps**:
1. Test with real API keys for OpenAI/Anthropic/Google
2. Monitor performance and rate limits
3. Consider adding cost tracking
4. Consider adding model health monitoring
