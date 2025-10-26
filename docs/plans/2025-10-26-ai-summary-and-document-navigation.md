# AI Summary Generation and Enhanced Document Navigation

**Date:** 2025-10-26
**Status:** Design Approved
**Features:** AI-generated search summaries, clickable citations, chunk-level document navigation

## Overview

This design adds two major UX enhancements to the RAAS search experience:

1. **AI Summary Generation**: Automatically generate AI summaries for search results using selected LLM models
2. **Enhanced Document Navigation**: Direct navigation from search results and summary citations to specific chunks within documents

## Requirements

### AI Summary Generation
- Generate AI summaries for search queries when a model is selected
- Add "None - No AI Summary" option to model selector
- Default to GPT-5-mini model
- Load search results instantly, show summary loading state separately
- Gracefully handle generation failures (show results without summary)
- Display summary at top of search results with model attribution

### Document Navigation
- Make search result chunks clickable to open document detail modal
- Highlight and scroll to clicked chunk in modal
- Make summary citations `[1]`, `[2]` clickable to navigate to source chunks
- Add explicit "View Document" affordance to document cards

## Architecture

### High-Level Design

Two independent features with clean separation:

```
Frontend:
  Search Flow:
    1. User types query → /api/v1/search → Results appear instantly
    2. If model selected → /api/v1/generate/summary → Summary appears when ready

  Navigation Flow:
    User clicks chunk or citation → DocumentDetailModal opens → Chunk highlighted & scrolled into view
```

### Backend API Design

#### New Summary Endpoint

```
POST /api/v1/generate/summary

Request:
{
  "query": "what is semantic search?",
  "chunk_ids": ["uuid1", "uuid2", ...],  // From search results
  "model": "gpt-5-mini"
}

Response:
{
  "summary": "Based on your documents, semantic search...",
  "model_used": "gpt-5-mini"
}

Error Responses:
- 503: Generator service unavailable
- 404: Invalid chunk IDs
- 400: Model not available (returns list of available models)
```

**Implementation Details:**
- New route file: `services/api/app/api/routes/generate.py`
- Reuses existing `GeneratorClient.generate_summary()` from `services/api/app/services/generator_client.py`
- Fetches chunk content by IDs from chunk repository
- Formats chunks for generator service
- Returns summary + model or appropriate error

**Why chunk_ids instead of passing chunk text?**
- Frontend doesn't need full chunk text in search response (smaller payload)
- Backend fetches fresh data (source of truth)
- Prevents tampering with chunk content
- Cleaner API contract

#### Error Handling Strategy

All errors handled gracefully:
- Generator service down → Return 503, frontend shows results without summary
- Invalid chunk IDs → Return 404 with detail
- Model not available → Return 400 with available models list
- Network timeout → Frontend shows error inline, doesn't break search results

### Frontend Implementation

#### Model Selector Enhancement

**Changes to `EnhancedSearchBar` component:**
- Add "None - No AI Summary" as first option in model dropdown
- Default selection: GPT-5-mini (on component mount)
- State: `selectedModel: string | null`
- `null` or "none" value = skip summary generation entirely

#### Summary Generation Hook

**New hook: `useSummaryGeneration`**

```typescript
function useSummaryGeneration(
  query: string,
  chunkIds: string[],
  model: string | null
) {
  // Only triggers if:
  // 1. model is not null/"none"
  // 2. chunkIds exist (search returned results)
  // 3. query is not empty

  return useQuery({
    queryKey: ['summary', query, chunkIds, model],
    queryFn: () => api.generateSummary({ query, chunk_ids: chunkIds, model }),
    enabled: !!model && model !== 'none' && chunkIds.length > 0 && !!query,
    retry: 1,  // Only retry once
    staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
  });
}
```

**UI States:**
1. **No model selected**: Summary section hidden entirely
2. **Loading**: Skeleton placeholder "Generating AI summary..."
3. **Success**: Renders `<SummaryDisplay>` component
4. **Error**: Inline error message, doesn't break search results display

