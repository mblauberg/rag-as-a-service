# Ollama Removal Design
**Date:** 2025-10-26
**Status:** Design Phase
**Author:** Claude Code with Michael Blauberg

## 1. Context and Motivation

### Current State
The RAAS system currently includes Ollama as an optional local LLM provider alongside OpenAI, Anthropic, and Google. However:
- Ollama is disabled by default (`ENABLE_OLLAMA=false`)
- It has never been successfully run in local development
- It requires significant resources (2-8GB RAM, 1-4 CPU cores)
- It adds deployment complexity without demonstrable value

### Decision Rationale
Based on project goals and constraints:
- **Goal:** Build a production-ready RAG system with depth over breadth
- **Deployment:** Local Kind cluster (primary), optional GCP (secondary)
- **Platform:** M1 MacBook Pro (ARM architecture, potential Docker compatibility issues)
- **Resources:** Limited local RAM; removing Ollama frees 2-8GB for core services
- **Status:** "Nice to have" feature that hasn't been validated

### Benefits of Removal
1. **Simplified Architecture:** Fewer moving parts, clearer deployment story
2. **Resource Efficiency:** ~2-8GB RAM freed for API/Embedder/Generator scaling
3. **Faster Iteration:** No Ollama container builds or model pulls
4. **Reduced Test Surface:** Less code to maintain and test
5. **Honest Documentation:** Don't claim unvalidated features
6. **Better Focus:** Invest time in core RAG capabilities

### What We Retain
The architecture still demonstrates:
- Multi-provider LLM abstraction (OpenAI, Anthropic, Google)
- Provider registry pattern with graceful degradation
- Configuration-driven model selection
- Clean separation between provider interface and implementation

---

## 2. Scope of Changes

### Files to Delete Entirely

**Infrastructure:**
- `infrastructure/k8s/base/ollama/deployment.yaml`
- `infrastructure/k8s/base/ollama/service.yaml`
- `infrastructure/k8s/base/ollama/pvc.yaml`
- `infrastructure/scripts/init-ollama.sh`

**Generator Service Code:**
- `services/generator/app/providers/ollama_provider.py`
- `services/generator/app/services/ollama_client.py`
- `services/generator/tests/unit/providers/test_ollama_provider.py`
- `services/generator/tests/unit/clients/test_ollama_client.py`

### Files to Modify

**Infrastructure:**
- `infrastructure/docker-compose/docker-compose.yml` - Remove ollama service and volume
- `infrastructure/k8s/base/kustomization.yaml` - Remove ollama resource references
- `infrastructure/k8s/overlays/local/storage-patches.yaml` - Remove ollama PVC patches (if present)

**Generator Service:**
- `services/generator/app/core/config.py` - Remove ollama_url, enable_ollama
- `services/generator/app/providers/registry.py` - Remove OllamaProvider registration
- `services/generator/app/providers/base.py` - Review for Ollama-specific code
- `services/generator/app/models/schemas.py` - Remove ollama model references
- `services/generator/.env.example` - Remove OLLAMA_* variables
- `services/generator/README.md` - Update provider documentation

**Tests:**
- `services/generator/tests/conftest.py` - Remove Ollama fixtures
- `services/generator/tests/unit/test_config.py` - Remove Ollama config tests
- `services/generator/tests/unit/test_schemas.py` - Remove Ollama schema tests
- `services/generator/tests/unit/services/test_generation_service.py` - Remove Ollama integration tests
- `tests/integration/test_multi_provider.sh` - Remove Ollama test cases

**Documentation:**
- `docs/PROPOSAL.md` - Update architecture diagram and provider list
- `README.md` - Update features and deployment instructions
- `services/generator/README.md` - Update supported providers
- `infrastructure/k8s/README.md` - Update service list

**Frontend (if applicable):**
- `services/frontend/src/types/index.ts` - Check for ollama model references
- `services/frontend/src/components/search/EnhancedSearchBar.tsx` - Remove ollama from model list
- `services/frontend/src/utils/__tests__/modelUtils.test.ts` - Remove ollama test cases

---

## 3. Detailed Implementation Plan

### Phase 1: Infrastructure Removal

**Task 1.1: Remove Ollama from docker-compose**
- Delete `ollama` service definition (lines 118-132)
- Delete `ollama-data` volume (line 178)
- Remove `ollama` from generator service health check dependency (if present)
- Verify no other services reference `ollama` container

