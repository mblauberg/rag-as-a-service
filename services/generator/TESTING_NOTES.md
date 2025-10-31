# Manual Integration Testing Notes - Model Alias Support

## Date: 2025-10-31

## Status: TO BE PERFORMED

These manual integration tests require real API keys and a running service. They have been documented but not yet executed with production API keys.

---

## Test Procedures

### Test 1: Start Generator Service Locally

**Purpose:** Verify the service starts correctly with at least one provider configured.

**Prerequisites:**
- At least one valid API key (ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY)
- Poetry environment configured
- Port 8002 available

**Steps:**
```bash
cd services/generator
export ANTHROPIC_API_KEY="your-real-key-here"  # Use actual key for one provider
poetry run uvicorn app.main:app --reload --port 8002
```

**Expected Result:**
- Service starts without errors
- Logs show which providers are available
- Service listens on http://localhost:8002

**Status:** TO BE PERFORMED

**Notes:**
- _Will document actual startup logs when executed_
- _Will verify provider initialization messages_

---

### Test 2: Verify /models Endpoint Returns Versioned API Names

**Purpose:** Confirm that the models endpoint returns the correct versioned API model names.

**Prerequisites:**
- Generator service running (from Test 1)
- curl or similar HTTP client

**Steps:**
```bash
curl http://localhost:8002/models | jq '.models[] | {name, display_name}'
```

**Expected Result:**
- Response includes models with versioned API names:
  - `anthropic:claude-sonnet-4-5-20250929` (if Anthropic configured)
  - `anthropic:claude-opus-4-1-20250805` (if Anthropic configured)
  - `anthropic:claude-haiku-4-5-20251001` (if Anthropic configured)
  - `google:gemini-2.5-pro` (if Google configured)
  - `google:gemini-2.5-flash` (if Google configured)
  - `openai:gpt-5` (if OpenAI configured)
  - `openai:gpt-5-mini` (if OpenAI configured)
- Each model includes display_name, description, and capabilities

**Status:** TO BE PERFORMED

**Notes:**
- _Will capture full JSON response when executed_
- _Will verify all configured providers return models_

---

### Test 3: Test Generation with Model Alias

**Purpose:** Verify that model aliases work correctly and route to the proper provider with resolved API names.

**Prerequisites:**
- Generator service running with at least one provider configured
- Sample document chunks for testing

**Steps:**
```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main topics discussed?",
    "chunks": [
      {
        "text": "This is test content about model aliases and API integration.",
        "document_id": "test-doc-1",
        "chunk_index": 0
      }
    ],
    "model": "sonnet-4.5"
  }' | jq
```

**Test Variations:**
- Test with different aliases based on configured providers:
  - `"model": "sonnet-4.5"` (if Anthropic configured)
  - `"model": "opus-4.1"` (if Anthropic configured)
  - `"model": "haiku-4.5"` (if Anthropic configured)
  - `"model": "gpt-5"` (if OpenAI configured)
  - `"model": "gpt-5-mini"` (if OpenAI configured)
  - `"model": "gemini-flash-2.5"` (if Google configured)
  - `"model": "gemini-pro-2.5"` (if Google configured)

**Expected Result:**
- Successful HTTP 200 response
- Response includes:
  - `summary` field with generated content
  - `provider` field matching the correct provider (e.g., "anthropic" for "sonnet-4.5")
  - `model` field showing the alias used
- Generated summary is relevant to the query and context
- No errors in service logs

**Status:** TO BE PERFORMED

**Notes:**
- _Will document response times when executed_
- _Will verify summary quality and relevance_
- _Will test with multiple aliases if multiple providers configured_

---

### Test 4: Test Error Handling for Unavailable Provider

**Purpose:** Verify that helpful error messages are returned when requesting a model from an unconfigured provider.

**Prerequisites:**
- Generator service running with only ONE provider configured (e.g., only ANTHROPIC_API_KEY set)

**Steps:**
```bash
# If only Anthropic is configured, try to use OpenAI model
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "chunks": [
      {
        "text": "test content",
        "document_id": "doc1",
        "chunk_index": 0
      }
    ],
    "model": "gpt-5"
  }' | jq
```

**Expected Result:**
- HTTP 400 or 422 error response
- Error message includes:
  - Clear indication that the provider is not available
  - Mention of "no API key configured"
  - List of available providers
  - Example: `"Provider 'openai' not available (no API key configured). Available providers: ['anthropic']"`