#### Enhanced SummaryDisplay Component

**Updated interface:**
```typescript
interface SummaryDisplayProps {
  summary: string;
  modelUsed: string;
  searchResults: SearchResult[];  // NEW: Map citations to chunks
  onCitationClick: (docId: string, chunkId: string) => void;  // NEW: Click handler
}
```

**Citation Click Implementation:**
```typescript
// Parse [1], [2], etc.
const citationNum = parseInt(match[1]);
const result = searchResults[citationNum - 1];  // [1] → index 0

<button
  onClick={() => onCitationClick(result.document_id, result.chunk_id)}
  className="inline-flex items-center px-1.5 py-0.5 mx-0.5
             text-xs font-medium text-blue-700 bg-blue-100
             rounded hover:bg-blue-200 cursor-pointer transition-colors"
  aria-label={`View source ${citationNum}`}
>
  {match[0]}
</button>
```

#### Search Results Click Handling

**Updated `SearchResults` component:**
```typescript
interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  onChunkClick: (docId: string, chunkId: string) => void;  // NEW
}

// Render each result as clickable
<Card
  className="cursor-pointer hover:shadow-md transition-shadow"
  onClick={() => onChunkClick(result.document_id, result.chunk_id)}
>
  {/* Chunk preview */}
</Card>
```

#### Document Detail Modal Enhancement

**Updated interface:**
```typescript
interface DocumentDetailModalProps {
  documentId: string;
  highlightChunkId?: string;  // NEW: Optional chunk to highlight
  open: boolean;
  onClose: () => void;
}
```

**Chunk Highlighting Logic:**
1. Modal receives `highlightChunkId` prop
2. On mount/update with new highlightChunkId:
   ```typescript
   useEffect(() => {
     if (highlightChunkId) {
       const element = document.getElementById(`chunk-${highlightChunkId}`);
       if (element) {
         element.scrollIntoView({ behavior: 'smooth', block: 'center' });
         element.classList.add('bg-yellow-100', 'border-l-4', 'border-yellow-500');

         // Optional: Remove highlight after 3 seconds
         setTimeout(() => {
           element.classList.remove('bg-yellow-100', 'border-l-4', 'border-yellow-500');
         }, 3000);
       }
     }
   }, [highlightChunkId]);
   ```

3. Ensure each chunk has `id` attribute: `<div id={`chunk-${chunk.id}`}>`

#### MainPage Integration

**State management:**
```typescript
const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
const [highlightChunkId, setHighlightChunkId] = useState<string | null>(null);

const handleChunkClick = (docId: string, chunkId: string) => {
  setSelectedDocId(docId);
  setHighlightChunkId(chunkId);
};

const handleModalClose = () => {
  setSelectedDocId(null);
  setHighlightChunkId(null);  // Clear highlight on close
};
```

**Component wiring:**
```typescript
{/* Summary with clickable citations */}
{summary && (
  <SummaryDisplay
    summary={summary}
    modelUsed={modelUsed}
    searchResults={searchResults.data?.results || []}
    onCitationClick={handleChunkClick}
  />
)}

{/* Search results with clickable chunks */}
<SearchResults
  results={searchResults.data?.results || []}
  query={searchQuery}
  onChunkClick={handleChunkClick}
/>

{/* Modal with chunk highlighting */}
<DocumentDetailModal
  documentId={selectedDocId}
  highlightChunkId={highlightChunkId}
  open={!!selectedDocId}
  onClose={handleModalClose}
/>
```

## User Flows

### Flow 1: Search with AI Summary

1. User types "what is semantic search?"
2. Search results appear instantly (300ms)
3. Summary section shows loading skeleton
4. 2-5 seconds later, AI summary appears:
   ```
   Semantic search uses vector embeddings [1] to understand the meaning
   of queries [2] rather than just matching keywords [3].
   ```