**Task 1.2: Remove Ollama from Kubernetes manifests**
- Delete `infrastructure/k8s/base/ollama/` directory entirely
- Remove ollama resources from `infrastructure/k8s/base/kustomization.yaml`
- Check `infrastructure/k8s/overlays/local/` for ollama-specific patches
- Remove ollama init script: `infrastructure/scripts/init-ollama.sh`

**Task 1.3: Update Kubernetes documentation**
- Update `infrastructure/k8s/README.md` service list (remove Ollama entry)
- Verify no deployment guides reference Ollama setup

### Phase 2: Generator Service Code Removal

**Task 2.1: Remove Ollama provider implementation**
- Delete `services/generator/app/providers/ollama_provider.py`
- Delete `services/generator/app/services/ollama_client.py`
- Verify no other files import from these modules

**Task 2.2: Update provider registry**
File: `services/generator/app/providers/registry.py`
- Remove `from app.providers.ollama_provider import OllamaProvider` import
- Remove OllamaProvider from registry initialization
- Ensure registry still works with remaining providers (OpenAI, Anthropic, Google)

**Task 2.3: Update configuration**
File: `services/generator/app/core/config.py`
- Remove `ollama_url: str` field
- Remove `enable_ollama: bool` field
- Keep provider abstraction intact

File: `services/generator/.env.example`
- Remove `OLLAMA_URL` variable
- Remove `ENABLE_OLLAMA` variable
- Add comment explaining supported providers (OpenAI, Anthropic, Google)

**Task 2.4: Update schemas**
File: `services/generator/app/models/schemas.py`
- Search for any ollama-specific model names or enum values
- Remove ollama model references while preserving schema structure
- Ensure model validation still works for remaining providers

**Task 2.5: Update generator documentation**
File: `services/generator/README.md`
- Update "Supported Providers" section (remove Ollama)
- Update environment variable documentation
- Update example configurations
- Add note about why cloud providers only (production-ready, reliable, scalable)

### Phase 3: Test Suite Updates

**Task 3.1: Remove Ollama unit tests**
- Delete `services/generator/tests/unit/providers/test_ollama_provider.py`
- Delete `services/generator/tests/unit/clients/test_ollama_client.py`

**Task 3.2: Update test fixtures**
File: `services/generator/tests/conftest.py`
- Remove any Ollama-specific fixtures (mock clients, test data)
- Verify remaining fixtures still work

**Task 3.3: Update config tests**
File: `services/generator/tests/unit/test_config.py`
- Remove tests for `ollama_url` configuration
- Remove tests for `enable_ollama` flag
- Ensure other config tests still pass

**Task 3.4: Update schema tests**
File: `services/generator/tests/unit/test_schemas.py`
- Remove ollama model validation tests
- Verify remaining schema tests cover OpenAI/Anthropic/Google models

**Task 3.5: Update service integration tests**
File: `services/generator/tests/unit/services/test_generation_service.py`
- Remove tests for Ollama provider integration
- Ensure multi-provider tests cover remaining providers

**Task 3.6: Update integration test scripts**
File: `tests/integration/test_multi_provider.sh`
- Remove Ollama test cases
- Update script comments to reflect supported providers
- Verify script still tests provider switching correctly

### Phase 4: Frontend Updates

**Task 4.1: Update TypeScript types**
File: `services/frontend/src/types/index.ts`
- Search for `ollama` in model type definitions
- Remove ollama model references from type unions/enums

**Task 4.2: Update search components**
File: `services/frontend/src/components/search/EnhancedSearchBar.tsx`
- Remove ollama from model selection dropdown (if present)
- Ensure model list still renders correctly

**Task 4.3: Update frontend tests**
File: `services/frontend/src/utils/__tests__/modelUtils.test.ts`
- Remove ollama model utility tests
- Verify remaining model utilities work

File: `services/frontend/src/components/search/__tests__/EnhancedSearchBar.test.tsx`
- Remove ollama model selection tests (if present)

### Phase 5: Documentation Updates

**Task 5.1: Update proposal**
File: `docs/PROPOSAL.md`

Current text (line 16):
> "For text generation, the system integrates OpenAI's GPT-5 Mini—released in August 2025—though it supports multiple LLM providers including Anthropic, Google, and locally-hosted Ollama models."

