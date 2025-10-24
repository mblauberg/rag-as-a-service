# Project Cleanup Design

**Date:** 2025-10-24
**Type:** Maintenance
**Status:** COMPLETED
**Executed:** Commit f53bc98 "chore: comprehensive project cleanup"

## Overview

Comprehensive cleanup of the RAAS project to remove outdated documentation, completed plan files, unused code, prunable git worktrees, and sample data. This cleanup streamlines the project while preserving active development work and useful documentation.

## Constraints

- **Active worktrees:** All mentioned worktrees have been handled (see Execution Summary below)
- **Merged worktrees:** `external-model-providers` and `kubernetes-scaffolding` were merged successfully
- **Core functionality:** All integration tests and utility scripts are actively used
- **Safety:** Git worktree removal will fail on uncommitted changes, protecting unmerged work

## Execution Summary

**Completed:** 2025-10-24 in commit f53bc98

**Actions Taken:**
- ✅ Removed 4 prunable/merged git worktrees successfully
- ✅ Removed outdated root-level documentation files
- ✅ Deleted completed plan documents (generation-component, multi-provider, external-model-providers)
- ✅ Removed unused frontend components (Input.tsx, badge.tsx, card.tsx, test/utils.tsx)
- ✅ Cleaned sample data from data/sample-docs/

**Current Worktree State (as of 2025-10-24):**
- `cleanup-and-refactoring` - Active, implementing additional cleanup and SOLID refactoring
- `critical-rag-optimizations` - Active, implementing RAG improvements (BGE-M3, BM25, RRF)

## Cleanup Categories

### 1. Worktree Cleanup

**To Remove:**
- `external-model-providers` - merged into master
- `complete-phase4-refactor` - marked prunable
- `comprehensive-quality-improvements` - marked prunable
- `generation-component` - marked prunable

**To Preserve:**
- `kubernetes-scaffolding` - active development

**Method:** Use `git worktree remove <name>` for safe removal

**Safety:** Git prevents removal of worktrees with uncommitted changes

### 2. Root Directory Files

**To Remove:**
- `INFRASTRUCTURE_IMPLEMENTATION_SUMMARY.md` - completion summary, info now in codebase
- `SEMANTIC_CHUNKING_IMPLEMENTATION_COMPLETE.md` - completion summary, no longer needed
- `migration_log.txt` - temporary migration log

**Rationale:** These were temporary documentation artifacts for completed work. The implementations are now in the codebase, making these summaries redundant.

### 3. Documentation Cleanup

**Completed Plans to Remove:**
- `docs/plans/2025-10-24-generation-component-design.md`
- `docs/plans/2025-10-24-generation-component-implementation.md`
- `docs/plans/2025-10-24-multi-provider-model-selector-design.md`
- `docs/plans/2025-10-24-multi-provider-model-selector.md`
- `docs/plans/2025-10-24-external-model-providers-backend-design.md`

**Plans to Preserve:**
- `docs/plans/2025-10-24-kubernetes-scaffolding-design.md` - active worktree
- `docs/plans/2025-10-24-rag-optimization-implementation.md` - contains future optimization work

**Other Docs to Preserve:**
- `docs/MULTI_PROVIDER_SETUP.md` - user setup guide
- `docs/RAG_OPTIMIZATION_ANALYSIS.md` - analysis document
- `docs/kubernetes.md`, `docs/demo_gcp.md` - deployment guides
- `docs/project_structure.md`, `docs/REFERENCES.md` - reference docs
- PDF files - course materials

**Rationale:** Remove plan documents for completed/merged features. Keep setup guides, analysis documents, and reference materials that provide ongoing value.

### 4. Sample Data

**To Remove:**
- `data/sample-docs/test.txt` - test sample document
- `data/sample-docs/` directory (if empty after removal)

**To Preserve:**
- `data/` directory structure - required for runtime file uploads

**Rationale:** Sample test data is not needed in repository. The `data/` directory is referenced in CLAUDE.md for runtime uploads.

### 5. Frontend Unused Components

**To Remove:**
- `services/frontend/src/components/common/Input.tsx` - unused (replaced by shadcn/ui)
- `services/frontend/src/components/ui/badge.tsx` - not imported
- `services/frontend/src/components/ui/card.tsx` - not imported
- `services/frontend/src/test/utils.tsx` - not imported by tests

**To Preserve:**
- All actively used components
- `services/frontend/src/test/setup.ts` - used by vitest.config.ts
- `services/frontend/src/utils/__tests__/modelUtils.test.ts` - actual test file

**Rationale:** Project transitioned from custom common components to shadcn/ui components, leaving unused files. Test utils were created but never utilized.

## Cleanup Process

The cleanup will be executed in a single operation:

1. **Remove worktrees** - `git worktree remove` for each prunable/merged worktree
2. **Remove root files** - delete summary and log files
3. **Remove completed plans** - delete merged feature plan documents
4. **Remove sample data** - clean up test files in data/
5. **Remove unused frontend files** - delete unused components and test utilities
6. **Stage git deletions** - stage all removed files that git is tracking
7. **Commit cleanup** - single commit documenting all removals

## Git Commit Message

```
chore: comprehensive project cleanup

Remove outdated documentation, completed plans, and unused code:
- Remove 4 prunable/merged git worktrees
- Remove root-level summary files (INFRASTRUCTURE_IMPLEMENTATION_SUMMARY.md, etc.)
- Remove completed plan documents for merged features
- Remove sample test data from data/sample-docs/
- Remove unused frontend components (common/Input, ui/badge, ui/card, test/utils)

Preserves:
- Active kubernetes-scaffolding worktree
- Active plan documents
- User-facing documentation (setup guides, references)
- All integration tests and utility scripts
```

## Files Affected

**Total removals:**
- 4 git worktrees
- 3 root-level files
- 5 plan documents
- 1+ sample data files
- 4 frontend component files

**No removals:**
- Integration tests (all actively test master branch features)
- `scripts/reembed_documents.py` (utility script)
- Active documentation and setup guides
- Test configuration files

## Success Criteria

- ✅ All prunable/merged worktrees removed
- ✅ Git history clean with single cleanup commit
- ✅ No breaking changes to build or test processes
- ✅ Project structure cleaner and easier to navigate
- ✅ Active development continues in new focused worktrees

## Follow-up Work

This cleanup was followed by a more comprehensive cleanup and SOLID refactoring effort tracked in:
- `docs/plans/2025-10-24-cleanup-and-refactoring-design.md` (design)
- `docs/plans/2025-10-24-cleanup-and-refactoring-implementation.md` (implementation plan)
- Branch: `feature/cleanup-and-refactoring`

The follow-up work includes:
- Additional file relocations and gitignore improvements
- SOLID principle refactoring (splitting document_service.py, fixing DI violations)
- Comprehensive frontend component tests
- Code formatting and error handling standardization