**Status:** TO BE PERFORMED

**Notes:**
- _Will document exact error format when executed_
- _Will verify error message helpfulness_
- _Will test with different provider combinations_

---

## Additional Manual Tests (Optional)

### Test 5: Backward Compatibility with provider:model Format

**Purpose:** Verify that the old `provider:model` format still works.

**Steps:**
```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "chunks": [{"text": "test", "document_id": "d1", "chunk_index": 0}],
    "model": "anthropic:claude-sonnet-4-5-20250929"
  }' | jq
```

**Expected Result:**
- Successful generation
- Same behavior as using alias "sonnet-4.5"

**Status:** TO BE PERFORMED

---

### Test 6: Unknown Model Error Handling

**Purpose:** Verify helpful error for completely unknown models.

**Steps:**
```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "chunks": [{"text": "test", "document_id": "d1", "chunk_index": 0}],
    "model": "unknown-model-xyz"
  }' | jq
```

**Expected Result:**
- Error message stating "Cannot determine provider"
- List of supported aliases shown
- Guidance on using `provider:model` format

**Status:** TO BE PERFORMED

---

## Testing Configuration Matrix

| Test Scenario | Provider(s) Configured | Expected Outcome |
|--------------|------------------------|------------------|
| Only OpenAI | OPENAI_API_KEY | gpt-5, gpt-5-mini work; others error |
| Only Anthropic | ANTHROPIC_API_KEY | sonnet-4.5, opus-4.1, haiku-4.5 work; others error |
| Only Google | GOOGLE_API_KEY | gemini-flash-2.5, gemini-pro-2.5 work; others error |
| All Three | All keys set | All aliases work |
| None | No keys | Service starts but all generate requests fail |

**Status:** TO BE PERFORMED

---

## Checklist for Manual Testing

- [ ] **Test 1:** Service starts with at least one provider
- [ ] **Test 2:** /models endpoint returns correct versioned names
- [ ] **Test 3:** Generation with alias works (test each configured provider)
- [ ] **Test 4:** Error handling for unavailable provider
- [ ] **Test 5:** Backward compatibility with provider:model format
- [ ] **Test 6:** Unknown model error handling
- [ ] **Matrix:** Test with different provider configurations

---

## Important Notes

### Why Manual Testing is Required

These tests require:
1. **Real API Keys:** Live calls to OpenAI, Anthropic, or Google APIs
2. **Running Service:** Full FastAPI application with all dependencies
3. **Network Access:** Actual HTTP requests to provider APIs
4. **Cost Implications:** API calls may incur charges

### How to Execute These Tests

1. **Set up environment:**
   ```bash
   cd services/generator
   cp .env.template .env
   # Edit .env and add at least one real API key
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Run the service:**
   ```bash
   poetry run uvicorn app.main:app --reload --port 8002
   ```

4. **Open a new terminal and execute tests:**
   - Follow each test procedure above
   - Document results in this file
   - Note any unexpected behaviors
   - Capture sample responses

5. **Test different configurations:**
   - Test with only one provider at a time
   - Test with all providers
   - Verify error messages are helpful

### Safety Considerations

- Use test API keys if available (not production keys)
- Monitor API usage and costs
- Use minimal/cheap models for testing where possible
- Consider API rate limits
- Don't commit API keys to version control

---

## Results Section (To Be Completed)

### Execution Date: _TBD_

### Provider Configuration Tested: _TBD_

### Test Results:

#### Test 1: Service Startup
- **Status:**
- **Providers Available:**
- **Notes:**

#### Test 2: /models Endpoint
- **Status:**
- **Models Returned:**
- **Notes:**

#### Test 3: Generation with Aliases
- **Status:**
- **Aliases Tested:**
- **Response Times:**
- **Notes:**

#### Test 4: Error Handling
- **Status:**
- **Error Message:**
- **Notes:**

### Issues Found:
_List any issues discovered during manual testing_

### Recommendations:
_Any improvements or follow-up items identified_

---

## Conclusion

This document provides comprehensive procedures for manually testing the model alias support feature. All tests are marked as "TO BE PERFORMED" and should be executed with real API keys before the feature is considered production-ready.

**Next Steps:**
1. Obtain test API keys for at least one provider
2. Execute Test 1-4 systematically
3. Document results in the Results Section
4. Address any issues found
5. Execute optional tests (Test 5-6) for comprehensive coverage
6. Update this document with findings
7. Consider this feature validated for production use