Updated:
> "For text generation, the system integrates OpenAI's GPT-5 Mini—released in August 2025—with support for multiple cloud LLM providers including Anthropic Claude and Google Gemini for provider flexibility and graceful degradation."

Current text (line 48):
> "Text generation relies on OpenAI's GPT-5 Mini model—the latest efficient reasoning model released in August 2025—though the system supports multiple providers including Anthropic, Google, and locally-hosted Ollama models."

Updated:
> "Text generation relies on OpenAI's GPT-5 Mini model—the latest efficient reasoning model released in August 2025—with support for Anthropic Claude and Google Gemini as alternative providers. The provider abstraction enables graceful degradation and vendor-agnostic deployment."

Architecture diagram (lines 115-121):
- Remove Ollama box from diagram
- Update table to remove Ollama row (line 134)

**Task 5.2: Update main README**
File: `README.md`
- Search for "ollama" references (case-insensitive)
- Update features list to focus on multi-cloud provider support
- Update deployment instructions to remove Ollama setup steps
- Update architecture overview

**Task 5.3: Update test documentation**
File: `tests/README.md`
- Remove Ollama from test coverage documentation
- Update provider testing instructions

### Phase 6: Verification and Cleanup

**Task 6.1: Grep for remaining references**
```bash
# Search entire codebase for ollama references
grep -ri "ollama" --exclude-dir=node_modules --exclude-dir=.git \
  --exclude-dir=__pycache__ --exclude-dir=.venv
```

**Task 6.2: Verify generator service health**
```bash
cd services/generator
poetry run pytest -v
poetry run python -m app.main  # Verify service starts
```

**Task 6.3: Verify docker-compose deployment**
```bash
cd infrastructure/docker-compose
docker-compose config  # Validate YAML
docker-compose up -d
docker-compose ps  # Ensure all services healthy
```

**Task 6.4: Verify Kubernetes deployment**
```bash
kubectl kustomize infrastructure/k8s/overlays/local/
# Verify no ollama resources in output
```

**Task 6.5: Verify frontend builds**
```bash
cd services/frontend
npm run type-check
npm run build
```

---

## 4. Risk Assessment and Mitigation

### Risks

**Risk 1: Breaking provider abstraction pattern**
- **Likelihood:** Low
- **Impact:** Medium
- **Mitigation:** Keep `providers/base.py` intact; only remove Ollama implementation
- **Test:** Verify OpenAI/Anthropic/Google providers still work via unit tests

**Risk 2: Frontend model selection breaks**
- **Likelihood:** Low
- **Impact:** Medium
- **Mitigation:** Update TypeScript types before removing backend code
- **Test:** Run `npm run type-check` and frontend tests

**Risk 3: Missing references in documentation**
- **Likelihood:** Medium
- **Impact:** Low
- **Mitigation:** Comprehensive grep search before finalizing
- **Test:** Search for "ollama" case-insensitively across all docs

**Risk 4: Integration tests assume Ollama availability**
- **Likelihood:** Medium
- **Impact:** Medium
- **Mitigation:** Review all test scripts and conftest.py fixtures
- **Test:** Run full test suite after removal

### Rollback Plan
If removal causes issues:
1. Git history preserves all deleted code
2. Can restore with: `git checkout HEAD~1 -- <file_path>`
3. All changes are in a single commit for easy revert

---

## 5. Success Criteria

### Functional Requirements
- [ ] Generator service starts successfully without Ollama
- [ ] OpenAI provider generates responses correctly
- [ ] Anthropic provider works (if API key configured)
- [ ] Google provider works (if API key configured)
- [ ] Frontend model selection UI works
- [ ] All unit tests pass (generator service)
- [ ] All integration tests pass (multi-provider)
- [ ] All frontend tests pass

### Non-Functional Requirements
- [ ] No "ollama" references in codebase (except this design doc and git history)
- [ ] Docker-compose deploys successfully
- [ ] Kubernetes manifests validate with kustomize
- [ ] Documentation accurately reflects supported providers
- [ ] Memory usage improved by ~2-8GB in local deployments

### Documentation Requirements
- [ ] PROPOSAL.md updated with accurate provider list
- [ ] README.md reflects current architecture
- [ ] Generator README.md documents cloud providers only
- [ ] Architecture diagrams show 3 cloud providers (not 4 including Ollama)

---

## 6. Timeline Estimate

