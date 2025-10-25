# Frontend Refactor: Minimal Modern Design

**Date:** 2025-01-25
**Type:** Design Document
**Status:** Approved

## Overview

Comprehensive frontend refactoring to implement minimal, modern design following artifacts-builder best practices while avoiding "AI slop" aesthetics (excessive centering, purple gradients, uniform rounded corners).

## Goals

1. **Visual Design**: Create distinctive, professional design avoiding generic AI-generated aesthetics
2. **Component Architecture**: Full shadcn/ui integration for consistency and maintainability
3. **UX Improvements**: Document detail as overlay, floating action button for uploads
4. **Code Quality**: Maintain 98%+ test coverage, improve component reusability

## Constraints

- Preserve all existing functionality (search, upload, document management)
- Maintain current test coverage (98%+)
- Keep tech stack: React 18, TypeScript, Vite, Tailwind, React Query
- No breaking changes to API integration
- **Preserve search bar design** (user is happy with it)

## Implementation Strategy

**Approach:** Parallel subagent-driven development

Break work into 5 independent tasks executed concurrently by separate subagents:

1. **Design System Foundation** - Design tokens, color palette, typography
2. **Core Component Migration** - Basic shadcn/ui components
3. **Layout Pattern Refactoring** - Page layouts and navigation
4. **Advanced Component Updates** - Complex components (search, cards, modals)
5. **Testing & Integration** - Test updates, visual verification, E2E workflows

## Design System

### Color Palette

**Moving away from:** Generic primary-600 blues/purples

**New palette:**
- **Neutrals:** Slate grays (slate-50 to slate-900) as foundation
- **Accent:** Refined teal/emerald or warm amber (professional, distinctive)
- **Semantic:** Minimal red (errors), green (success)
- **No gradients** except subtle backgrounds where necessary

### Typography

**Avoiding:** Inter font (too common in AI-generated designs)

**Using:**
- System font stack OR distinctive font (Geist, DM Sans, or native system)
- Clear hierarchy: fewer sizes, more weight variation
- Increased line-height for readability
- Minimal font size variations

### Component Design Principles

1. **Reduced border radius:** 4px instead of 8px+ (less "bubbly")
2. **Subtle shadows:** Prefer borders over heavy drop shadows
3. **Generous whitespace:** Minimal ≠ cramped
4. **Flat design:** Subtle depth cues only where needed
5. **Less visual "chrome":** Cleaner, simpler interface

## Architecture Changes

### Routing Simplification

**Current:**
- Route: `/` → MainPage
- Route: `/documents/:id` → DocumentDetailPage

**New:**
- Route: `/` → MainPage (single route)
- Document details shown in overlay modal
- Simpler navigation, maintains context

### Component Structure

```
src/
  components/
    ui/                          # shadcn/ui components
      button.tsx
      card.tsx
      dialog.tsx
      select.tsx
      badge.tsx
      skeleton.tsx
      alert.tsx
      dropdown-menu.tsx
      input.tsx
      textarea.tsx
    common/                      # Shared components
      Button.tsx                 # Updated with shadcn styling
      Card.tsx                   # Replaced with shadcn card
      Modal.tsx                  # Updated Radix dialog styling
      Spinner.tsx                # Replaced with skeleton
    documents/
      DocumentCard.tsx           # Rebuilt with shadcn components
      DocumentDetailModal.tsx    # NEW: Full document view overlay
    search/
      EnhancedSearchBar.tsx      # Updated with shadcn select
      SearchResults.tsx          # Updated with new components
      SummaryDisplay.tsx         # Updated styling
    upload/
      UploadModal.tsx            # Updated styling
      UploadFAB.tsx              # NEW: Floating action button
  pages/
    MainPage.tsx                 # Single page, manages modals
  hooks/                         # No changes
  services/                      # No changes
  types/                         # No changes
```

## UX Improvements

### 1. Document Detail as Overlay

**Change:** Convert DocumentDetailPage → DocumentDetailModal

**Benefits:**
- Faster navigation (no route change)
- Maintains search context
- More app-like feel
- Smoother transitions

**Implementation:**
- Remove `/documents/:id` route
- Use shadcn/ui Dialog (large modal or full-screen)
- Click document card → opens overlay
- Close button/backdrop click → returns to main view

### 2. Floating Action Button for Upload

**Change:** Move upload button from sticky header to floating action button

**Design:**
- Position: `fixed bottom-8 right-8 z-50`
- Style: Circular button with plus icon
- Animation: Hover lift, smooth transitions
- Always accessible, doesn't clutter header

**Behavior:**
- Shows on main page when documents exist
- Hidden when upload modal is open
- Prominent CTA remains in empty state (when no documents)

### 3. Default Model Selection

**Change:** Auto-select GPT-5 Mini on page load

**Implementation:**
- When `useModels()` loads, set `selectedModel` to "gpt-5-mini"
- Fallback: If not available, select first model in list
- Improves UX: Users can search immediately

## Component Migration Details

### shadcn/ui Components to Add

