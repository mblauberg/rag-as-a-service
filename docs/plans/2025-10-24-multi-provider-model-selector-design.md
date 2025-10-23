# Multi-Provider Model Selector Design

**Date**: 2025-10-24
**Status**: Design Approved
**Scope**: Enhanced model dropdown with multi-provider support (Ollama, OpenAI, Anthropic, Google)

## Overview

This design integrates the model selector directly into the search bar with a modern dropdown interface and establishes a multi-provider architecture to support LLM APIs from Ollama, OpenAI, Anthropic, and Google.

## Goals

1. **UX Enhancement**: Replace the separate model selector with an integrated dropdown in the search bar
2. **Future-Proof Architecture**: Support multiple model providers (current: Ollama, future: OpenAI/Anthropic/Google)
3. **Design Consistency**: Match the existing glassmorphism aesthetic with modern UI components
4. **Extensibility**: Enable easy addition of new providers without major refactoring

## Architecture

### Three-Layer Approach

#### 1. Backend: Provider Abstraction Layer

**Location**: `services/generator/app/providers/`

**Base Interface**:
```python
class ModelProvider(ABC):
    @abstractmethod
    async def list_models(self) -> list[Model]:
        """Return available models from this provider"""

    @abstractmethod
    async def generate(self, model: str, prompt: str, context: str) -> str:
        """Generate summary using provider's API"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and accessible"""
```

**Concrete Implementations**:
- **OllamaProvider** (`providers/ollama_provider.py`): Uses existing Ollama HTTP API (localhost:11434)
- **OpenAIProvider** (`providers/openai_provider.py`): Uses OpenAI SDK, requires `OPENAI_API_KEY` env var
- **AnthropicProvider** (`providers/anthropic_provider.py`): Uses Anthropic SDK, requires `ANTHROPIC_API_KEY`
- **GoogleProvider** (`providers/google_provider.py`): Uses Google Generative AI SDK, requires `GOOGLE_API_KEY`

Each provider handles authentication, error handling, and response parsing internally.

#### 2. Backend: Provider Registry

**Location**: `services/generator/app/registry.py`

```python
class ProviderRegistry:
    def __init__(self):
        self.providers: dict[str, ModelProvider] = {}

    def register(self, name: str, provider: ModelProvider):
        """Register a provider if it's available"""
        if provider.is_available():
            self.providers[name] = provider

    async def list_all_models(self) -> list[Model]:
        """Aggregate models from all registered providers"""
        models = []
        for provider_name, provider in self.providers.items():
            models.extend(await provider.list_models())
        return models

    async def generate(self, model_name: str, prompt: str, context: str) -> tuple[str, str]:
        """Route generation to appropriate provider, return (summary, provider_name)"""
        provider_name = self._extract_provider(model_name)
        if provider_name not in self.providers:
            raise ValueError(f"Provider not found: {provider_name}")
        return await self.providers[provider_name].generate(model_name, prompt, context)
```

**Configuration via Environment Variables**:
- `ENABLE_OLLAMA=true` (default true)
- `ENABLE_OPENAI=false` (requires `OPENAI_API_KEY`)
- `ENABLE_ANTHROPIC=false` (requires `ANTHROPIC_API_KEY`)
- `ENABLE_GOOGLE=false` (requires `GOOGLE_API_KEY`)

At startup, the generator service attempts to register all enabled providers. Providers without required API keys gracefully skip registration.

#### 3. Frontend: Integrated Search Bar Component

**Component**: `EnhancedSearchBar` (modified)
**Location**: `services/frontend/src/components/search/EnhancedSearchBar.tsx`

**New Props**:
```typescript
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
```

**Visual Design**:
- Dropdown positioned on right side of search bar, replacing `<kbd>/</kbd>` keyboard hint
- Button shows: Cpu icon (lucide-react) + abbreviated model name + ChevronDown icon
- Button styling: `bg-white/70 backdrop-blur-md border border-gray-200/50 rounded-full`
- Dropdown menu uses `@radix-ui/react-dropdown-menu` with glassmorphism styling

## Data Schema

### Backend Model Schema

```python
class Model(BaseModel):
    name: str              # Unique identifier (e.g., "llama3.3:70b", "openai:gpt-5")
    display_name: str      # Human-readable name (e.g., "Llama 3.3 70B", "GPT-5")
    provider: str          # "ollama", "openai", "anthropic", "google"
    size: str              # "8B", "70B", "N/A" (for API models)
    description: str       # Capability description
    capabilities: list[str] = []  # ["reasoning", "coding", "creative"]
    modified_at: str       # ISO timestamp
```

### Frontend TypeScript Types

**Updated** `services/frontend/src/types/index.ts`:
```typescript
export interface Model {
  name: string;
  display_name: string;
  provider: string;
  size: string;
  description: string;
  capabilities: string[];
  modified_at: string;
}
```

### Model Naming Convention