5. User clicks `[1]` citation
6. Document modal opens, scrolls to chunk #1, highlights it
7. User reads full context

### Flow 2: Search Result Navigation

1. User searches "embeddings"
2. Results show 10 relevant chunks
3. User clicks on chunk #3
4. Document modal opens showing that document
5. Automatically scrolls to chunk #3 with yellow highlight
6. User can read surrounding chunks for context

### Flow 3: No Summary (Model = None)

1. User selects "None - No AI Summary" from model dropdown
2. User searches "transformers"
3. Results appear instantly
4. No summary section shown
5. Search is faster (no LLM call)

## Implementation Plan

### Backend Tasks

1. **Create Summary Endpoint**
   - File: `services/api/app/api/routes/generate.py`
   - Request/Response models in `app/api/models.py`
   - Use existing `GeneratorClient.generate_summary()`
   - Add route to main router

2. **Add Chunk Repository Method**
   - Method: `get_chunks_by_ids(chunk_ids: list[UUID]) -> list[Chunk]`
   - Needed to fetch chunk content for summary generation
   - Add to `ChunkRepository` interface and implementation

3. **Update API Models**
   - Add `GenerateSummaryRequest` model
   - Add `GenerateSummaryResponse` model

4. **Error Handling**
   - Wrap generator calls in try/except
   - Return appropriate HTTP status codes
   - Log errors for debugging

### Frontend Tasks

1. **Model Selector**
   - Add "None - No AI Summary" option
   - Set GPT-5-mini as default
   - Handle null model state

2. **Create useSummaryGeneration Hook**
   - New file: `services/frontend/src/hooks/useSummaryGeneration.ts`
   - Use React Query
   - Implement conditional fetching based on model selection

3. **Update SummaryDisplay Component**
   - Add `searchResults` prop
   - Add `onCitationClick` prop
   - Make citations clickable buttons
   - Add hover states and accessibility labels

4. **Update SearchResults Component**
   - Add `onChunkClick` prop
   - Make result cards clickable
   - Visual feedback on hover

5. **Update DocumentDetailModal**
   - Add `highlightChunkId` prop
   - Implement scroll-to-chunk logic
   - Add/remove highlight classes
   - Ensure chunks have unique `id` attributes

6. **Update MainPage**
   - Add `highlightChunkId` state
   - Wire up all click handlers
   - Integrate `useSummaryGeneration` hook
   - Handle loading/error states

7. **Update DocumentCard Component**
   - Add "View Document" button or icon
   - Improve visual affordance for clickability

### Testing Tasks

1. **Backend Tests**
   - Test summary endpoint with valid chunk IDs
   - Test with invalid chunk IDs (404)
   - Test with unavailable model (400)
   - Test generator service down (503)
   - Test empty results

2. **Frontend Tests**
   - Test model selector default to GPT-5-mini
   - Test "None" option hides summary
   - Test summary loading state
   - Test citation click navigation
   - Test search result click navigation
   - Test chunk highlighting in modal
   - Test error states (generator down)

3. **Integration Tests**
   - End-to-end: Search → Summary → Citation click → Chunk highlight
   - End-to-end: Search → Result click → Chunk highlight
   - Test with generator service unavailable

## Success Criteria

- ✅ Search results appear instantly (< 500ms), independent of summary generation
- ✅ AI summaries appear within 5 seconds for typical queries
- ✅ Summary generation failures don't break search experience
- ✅ Citations are visually distinct and obviously clickable
- ✅ Clicking citation or search result opens correct document at correct chunk
- ✅ Highlighted chunk is visible and centered in viewport
- ✅ "None" model option works and improves performance for users who don't want summaries

## Future Enhancements

- Streaming summary generation (SSE or WebSocket)
- "Regenerate summary" button
- Summary quality feedback (thumbs up/down)
- Save/bookmark summaries
- Summary history per search query
- Multiple model comparison (side-by-side summaries)
- Chunk preview on citation hover
