# Model Alias Support Design

**Date:** 2025-10-31
**Status:** Approved
**Author:** Claude Code

## Overview

Add support for user-friendly model aliases that map to provider-specific API model names. This allows users to specify models like `gpt-5`, `sonnet-4.5`, or `gemini-flash-2.5` without needing provider prefixes, while maintaining backward compatibility with the existing `provider:model` format.

## Goals

1. Support standalone model aliases (e.g., `gpt-5`, `sonnet-4.5`, `haiku-4.5`)
2. Map aliases to actual API model names (e.g., `sonnet-4.5` → `claude-sonnet-4-5-20250929`)
3. Make all three providers optional (remove OpenAI as required default)
4. Maintain backward compatibility with `provider:model` format
5. Provide clear error messages when providers are unavailable

## Model Mappings

| User-friendly Alias | Provider | Actual API Model Name |
|---------------------|----------|----------------------|
| gpt-5 | OpenAI | gpt-5 |
| gpt-5-mini | OpenAI | gpt-5-mini |
| sonnet-4.5 | Anthropic | claude-sonnet-4-5-20250929 |
| opus-4.1 | Anthropic | claude-opus-4-1-20250805 |
| haiku-4.5 | Anthropic | claude-haiku-4-5-20251001 |
| gemini-flash-2.5 | Google | gemini-2.5-flash |
| gemini-pro-2.5 | Google | gemini-2.5-pro |

## Architecture

### Central Registry Approach

Use a **central model alias mapping** in `ProviderRegistry` that translates user-friendly names to provider-specific API model names.

**Key Components:**

1. **Model Alias Registry** (services/generator/app/providers/registry.py)
   - `MODEL_ALIASES` dictionary: friendly name → (provider, API model name)
   - Single source of truth for all model mappings
   - Easy to extend with new models

2. **Provider Updates** (all provider files)
   - Update MODELS list with actual API model names
   - Provider `generate()` methods receive correct API names

3. **Backward Compatibility**
   - Existing `provider:model` format continues to work
   - New standalone names checked against alias registry first
   - Falls back to existing provider extraction logic

## Implementation Details

### 1. Registry Changes (registry.py)

#### Add MODEL_ALIASES Dictionary

```python
class ProviderRegistry:
    """Registry for managing and routing between model providers."""

    # Model alias mappings: friendly_name -> (provider, api_model_name)
    MODEL_ALIASES = {
        # OpenAI models
        "gpt-5": ("openai", "gpt-5"),
        "gpt-5-mini": ("openai", "gpt-5-mini"),

        # Anthropic models
        "sonnet-4.5": ("anthropic", "claude-sonnet-4-5-20250929"),
        "opus-4.1": ("anthropic", "claude-opus-4-1-20250805"),
        "haiku-4.5": ("anthropic", "claude-haiku-4-5-20251001"),

        # Google models
        "gemini-flash-2.5": ("google", "gemini-2.5-flash"),
        "gemini-pro-2.5": ("google", "gemini-2.5-pro"),
    }
```

#### Update _extract_provider() Method

```python
def _extract_provider(self, model_name: str) -> str:
    """
    Extract provider name from model identifier.

    Args:
        model_name: Model name (alias, provider:model, or direct name)

    Returns:
        Provider name

    Raises:
        ValueError: If provider cannot be determined
    """
    # First, check if it's a standalone alias
    if model_name in self.MODEL_ALIASES:
        return self.MODEL_ALIASES[model_name][0]

    # Then check provider:model format
    if ":" in model_name:
        parts = model_name.split(":")
        if parts[0] in self.providers:
            return parts[0]
        if parts[0] in ["openai", "anthropic", "google"]:
            return parts[0]

    # No default - raise error with helpful message
    raise ValueError(
        f"Cannot determine provider for model '{model_name}'. "
        f"Use format 'provider:model' or one of the supported aliases: "
        f"{list(self.MODEL_ALIASES.keys())}"
    )
```

#### Add _resolve_model_name() Method

```python
def _resolve_model_name(self, model_name: str) -> str:
    """
    Resolve user-provided model name to actual API model name.

    Args:
        model_name: User's model identifier

    Returns:
        Actual API model name
    """
    # Check if it's an alias
    if model_name in self.MODEL_ALIASES:
        return self.MODEL_ALIASES[model_name][1]

    # Check if provider:model format
    if ":" in model_name:
        return model_name.split(":", 1)[1]

    # Return as-is (for backward compatibility)
    return model_name
```

#### Update generate() Method

```python
async def generate(self, model_name: str, prompt: str, context: str) -> Tuple[str, str]:
    """
    Route generation request to appropriate provider.

    Args:
        model_name: Model identifier (alias or provider:model)
        prompt: User query
        context: Retrieved context

    Returns:
        Tuple of (generated_summary, provider_name)

    Raises:
        ValueError: If provider not found or not available
    """
    provider_name = self._extract_provider(model_name)

    if provider_name not in self.providers:
        available = list(self.providers.keys())
        raise ValueError(
            f"Provider '{provider_name}' not available (no API key configured). "
            f"Available providers: {available if available else 'none'}"
        )

    # Resolve to actual API model name
    api_model_name = self._resolve_model_name(model_name)
    full_model = f"{provider_name}:{api_model_name}"

    summary = await self.providers[provider_name].generate(full_model, prompt, context)
    return summary, provider_name
```

