# RAAS Project Cleanup and SOLID Refactoring Design

**Date:** 2025-10-24
**Type:** Maintenance & Quality Improvement
**Status:** Ready to Execute
**Scope:** All services (API, Embedder, Frontend) + Documentation
**Branch:** `feature/cleanup-and-refactoring`
**Parallel Work:** `feature/critical-rag-optimizations` (independent RAG improvements)

## Executive Summary

This design addresses project cleanup (junk files, outdated documentation) and SOLID principle violations through a parallel three-track approach:

- **Track A**: Immediate safe cleanup (file relocations, deletions, gitignore fixes)
- **Track B**: Component-by-component SOLID refactoring using subagent-driven development
- **Track C**: Cross-cutting polish (error handling, consistency, minor optimizations)

**Approach:** Moderate refactoring with improvements while refactoring. Track A executes immediately and merges independently. Track B components run in parallel via subagents, each with TDD and code review. Track C applies polish after refactors complete.

**Estimated Effort:** 10-15 hours total across all tracks.

## Goals

1. **Clean Repository**: Remove junk files, outdated docs, and generated artifacts from git
2. **SOLID Compliance**: Fix Single Responsibility and Dependency Inversion violations
3. **Improved Testability**: Enable easier testing through dependency injection
4. **Better Error Handling**: Consistent, user-friendly error messages across services
5. **Code Quality**: Eliminate duplication, improve consistency, add missing tests

## Constraints & Decisions

**Risk Level:** Moderate
- Safe cleanup operations only in Track A
- Component refactors split large files into focused classes
- Comprehensive tests verify no behavior changes

**Behavior Preservation:** Improve while refactoring
- Fix obvious issues during refactoring (better error messages, consistent exception handling)
- Minor efficiency gains allowed when discovered
- Exact behavior preserved for core functionality

**Execution Strategy:** Parallel tracks with subagent-driven development
- Track A: Sequential cleanup (single agent, immediate)
- Track B: Parallel component refactors (subagents with TDD + code review)
- Track C: Sequential polish after A & B complete

## Current State Assessment

**Last Updated:** 2025-10-24

**Note on Parallel Work:**
The `feature/critical-rag-optimizations` branch is running in parallel implementing RAG improvements (BGE-M3 embeddings upgrade, BM25 sparse search, reciprocal rank fusion). This work is independent and can be merged separately. This cleanup and refactoring work is focused solely on code quality, organization, and testing.

### Issues Identified

**File Organization:**
- 7 test files at project root (various Playwright/integration tests)
- Generated files may still be tracked in git (need verification)
- Duplicate Claude settings file may exist (`.claude/settings.local 2.json`)

**Documentation:**
- Previous cleanup (commit f53bc98) removed some outdated plans
- Current plan documents in docs/plans/ need review
- RAG optimization plan files are active for parallel work

**Code Quality (SOLID Violations):**
- `document_service.py` at 380 lines violates Single Responsibility Principle
- Global service singletons prevent proper dependency injection
- `DocumentProcessingService()` created internally instead of injected
- Duplicate formatting functions across frontend components

**Testing:**
- Frontend has only 1 test file (`modelUtils.test.ts`)
- Missing tests for key React components (SearchBar, UploadModal, DocumentCard)
- Backend tests exist but could benefit from better fixtures

## Design: Three-Track Parallel Approach

```
Timeline:  [===============================================]

Track A:   [====]                                    (merge immediately)
           Cleanup

Track B:   [=================]                       (merge as each completes)
           B1: Split document_service.py
           B2: Fix DI violations
           B3: Add frontend tests

Track C:                      [=================]    (merge after B completes)
                              Polish & consistency
```

### Track Integration Strategy

1. **Track A** merges to master immediately (zero risk, no code changes)
2. **Track B** components merge independently as each completes (code review gates)
3. **Track C** merges last after reviewing all Track B refactored code

---

## Track A: Immediate Safe Cleanup

**Objective:** Clean repository of junk files and outdated documentation without any code changes.

### A1: File Relocations

**Move misplaced test files to proper location:**

```bash
# From project root to tests/integration/
test_upload_search.py   → tests/integration/test_upload_search.py
test_webapp.py          → tests/integration/test_webapp.py
```