| Component | Purpose | Replaces |
|-----------|---------|----------|
| button | Primary actions | Custom Button (partial) |
| card | Document cards, containers | Custom Card |
| select | Model dropdown | Custom dropdown |
| badge | Document metadata, tags | Custom badges |
| skeleton | Loading states | Custom spinners |
| alert | Error/success messages | Custom alerts |
| dropdown-menu | Menus | Existing Radix (formalize) |

### Component Mapping

1. **Button** (`components/common/Button.tsx`)
   - Update styling to match design system
   - Use shadcn/ui button variants

2. **Card** (`components/common/Card.tsx`)
   - Replace entirely with shadcn/ui card
   - Update all usage sites

3. **Modal** (`components/common/Modal.tsx`)
   - Keep Radix Dialog foundation
   - Update styling to match design system

4. **Input/Textarea** (`components/ui/`)
   - Update to match new design tokens
   - Reduced border radius, updated colors

5. **EnhancedSearchBar** (`components/search/EnhancedSearchBar.tsx`)
   - **PRESERVE CURRENT DESIGN** (user likes it)
   - Update model dropdown to use shadcn/ui select
   - Apply new design tokens for consistency

6. **DocumentCard** (`components/documents/DocumentCard.tsx`)
   - Rebuild with shadcn/ui card, badge
   - Add click handler for modal opening
   - Minimal, clean styling

7. **SearchResults** (`components/search/SearchResults.tsx`)
   - Update to use new card/badge components
   - Add click-to-modal behavior
   - Consistent styling

8. **UploadModal** (`components/upload/UploadModal.tsx`)
   - Update styling to match design system
   - Keep react-dropzone functionality
   - Cleaner, minimal appearance

### New Components

1. **DocumentDetailModal** (`components/documents/DocumentDetailModal.tsx`)
   - Full document view in overlay
   - Uses shadcn/ui Dialog
   - Close returns to previous view
   - Shows all document metadata, content

2. **UploadFAB** (`components/upload/UploadFAB.tsx`)
   - Floating action button component
   - Circular with plus icon
   - Opens UploadModal on click
   - Smooth animations

## State Management Updates

### MainPage State

```typescript
const [searchQuery, setSearchQuery] = useState('');
const [selectedModel, setSelectedModel] = useState<string | null>(null);
const [uploadOpen, setUploadOpen] = useState(false);
const [selectedDocId, setSelectedDocId] = useState<string | null>(null); // NEW

// Auto-select GPT-5 Mini when models load
useEffect(() => {
  if (models.data && !selectedModel) {
    const gpt5Mini = models.data.models.find(m => m.id === 'gpt-5-mini');
    setSelectedModel(gpt5Mini?.id || models.data.models[0]?.id || null);
  }
}, [models.data, selectedModel]);
```

### Navigation Updates

- Remove `useNavigate()` from React Router
- Document clicks set `selectedDocId` instead of navigating
- Modal closes by setting `selectedDocId` to null

## Testing Strategy

### Test Updates Required

Each task includes updating relevant tests:

1. **Design System Tests**
   - Verify design tokens applied correctly
   - Visual regression tests (optional)

2. **Component Tests**
   - Update for shadcn/ui components
   - Mock new component APIs
   - Verify click handlers for modals

3. **Integration Tests**
   - Document click → modal opens
   - Modal close → returns to grid
   - Search → results → click → modal
   - Upload FAB → modal opens

### Testing Approach (Per Task)

Each subagent:
1. Update relevant test files after changes
2. Run `npm test` to verify tests pass
3. Ensure coverage stays at 98%+
4. Commit working code with passing tests

### Final Integration Testing

After all parallel tasks complete:

1. **Full test suite:** `npm test`
2. **Type checking:** `npm run type-check`
3. **Visual verification:** Use webapp-testing skill (Playwright)
4. **Manual workflow testing:**
   - Upload document → verify appears in grid
   - Click document → verify modal opens with correct data
   - Search documents → verify results appear
   - Click search result → verify modal opens
   - Close modal → verify returns to correct view (grid or search results)
   - FAB click → verify upload modal opens

### Quality Gates

- [ ] All tests pass
- [ ] No TypeScript errors
- [ ] 98%+ test coverage maintained
- [ ] Visual consistency verified
- [ ] All original features working
- [ ] No console errors/warnings

## Design Tokens (tailwind.config.js)

### Colors

```javascript
colors: {
  slate: colors.slate, // Primary neutrals
  accent: {
    50: '#...', // Teal/emerald or amber
    // ... full scale
    950: '#...',
  },
  // Semantic colors
  success: colors.green,
  error: colors.red,
}
```

### Border Radius

```javascript
borderRadius: {
  sm: '2px',
  DEFAULT: '4px',
  md: '4px',
  lg: '6px',
  xl: '8px',
}
```

### Shadows

```javascript
boxShadow: {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  // Reduced shadow usage overall
}
```

### Typography

```javascript
fontFamily: {
  sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
}
```