Assuming sequential implementation:
- **Phase 1 (Infrastructure):** 15 minutes
- **Phase 2 (Generator Code):** 30 minutes
- **Phase 3 (Tests):** 30 minutes
- **Phase 4 (Frontend):** 20 minutes
- **Phase 5 (Documentation):** 30 minutes
- **Phase 6 (Verification):** 30 minutes

**Total:** ~2.5 hours (includes testing and verification)

With parallel task execution (multiple agents):
**Total:** ~45 minutes

---

## 7. Open Questions

1. **Should we keep the provider abstraction pattern documentation?**
   - Yes - this is still valuable architecture, just with 3 providers instead of 4

2. **Should we add a note explaining why cloud-only providers?**
   - Yes - in README and proposal, emphasize production-readiness and reliability

3. **Do we need a migration guide for existing deployments?**
   - No - Ollama was disabled by default, no active users affected

4. **Should we preserve Ollama code in a separate branch?**
   - No - git history is sufficient; reduces maintenance burden

---

## 8. Future Considerations

### If Local LLM Support Needed Later
Instead of reintroducing Ollama:
- Consider modal.com or Replicate for serverless inference
- Use Hugging Face Inference API (cloud-managed)
- Use Azure OpenAI for enterprise scenarios

### Alternative Architecture
If cost becomes a concern with cloud providers:
- Implement response caching (reduce API calls)
- Add request throttling (prevent cost spikes)
- Use cheaper models for non-critical queries (gpt-5-mini is already cost-efficient)

---

## 9. Implementation Approach

Recommend using `superpowers:subagent-driven-development` skill:
1. Create worktree: `feature/remove-ollama`
2. Split tasks into 6 phases (as outlined above)
3. Dispatch parallel agents for independent tasks:
   - Agent 1: Phase 1 (Infrastructure)
   - Agent 2: Phase 2 (Generator Code)
   - Agent 3: Phase 3 (Tests)
   - Agent 4: Phase 4 (Frontend)
   - Agent 5: Phase 5 (Documentation)
4. Sequential verification (Phase 6)
5. Code review with `superpowers:requesting-code-review`
6. Merge to master

---

## 10. Appendix: Affected Files Checklist

### Infrastructure (6 files)
- [ ] `infrastructure/docker-compose/docker-compose.yml` (modify)
- [ ] `infrastructure/k8s/base/kustomization.yaml` (modify)
- [ ] `infrastructure/k8s/base/ollama/deployment.yaml` (delete)
- [ ] `infrastructure/k8s/base/ollama/service.yaml` (delete)
- [ ] `infrastructure/k8s/base/ollama/pvc.yaml` (delete)
- [ ] `infrastructure/scripts/init-ollama.sh` (delete)

### Generator Service (11 files)
- [ ] `services/generator/app/core/config.py` (modify)
- [ ] `services/generator/app/providers/registry.py` (modify)
- [ ] `services/generator/app/providers/base.py` (review)
- [ ] `services/generator/app/models/schemas.py` (modify)
- [ ] `services/generator/app/providers/ollama_provider.py` (delete)
- [ ] `services/generator/app/services/ollama_client.py` (delete)
- [ ] `services/generator/.env.example` (modify)
- [ ] `services/generator/README.md` (modify)
- [ ] `services/generator/tests/conftest.py` (modify)
- [ ] `services/generator/tests/unit/test_config.py` (modify)
- [ ] `services/generator/tests/unit/test_schemas.py` (modify)

### Generator Tests (4 files)
- [ ] `services/generator/tests/unit/providers/test_ollama_provider.py` (delete)
- [ ] `services/generator/tests/unit/clients/test_ollama_client.py` (delete)
- [ ] `services/generator/tests/unit/services/test_generation_service.py` (modify)
- [ ] `tests/integration/test_multi_provider.sh` (modify)

### Frontend (3 files)
- [ ] `services/frontend/src/types/index.ts` (modify if needed)
- [ ] `services/frontend/src/components/search/EnhancedSearchBar.tsx` (modify if needed)
- [ ] `services/frontend/src/utils/__tests__/modelUtils.test.ts` (modify if needed)

### Documentation (4 files)
- [ ] `docs/PROPOSAL.md` (modify)
- [ ] `README.md` (modify)
- [ ] `tests/README.md` (modify)
- [ ] `infrastructure/k8s/README.md` (modify)

**Total:** 28 files affected (10 delete, 18 modify)