Use qualified names with provider prefixes for uniqueness:
- **Ollama**: Keep existing format (`"llama3.3:70b"`, `"qwen3:14b"`)
- **OpenAI**: `"openai:gpt-5"`, `"openai:gpt-5-mini"`, `"openai:gpt-4.1"`
- **Anthropic**: `"anthropic:claude-opus-4-1"`, `"anthropic:claude-sonnet-4-5"`
- **Google**: `"google:gemini-2-5-pro"`, `"google:gemini-2-5-flash"`

This ensures no naming collisions and makes provider routing trivial (split on `:` or `-` to determine provider).

## Example Model Configurations (2025)

### Ollama Models
- `llama3.3:70b` → "Llama 3.3 70B" - State-of-the-art, best overall performance
- `llama3.1:8b` → "Llama 3.1 8B" - Fast, 128K context, good for summaries
- `qwen3:14b` → "Qwen3 14B" - Multilingual, strong reasoning

### OpenAI Models (requires API key)
- `openai:gpt-5` → "GPT-5" - Best intelligence, coding/math excellence, 94.6% AIME
- `openai:gpt-5-mini` → "GPT-5 Mini" - Balanced performance/cost
- `openai:gpt-4.1` → "GPT-4.1" - 1M context, excellent long-form comprehension

### Anthropic Models (requires API key)
- `anthropic:claude-opus-4-1` → "Claude Opus 4.1" - Most powerful, best reasoning (released Aug 2025)
- `anthropic:claude-sonnet-4-5` → "Claude Sonnet 4.5" - Best coding model (released Sep 2025)
- `anthropic:claude-haiku-4-5` → "Claude Haiku 4.5" - Fast, cost-effective (released Oct 2025)

### Google Models (requires API key)
- `google:gemini-2-5-pro` → "Gemini 2.5 Pro" - 2M context, adaptive thinking
- `google:gemini-2-5-flash` → "Gemini 2.5 Flash" - Efficient, improved tool use, 54% SWE-Bench

**Model descriptions** are provider-specific:
- **Ollama**: Generated from local model metadata
- **API Providers**: Hardcoded based on provider documentation

## Frontend UI Design

### Dropdown Button (in search bar)

**Position**: Right side of search bar, replacing keyboard hint
**Components**:
- Cpu icon (lucide-react, 16px)
- Abbreviated model name (e.g., "Llama 3.3", "GPT-5", "Sonnet 4.5")
- ChevronDown icon (12px)

**Abbreviation Logic**:
```typescript
function abbreviateModelName(displayName: string): string {
  // "Llama 3.3 70B" → "Llama 3.3"
  // "GPT-5 Mini" → "GPT-5 Mini" (keep short names)
  // "Claude Sonnet 4.5" → "Sonnet 4.5"
  // "Gemini 2.5 Pro" → "Gemini 2.5"
}
```

### Dropdown Menu

**Library**: `@radix-ui/react-dropdown-menu` (add to dependencies)
**Styling**: Glassmorphism matching search bar

**Menu Structure**:
- Items grouped by provider
- `<DropdownMenuSeparator>` between provider groups
- Each item displays:
  - Provider badge pill (e.g., "Ollama", "OpenAI")
  - Model display_name (bold)
  - Size (secondary text)
  - Description (subtitle, muted text)
- Selected model shows checkmark icon
- Hover state with subtle background

**Example Menu Item**:
```
[Ollama] Llama 3.3 70B                                    ✓
         State-of-the-art, best overall performance

[OpenAI] GPT-5
         Best intelligence, coding/math excellence
```

## Data Flow

### Search with Model Selection

1. User selects model from dropdown (e.g., "GPT-5")
2. Frontend sends search request: `POST /api/v1/search` with `model: "openai:gpt-5"`
3. API service forwards request to generator: `POST /generate` with model field
4. Generator registry extracts provider from model name (`openai`)
5. Registry routes to OpenAIProvider
6. OpenAIProvider calls OpenAI API, generates summary
7. Response includes `summary` and `model_used: "openai:gpt-5"`
8. Frontend displays search results + summary with model attribution

### Model List Fetching

1. Frontend fetches models on mount: `GET /api/v1/models`
2. Generator service returns `await provider_registry.list_all_models()`
3. Models aggregated from all active providers
4. Frontend caches with React Query (5min stale time)
5. Dropdown populated with grouped models

## Error Handling

### Provider Availability
- If provider fails to initialize (missing API key, network error), it's skipped during registration
- Frontend handles empty model lists with fallback: "No models available"
- If all providers fail, show error: "Unable to load models. Check configuration."

### Model Selection Persistence
- Selected model stored in `localStorage` with key `selectedModel`
- On page load, validate stored model exists in current list
- If unavailable (provider disabled, model removed), fall back to first available
- Clear invalid selections automatically

### API Key Security
- API keys stored only in backend environment variables, never exposed to frontend
- Provider classes handle authentication internally
- Failed authentication logged server-side, generic error returned to client

### Rate Limiting & Costs
- Each provider tracks its own rate limits internally
- If rate limit hit, return error: `{"error": "Rate limit exceeded for {provider}"}`
- Frontend shows: "Model temporarily unavailable. Try another model."
- No automatic retry to avoid cost overruns