**Verification:**
- Run `pytest tests/integration/` to ensure tests still pass
- Update any import paths if necessary (both use Playwright, should work without changes)

### A2: Generated File Cleanup

**Remove from git tracking (but keep local):**

```bash
git rm -r --cached services/api/htmlcov/
git rm -r --cached services/api/.pytest_cache/
git rm -r --cached services/generator/.pytest_cache/
find . -type d -name "__pycache__" -exec git rm -r --cached {} + 2>/dev/null
```

**Delete duplicate settings:**
```bash
rm .claude/settings.local\ 2.json
```

**Rationale:** These are generated at runtime and should never be in git.

### A3: Outdated Documentation Cleanup

**Delete completed/outdated plan files (8 files):**

```bash
# All merged or completed features
docs/plans/2025-10-23-comprehensive-quality-improvements-design.md
docs/plans/2025-10-23-comprehensive-quality-improvements.md
docs/plans/2025-10-24-complete-phase4-frontend-refactor.md
docs/plans/2025-10-24-kubernetes-scaffolding-design.md
docs/plans/2025-10-24-kubernetes-scaffolding-implementation.md
docs/plans/2025-10-24-kubernetes-scalability-resilience-design.md
docs/plans/2025-10-24-project-cleanup-design.md
docs/plans/2025-10-24-semantic-chunking-remaining-tasks.md
```

**Keep RAG optimization plans (2 files):**
```bash
docs/plans/2025-01-24-critical-rag-optimizations.md       # Future work
docs/plans/2025-10-24-rag-optimization-implementation.md  # Future work
```

**Review large documentation files:**
- `docs/ENHANCEMENT_PRIORITIZATION_PLAN.md` (743 lines) - Archive or delete if outdated
- `docs/RAG_OPTIMIZATION_ANALYSIS.md` (804 lines) - Keep if relevant for future RAG work

**Decision criteria:** If document contains info not captured elsewhere and still relevant to future work, keep it. Otherwise archive to `docs/archive/` or delete.

### A4: Enhanced .gitignore

**Add comprehensive exclusions:**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
htmlcov/
.coverage
.coverage.*
.mypy_cache/
.dmypy.json
dmypy.json

# Virtual environments
.env.local
.venv/
.venv*/
venv/
venv*/
ENV/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
Thumbs.db

# Claude Code
.claude/settings.local*.json
```

### A5: Verification & Commit

**Verification steps:**
1. Run `git status` - no tracked generated files
2. Run `pytest services/api/tests/` - all tests pass
3. Run `pytest tests/integration/` - relocated tests pass
4. Check `docs/plans/` - only 2 RAG files remain

**Commit:**
```bash
git add -A
git commit -m "chore: comprehensive project cleanup

- Move test files to proper integration test directory
- Remove generated files from git tracking (htmlcov, pytest_cache, __pycache__)
- Delete 8 outdated plan documents for completed features
- Delete duplicate Claude settings file
- Enhance .gitignore with comprehensive exclusions