### 2. Provider Updates

#### OpenAI Provider (openai_provider.py)

Models already use correct API names - no changes needed to MODELS list.

#### Anthropic Provider (anthropic_provider.py)

Update MODELS list with actual API model names:

```python
MODELS = [
    {
        "name": "anthropic:claude-opus-4-1-20250805",
        "display_name": "Claude Opus 4.1",
        "size": "N/A",
        "description": "Most powerful Claude model, best reasoning",
        "capabilities": ["reasoning", "coding", "analysis", "multimodal"]
    },
    {
        "name": "anthropic:claude-sonnet-4-5-20250929",
        "display_name": "Claude Sonnet 4.5",
        "size": "N/A",
        "description": "Best coding model in the world",
        "capabilities": ["coding", "reasoning", "fast"]
    },
    {
        "name": "anthropic:claude-haiku-4-5-20251001",
        "display_name": "Claude Haiku 4.5",
        "size": "N/A",
        "description": "Fast and cost-effective",
        "capabilities": ["fast", "efficient", "reasoning"]
    }
]
```

#### Google Provider (google_provider.py)

Update MODELS list with actual API model names:

```python
MODELS = [
    {
        "name": "google:gemini-2.5-pro",
        "display_name": "Gemini 2.5 Pro",
        "size": "N/A",
        "description": "2M context, adaptive thinking capabilities",
        "capabilities": ["reasoning", "long-context", "multimodal"]
    },
    {
        "name": "google:gemini-2.5-flash",
        "display_name": "Gemini 2.5 Flash",
        "size": "N/A",
        "description": "Efficient, improved tool use, 54% SWE-Bench",
        "capabilities": ["fast", "tool-use", "reasoning"]
    }
]
```

### 3. Startup Validation

Add validation to ensure at least one provider is available when the service starts:

```python
# In main.py or service initialization
def validate_providers(registry: ProviderRegistry) -> None:
    """Ensure at least one provider is available."""
    if not registry.providers:
        raise RuntimeError(
            "No LLM providers available. Please configure at least one API key: "
            "OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
        )
```

## Testing Strategy

### Unit Tests

**Test Model Alias Resolution:**
- ✓ Standalone aliases map correctly: `"gpt-5"` → `("openai", "gpt-5")`
- ✓ All aliases resolve to correct API names
- ✓ Unknown model raises ValueError with helpful message

**Test Provider Selection:**
- ✓ Alias selects correct provider: `"sonnet-4.5"` → anthropic
- ✓ Error when provider not available includes available providers
- ✓ Error when model format is invalid

**Test All Providers Optional:**
- ✓ Registry works with only OpenAI configured
- ✓ Registry works with only Anthropic configured
- ✓ Registry works with only Google configured
- ✓ Error when no providers configured

**Test Backward Compatibility:**
- ✓ Existing `openai:gpt-4o` format still works
- ✓ Existing `anthropic:claude-3-5-sonnet` format still works
- ✓ Existing `google:gemini-1.5-flash` format still works

### Integration Tests

- ✓ End-to-end generation with new model aliases
- ✓ API routes accept new model names
- ✓ Frontend displays new model names correctly

### Frontend Validation

- Verify `modelUtils.ts` abbreviation logic handles new names
- Test model selection dropdown with new aliases
- Verify search results show correct model names

## Migration Path

### Backward Compatibility

All existing code continues to work:
- Existing `provider:model` format unchanged
- API clients using old format see no breaking changes
- Frontend receives model list from API (automatic update)

### New Features

- Users can now use short aliases: `gpt-5`, `sonnet-4.5`, etc.
- Any provider can be used (OpenAI no longer required)
- Clear error messages guide users to available models/providers

## Files to Modify

1. `services/generator/app/providers/registry.py` - Add alias mapping, update methods
2. `services/generator/app/providers/anthropic_provider.py` - Update MODELS list
3. `services/generator/app/providers/google_provider.py` - Update MODELS list
4. `services/generator/app/main.py` - Add startup validation
5. `services/generator/tests/unit/providers/test_registry.py` - Add/update tests
6. `services/generator/tests/unit/providers/test_openai_provider.py` - Update tests
7. `services/generator/tests/unit/providers/test_anthropic_provider.py` - Update tests
8. `services/generator/tests/unit/providers/test_google_provider.py` - Update tests

## Success Criteria

- [ ] All new model aliases work correctly
- [ ] System works with any single provider configured
- [ ] Backward compatibility maintained (existing code works)
- [ ] All tests pass (unit and integration)
- [ ] Clear error messages when providers unavailable
- [ ] Frontend displays new model names correctly

## Future Enhancements

- Add more model aliases as new models are released
- Consider adding model capability filtering in frontend
- Add model deprecation warnings for old model versions
- Consider caching model list responses in API layer