### Generation Failures
- If generation fails (timeout, API error), return `summary: null, model_used: null`
- Frontend displays search results without summary, shows error toast
- Search results still shown (generation failure doesn't block search)

### Provider Routing
- Model name validated against available models before routing
- Invalid model returns 400: "Model not found: {model_name}"
- Provider prefix extracted via split, falls back to Ollama if no prefix

## Testing Strategy

### Backend Tests (Generator Service)

**Unit Tests** (`tests/unit/providers/`):
- Mock provider APIs to test error handling
- Test model list aggregation from multiple providers
- Test provider routing based on model name prefix
- Test graceful degradation when providers unavailable

**Integration Tests** (`tests/integration/`):
- Test `/models` endpoint returns correct schema
- Test generation endpoint with different providers
- Test provider registry initialization with various env var combinations

### Frontend Tests

**Component Tests** (`src/components/search/__tests__/`):
- Test model dropdown renders correctly with models
- Test model selection updates state and localStorage
- Test keyboard shortcuts still work with integrated dropdown
- Test loading and error states

**Integration Tests** (`src/__tests__/`):
- Test model list fetched on mount
- Test search with selected model sends correct API request
- Test model persistence across page reloads

### Manual Testing Checklist
- [ ] Verify glassmorphism styling matches existing search bar
- [ ] Test dropdown on mobile/tablet screen sizes
- [ ] Verify model names abbreviated correctly
- [ ] Test with only Ollama (no API keys)
- [ ] Test with multiple providers enabled
- [ ] Test provider grouping in dropdown
- [ ] Test with >20 models (virtualization)

### Performance Considerations
- Model list cached in frontend (React Query, 5min stale time)
- Provider initialization happens once at startup, not per request
- Dropdown uses virtualization if >20 models (react-window)

## Implementation Order

### Phase 1: Backend Foundation
1. Create provider abstract base class
2. Implement OllamaProvider (refactor existing code)
3. Create ProviderRegistry
4. Update generator service startup to initialize registry
5. Enhance Model schema with new fields
6. Update `/models` endpoint to aggregate from registry

### Phase 2: API Provider Implementations
7. Implement OpenAIProvider with SDK
8. Implement AnthropicProvider with SDK
9. Implement GoogleProvider with SDK
10. Add environment variable configuration
11. Write provider unit tests

### Phase 3: Frontend Integration
12. Add `@radix-ui/react-dropdown-menu` dependency
13. Update TypeScript types in `types/index.ts`
14. Refactor EnhancedSearchBar with model dropdown
15. Implement model name abbreviation logic
16. Style dropdown menu with glassmorphism
17. Update MainPage to pass models to EnhancedSearchBar
18. Remove old ModelSelector component

### Phase 4: Testing & Polish
19. Write frontend component tests
20. Write integration tests for full flow
21. Manual testing on various screen sizes
22. Documentation updates (README, API docs)
23. Update Docker Compose with example env vars

## Dependencies

### Backend (Generator Service)
- `openai` (OpenAI Python SDK)
- `anthropic` (Anthropic Python SDK)
- `google-generativeai` (Google Generative AI SDK)

### Frontend
- `@radix-ui/react-dropdown-menu` (dropdown component)
- `lucide-react` (already installed, for icons)

## Configuration Example

### docker-compose.yml
```yaml
generator:
  environment:
    # Ollama (default enabled)
    - OLLAMA_BASE_URL=http://host.docker.internal:11434
    - ENABLE_OLLAMA=true

    # OpenAI (optional)
    - ENABLE_OPENAI=false
    - OPENAI_API_KEY=${OPENAI_API_KEY}

    # Anthropic (optional)
    - ENABLE_ANTHROPIC=false
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

    # Google (optional)
    - ENABLE_GOOGLE=false
    - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

### .env.example
```
# OpenAI Configuration (optional)
OPENAI_API_KEY=sk-...

# Anthropic Configuration (optional)
ANTHROPIC_API_KEY=sk-ant-...

# Google Configuration (optional)
GOOGLE_API_KEY=AIza...
```

## Migration Path

### Backward Compatibility
- Existing Ollama-only deployments continue to work without changes
- If `model` field missing in search request, use default (first available model)
- Old model names (without provider prefix) supported for Ollama models

### Gradual Rollout
1. Deploy backend with multi-provider support, Ollama only (no breaking changes)
2. Deploy frontend with integrated dropdown (improved UX, same functionality)
3. Enable API providers as needed via environment variables

## Success Metrics

- Model dropdown integrated seamlessly into search bar UI
- Multiple providers can be enabled via configuration
- Adding a new provider requires <2 hours of development
- Frontend remains responsive with 50+ models in dropdown
- No performance regression in search or generation latency

## Future Enhancements

- **Model Health Monitoring**: Track provider availability and latency
- **Model Recommendations**: Suggest best model based on query type
- **Cost Tracking**: Display estimated costs for API models
- **Custom Models**: Allow users to add custom fine-tuned models
- **A/B Testing**: Compare results from different models side-by-side