Preserves:
- 2 RAG optimization plan documents (future work)
- All user-facing documentation (setup guides, references)
- All integration tests and utility scripts"
```

**Time estimate:** 30-45 minutes
**Risk level:** Minimal (no code changes, only file operations)

---

## Track B: Component Refactoring (Subagent-Driven Development)

**Objective:** Refactor components in parallel using independent subagents, each following TDD and code review.

**Methodology:** Use `superpowers:subagent-driven-development` skill:
- Each subagent is a fresh session with no prior context baggage
- Test-Driven Development: write failing tests first
- Code review between tasks (verify against plan and coding standards)
- Each component merges independently when complete

### B1: Split document_service.py (API Service)

**Problem:** 380-line file violates Single Responsibility Principle. Handles upload, chunking orchestration, metadata management, and deletion in one class.

**Solution:** Extract into focused service classes.

**New Structure:**

```
services/api/app/services/
├── document_service.py          # Facade orchestrating the services below
├── document_upload_service.py   # File I/O, validation, storage
├── document_metadata_service.py # Database CRUD operations
└── chunking_orchestrator.py     # Coordinate chunking and embedding requests
```

**Service Responsibilities:**

**DocumentUploadService:**
- Validate uploaded file (type, size)
- Save file to disk with proper naming
- Extract text content from file
- Return file metadata (path, size, type)

**DocumentMetadataService:**
- Create document records in PostgreSQL
- Update document status fields
- Query documents (list, detail, by ID)
- Delete document records (cascades to chunks)

**ChunkingOrchestrator:**
- Split text into chunks using chunking service
- Create chunk records in database
- Send chunks to embedder service for vector generation
- Update embedding status

**DocumentService (Facade):**
- Orchestrate upload flow: upload → metadata → chunking → embedding
- Coordinate deletion: Qdrant → file → database
- Provide high-level operations for route handlers

**Refactoring Steps:**

1. **Write tests first** (TDD):
   - Test each new service class independently
   - Mock dependencies (database, file system, embedder client)
   - Verify original behavior preserved

2. **Extract DocumentUploadService:**
   - Move file validation and storage logic
   - Add constructor accepting `upload_dir` parameter
   - All file operations isolated here

3. **Extract DocumentMetadataService:**
   - Move database query logic
   - Accept `AsyncSession` in methods (not in constructor)
   - Pure database operations, no business logic

4. **Extract ChunkingOrchestrator:**
   - Move chunking and embedding coordination
   - Accept dependencies via constructor
   - Handle embedding status updates

5. **Update DocumentService facade:**
   - Instantiate sub-services via dependency injection
   - Delegate to appropriate service
   - Maintain same public interface for routes

6. **Update dependency injection:**
   - Add factory functions in `core/dependencies.py` for new services
   - Route handlers inject `DocumentService` facade (backward compatible)

7. **Run all tests:**
   - Verify integration tests still pass
   - Check coverage increased (more unit tests added)

**Success Criteria:**
- All existing tests pass
- New unit tests for each service class (>80% coverage)
- `document_service.py` under 150 lines (now just a facade)
- Zero duplicate code between services

**Time estimate:** 3-4 hours

### B2: Fix Dependency Injection Violations (API Service)

**Problem:** Services create dependencies internally instead of accepting via constructor:
- `DocumentProcessingService()` instantiated inside `document_service.py`
- Global singleton instances at module level
- Routes import services directly instead of using `Depends()`

**Solution:** Proper dependency injection throughout.

**Refactoring Steps:**

1. **Update service constructors:**
   - Remove all internal object creation
   - Accept dependencies as constructor parameters
   - Store as instance variables

2. **Create factory functions in `core/dependencies.py`:**
   ```python
   def get_document_service() -> DocumentService:
       return DocumentService(
           upload_service=DocumentUploadService(upload_dir=Path(settings.upload_dir)),
           metadata_service=DocumentMetadataService(),
           chunking_orchestrator=ChunkingOrchestrator(
               embedder_client=get_embedder_client()
           )
       )

   def get_embedder_client() -> EmbedderClient:
       return EmbedderClient(url=settings.embedder_url)

   def get_qdrant_client() -> QdrantClientWrapper:
       return QdrantClientWrapper(url=settings.qdrant_url)
   ```

3. **Remove global instances:**
   - Delete `document_service = DocumentService()` at module level
   - Delete `embedder_client = EmbedderClient()` at module level
   - Delete any other global service instances

4. **Update route handlers:**
   - Add `Depends()` for all service dependencies
   - Example:
     ```python
     @router.post("/upload")
     async def upload_document(
         file: UploadFile = File(...),
         title: str = Form(...),
         db: AsyncSession = Depends(get_db),
         doc_service: DocumentService = Depends(get_document_service)
     ):
         return await doc_service.upload(db, file, title)
     ```

5. **Update tests:**
   - Create test fixtures that return mock services
   - Override `app.dependency_overrides` in test setup
   - Verify dependency injection works correctly

**Success Criteria:**
- Zero global service instances
- All dependencies injected via constructors or `Depends()`
- Tests can easily mock dependencies
- Routes no longer import service implementations directly

**Time estimate:** 2-3 hours

### B3: Add Frontend Component Tests

**Problem:** Only 1 test file exists (`modelUtils.test.ts`). No tests for React components.

**Solution:** Comprehensive component testing with Vitest + React Testing Library.

**Test Coverage Target:**

```
services/frontend/src/
├── components/
│   ├── search/__tests__/
│   │   └── EnhancedSearchBar.test.tsx      # NEW
│   ├── upload/__tests__/
│   │   └── UploadModal.test.tsx            # NEW
│   ├── documents/__tests__/
│   │   └── DocumentCard.test.tsx           # NEW
├── utils/__tests__/
│   ├── formatters.test.ts                  # NEW
│   └── modelUtils.test.ts                  # EXISTS
```

**Test Scenarios:**

**EnhancedSearchBar.test.tsx:**
- Renders with placeholder text
- Calls onChange when user types
- Focuses input when "/" key pressed
- Clears input when Escape pressed
- Shows keyboard hint badge

**UploadModal.test.tsx:**
- Opens and closes dialog
- Handles file selection via input
- Handles drag-and-drop file upload
- Validates file types (PDF, DOCX, TXT)
- Shows error for invalid file types
- Auto-fills title from filename
- Calls mutation on submit
- Shows loading state during upload

**DocumentCard.test.tsx:**
- Renders document information correctly
- Formats date using utility function
- Formats file size using utility function
- Shows correct status badge color
- Handles click to navigate

**formatters.test.ts:**
- `formatDate()` formats with and without time
- `formatFileSize()` handles bytes, KB, MB correctly
- `getStatusColor()` returns correct Tailwind classes
- Edge cases (0 bytes, undefined status)

**Testing Approach:**

1. **Set up test utilities:**
   - Create `test/test-utils.tsx` with custom render that includes providers
   - Mock React Query client
   - Mock React Router

2. **Write component tests:**
   - Use `@testing-library/react` for rendering
   - Use `@testing-library/user-event` for interactions
   - Mock API calls with `vi.mock()`
   - Test user behavior, not implementation details

3. **Run coverage:**
   ```bash
   npm test -- --coverage
   ```
   - Target: >80% coverage for components
   - Focus on user interactions and edge cases

**Success Criteria:**
- All 4 new test files created
- Tests pass consistently
- Coverage >80% for tested components
- No flaky tests (use `waitFor` for async operations)

**Time estimate:** 3-4 hours

### B4: Subagent Execution Process

For each component (B1, B2, B3):

1. **Dispatch subagent** with task specification from this design
2. **Subagent follows TDD:**
   - Read failing test
   - Implement minimal code to pass
   - Refactor for quality
3. **Subagent runs all tests** to verify no regressions
4. **Subagent commits** with descriptive message
5. **Code review agent** validates against plan and standards
6. **Merge to master** when review passes

**Parallel execution:** All three components can run simultaneously (independent codebases).

---

## Track C: Cross-Cutting Polish

**Objective:** Apply consistent improvements across all services after component refactors complete.

**Execution:** Sequential (single agent), after reviewing all Track B refactored code.

### C1: Standardize Error Handling

**Backend:**

Create consistent exception handling patterns:

1. **Ensure all services use custom exceptions:**
   - Review all service files for `except Exception as e`
   - Replace with specific exception types from `core/exceptions.py`
   - Add new custom exceptions if needed (e.g., `ChunkingError`, `ValidationError`)

2. **Add request ID to error responses:**
   - Middleware already adds `X-Request-ID` header
   - Include request ID in error response body
   - Log request ID with all error messages

3. **Standardize error log format:**
   ```python
   logger.error(
       f"[{request_id}] Failed to process document {document_id}",
       exc_info=True,
       extra={"document_id": str(document_id), "request_id": request_id}
   )
   ```

**Frontend:**

1. **Use shadcn/ui Toast for all errors:**
   - Replace `alert()` calls with Toast notifications
   - Centralize error handling in API client
   - Extract user-friendly message from API error responses

2. **Add error boundary fallbacks:**
   - Already have top-level ErrorBoundary
   - Add specific boundaries for async data loading sections
   - Show "retry" button when appropriate

3. **User-friendly error messages:**
   - Map API error types to friendly messages
   - Example mapping:
     ```typescript
     const ERROR_MESSAGES = {
       'DocumentNotFoundError': 'The document you requested could not be found.',
       'EmbeddingFailedError': 'Unable to process document. Please try again.',
       'InvalidFileTypeError': 'This file type is not supported. Please upload PDF, DOCX, or TXT files.'
     }
     ```

### C2: Improve Error Messages

**Replace generic messages with actionable ones:**

**Backend Examples:**

| Before | After |
|--------|-------|
| `"File processing failed"` | `"Unable to extract text from '{filename}'. The file may be password-protected or corrupted."` |
| `"Embedding failed"` | `"Vector embedding service unavailable. Your document has been saved and will be processed automatically when the service recovers."` |
| `"Document not found"` | `"Document '{document_id}' not found. It may have been deleted."` |
| `"Invalid file type"` | `"File type '.{ext}' is not supported. Please upload PDF (.pdf), Word (.docx), or plain text (.txt) files."` |

**Frontend Examples:**

| Before | After |
|--------|-------|
| `"Upload failed"` | `"Unable to upload '{filename}'. Please check your connection and try again."` |
| `"Search error"` | `"Search is temporarily unavailable. Your documents are safe and will be searchable again shortly."` |
| `"Network error"` | `"Unable to connect to the server. Please check your internet connection."` |

**Implementation:**
- Update exception messages in `core/exceptions.py`
- Add context variables to error messages (filename, document_id, etc.)
- Review all user-facing error messages for clarity

### C3: Minor Efficiency Gains

**Backend Optimizations:**

1. **HTTP client connection pooling:**
   - Verify `httpx.AsyncClient` configured with connection pool
   - Set reasonable limits (max connections, timeout)
   - Reuse client instances (don't create per request)

2. **Database query optimization:**
   - Use `defer()` for loading large text fields only when needed
   - Select only required columns in list queries
   - Add database indexes if missing (check `migrations/`)

3. **Response compression:**
   - Enable gzip compression for API responses
   - Add to FastAPI middleware configuration

**Frontend Optimizations:**

1. **Code splitting:**
   - Lazy load DocumentDetailPage route
   - Split vendor bundle if large

2. **Image optimization:**
   - Add width/height to SVG icons
   - Use appropriate icon sizes (don't scale down large icons)

3. **Caching headers:**
   - Nginx serves frontend with proper cache headers
   - Static assets cached appropriately

**Implementation:**
- Profile before and after to measure impact
- Only implement optimizations that show measurable improvement
- Don't optimize prematurely (focus on readability)

### C4: Code Consistency

**Backend Formatting:**

```bash
cd services/api
poetry run black .
poetry run isort .
poetry run mypy app/
```

**Checks:**
- All async functions properly use `await` (no blocking calls)
- Type hints on all function signatures
- Docstrings follow Google style guide
- No unused imports

**Frontend Formatting:**

```bash
cd services/frontend
npx prettier --write "src/**/*.{ts,tsx}"
npx eslint "src/**/*.{ts,tsx}" --fix
```

**Checks:**
- Consistent import ordering (React, libraries, local)
- `const`/`let` used appropriately (no `var`)
- All components use TypeScript strict mode
- No `any` types without explanation

**Implementation:**
- Run formatters and fix auto-fixable issues
- Manually address remaining lint warnings
- Update CI to enforce formatting on future commits

**Time estimate:** 2-3 hours
**Risk level:** Low (tests verify behavior preserved)

---

## Implementation Plan

### Phase 1: Execute Track A (Immediate)

**Executor:** Single agent
**Duration:** 30-45 minutes
**Steps:**

1. Move test files to `tests/integration/`
2. Remove generated files from git tracking
3. Delete outdated plan documents
4. Review and archive/delete large docs
5. Update `.gitignore`
6. Run verification tests
7. Commit and merge to master

**Output:** Clean repository, ready for refactoring

### Phase 2: Execute Track B (Parallel Subagents)

**Executor:** 3 subagents in parallel
**Duration:** 3-4 hours (wall time, parallel execution)
**Steps:**

1. Dispatch subagent B1 for `document_service.py` split
2. Dispatch subagent B2 for DI fixes
3. Dispatch subagent B3 for frontend tests
4. Each subagent:
   - Writes failing tests (TDD)
   - Implements refactor
   - Runs all tests
   - Commits changes
   - Code review validates
5. Merge each component as it completes

**Output:** SOLID-compliant services, comprehensive tests

### Phase 3: Execute Track C (Sequential)

**Executor:** Single agent
**Duration:** 2-3 hours
**Steps:**

1. Review all Track B refactored code
2. Standardize error handling patterns
3. Improve error messages
4. Implement minor efficiency gains
5. Apply code formatting and consistency
6. Run all tests to verify
7. Commit and merge to master

**Output:** Polished, production-ready codebase

---

## Success Criteria

**Repository Cleanliness:**
- ✅ No test files at project root
- ✅ No generated files tracked in git
- ✅ Only 2 plan docs remain (RAG work)
- ✅ Comprehensive `.gitignore` in place

**SOLID Compliance:**
- ✅ No file >200 lines (excluding tests)
- ✅ Each service has single, clear responsibility
- ✅ Zero global service singletons
- ✅ All dependencies injected

**Test Coverage:**
- ✅ Backend tests >80% coverage
- ✅ Frontend component tests exist and pass
- ✅ All integration tests pass
- ✅ No flaky tests

**Code Quality:**
- ✅ Zero TypeScript errors
- ✅ All formatters pass (black, prettier)
- ✅ Consistent error handling across services
- ✅ User-friendly error messages

**Build & Deploy:**
- ✅ All Docker Compose services start successfully
- ✅ Integration tests pass end-to-end
- ✅ No console errors in browser
- ✅ Application works as before (behavior preserved)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Subagent refactor breaks existing functionality** | High | TDD approach (tests first), comprehensive test suite runs before merge, code review validation |
| **Merge conflicts between Track B components** | Medium | Components touch different files (API vs Frontend), regular rebasing against master |
| **Lost context during multi-hour execution** | Medium | This design doc serves as reference, each subagent task is self-contained with complete instructions |
| **Tests reveal bugs in existing code** | Low-Medium | Fix bugs as discovered (improvement allowed), document in commit messages |
| **Dependency injection refactor too complex** | Medium | Start with simple services, use facade pattern to maintain backward compatibility, incremental rollout |
| **Time estimate exceeded** | Low | Design is modular - can merge Track A independently, defer Track C if needed |

---

## Future Considerations

**Not in scope for this refactor:**

- Kubernetes deployment changes
- Database schema migrations (unless required for new columns)
- Frontend UX redesign (keep existing UI)
- Performance optimization beyond minor gains
- Adding new features

**Deferred to future work:**

- Full frontend component library migration (partial shadcn/ui usage is fine)
- Automated code review in CI/CD
- API versioning strategy
- Comprehensive load testing

---

## Appendix: File Changes Summary

**Track A Deletions:**
- 2 test files relocated (not deleted)
- ~50+ generated files removed from git tracking
- 8 plan documents deleted
- 1 duplicate settings file deleted

**Track B New Files:**
- `services/api/app/services/document_upload_service.py`
- `services/api/app/services/document_metadata_service.py`
- `services/api/app/services/chunking_orchestrator.py`
- `services/frontend/src/components/search/__tests__/EnhancedSearchBar.test.tsx`
- `services/frontend/src/components/upload/__tests__/UploadModal.test.tsx`
- `services/frontend/src/components/documents/__tests__/DocumentCard.test.tsx`
- `services/frontend/src/utils/__tests__/formatters.test.ts`

**Track B Modified Files:**
- `services/api/app/services/document_service.py` (refactored to facade)
- `services/api/app/core/dependencies.py` (added factories)
- `services/api/app/api/routes/*.py` (added Depends() injection)
- Multiple test files updated

**Track C Modified Files:**
- `services/api/app/core/exceptions.py` (new exception types)
- All service files (consistent error handling)
- All frontend components (Toast integration)
- Multiple files reformatted

**Total files impacted:** ~30-40 files across all tracks

---

## Approval & Next Steps

**Design Status:** ✅ Approved

**Next Steps:**
1. ✅ Write implementation plan (bite-sized tasks)
2. ✅ Create git worktree for isolated work
3. Execute Track A (immediate cleanup)
4. Execute Track B (parallel subagents with TDD)
5. Execute Track C (polish and consistency)
6. Verify all success criteria met
7. Merge to master

**Questions or concerns?** Discuss before implementation begins.