## Animation & Polish

Using framer-motion:

1. **Modal animations:**
   - Overlay: Fade in (0.2s)
   - Content: Slide up + fade (0.3s, ease-out)

2. **FAB animations:**
   - Hover: Scale(1.05) + lift shadow
   - Click: Scale(0.95) ripple effect

3. **Card animations:**
   - Hover: Subtle lift (translate-y: -2px)
   - Click: Quick scale feedback

4. **Page transitions:**
   - Keep minimal, smooth
   - Stagger children animations for lists

## Task Breakdown

### Task 1: Design System Foundation

**Owner:** Subagent 1

**Scope:**
- Update `tailwind.config.js` with new design tokens
- Create design documentation
- Update global styles if needed

**Files:**
- `tailwind.config.js`
- `src/index.css` (if needed)

**Tests:**
- Visual verification of color/spacing changes

**Commit:** "feat(design): implement minimal design system with new color palette"

### Task 2: Core Component Migration

**Owner:** Subagent 2

**Scope:**
- Add shadcn/ui components: button, card, select, badge, skeleton, alert
- Update `components/ui/` files
- Update `components/common/` to use new components

**Files:**
- `src/components/ui/button.tsx` (update)
- `src/components/ui/card.tsx` (new)
- `src/components/ui/select.tsx` (new)
- `src/components/ui/badge.tsx` (new)
- `src/components/ui/skeleton.tsx` (new)
- `src/components/ui/alert.tsx` (new)
- `src/components/common/Button.tsx` (update)
- `src/components/common/Card.tsx` (update)
- `src/components/common/Modal.tsx` (update)

**Tests:**
- Update Button tests
- Add component tests for new shadcn components

**Commit:** "feat(components): migrate to shadcn/ui core components"

### Task 3: Layout Pattern Refactoring

**Owner:** Subagent 3

**Scope:**
- Remove `/documents/:id` route
- Add document modal state to MainPage
- Create UploadFAB component
- Update MainPage layout

**Files:**
- `src/App.tsx` (remove route)
- `src/pages/MainPage.tsx` (add modal state, FAB)
- `src/components/upload/UploadFAB.tsx` (new)

**Tests:**
- Update MainPage tests for new state
- Add UploadFAB tests

**Commit:** "feat(layout): simplify routing and add floating upload button"

### Task 4: Advanced Component Updates

**Owner:** Subagent 4

**Scope:**
- Create DocumentDetailModal
- Update DocumentCard with click-to-modal
- Update SearchResults with click-to-modal
- Update EnhancedSearchBar (minimal - just use shadcn select)
- Update UploadModal styling
- Implement default model selection (GPT-5 Mini)

**Files:**
- `src/components/documents/DocumentDetailModal.tsx` (new)
- `src/components/documents/DocumentCard.tsx` (update)
- `src/components/search/SearchResults.tsx` (update)
- `src/components/search/EnhancedSearchBar.tsx` (update select only)
- `src/components/upload/UploadModal.tsx` (update styling)
- `src/pages/MainPage.tsx` (default model logic)

**Tests:**
- Add DocumentDetailModal tests
- Update DocumentCard tests
- Update SearchResults tests
- Update EnhancedSearchBar tests

**Commit:** "feat(components): add document detail modal and update complex components"

### Task 5: Testing & Integration

**Owner:** Subagent 5

**Scope:**
- Run full test suite
- Fix any test failures from other tasks
- Visual verification with Playwright
- E2E workflow testing
- Type checking
- Integration verification

**Files:**
- All test files (fixes as needed)
- Integration test updates

**Tests:**
- Full test suite passes
- Coverage at 98%+
- Visual tests pass
- E2E workflows verified

**Commit:** "test: update tests for refactored components and verify integration"

## Rollout Plan

1. **Create worktree:** `feature/frontend-minimal-design`
2. **Launch 5 subagents** in parallel with task assignments
3. **Each subagent:**
   - Implements assigned task
   - Updates tests
   - Commits working code
4. **Integration phase:**
   - Task 5 subagent verifies integration
   - Fixes conflicts/issues
   - Final commit
5. **Review & merge:**
   - Code review
   - Final visual verification
   - Merge to master

## Success Criteria

- [ ] All original functionality preserved
- [ ] Design avoids "AI slop" aesthetics (no centered overload, generic colors, excessive rounding)
- [ ] Search bar design preserved (user requirement)
- [ ] Document detail shown as overlay (not separate page)
- [ ] Upload button is floating action button (bottom-right)
- [ ] GPT-5 Mini selected by default
- [ ] All tests pass with 98%+ coverage
- [ ] No TypeScript errors
- [ ] Visual consistency across all components
- [ ] Smooth animations and transitions
- [ ] Clean, minimal, professional appearance

## Future Enhancements (Out of Scope)

- Deep linking with URL query params for modals
- Keyboard shortcuts (ESC to close modal, etc.)
- Dark mode support
- Advanced animation choreography
- Performance optimizations (code splitting, lazy loading)
