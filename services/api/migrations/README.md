# Database Migrations

## Full-Text Search (FTS) Setup

**Required for:** Hybrid search with BM25 keyword matching

**Database:** PostgreSQL only (SQLite uses fallback LIKE search)

### Apply Migration

```bash
psql $DATABASE_URL < migrations/add_fts_to_chunks.sql
```

### Verify

```sql
-- Check column exists
\d chunks

-- Check index exists
\di idx_chunks_text_search

-- Test FTS
SELECT id, content
FROM chunks
WHERE text_search_vector @@ plainto_tsquery('english', 'kubernetes')
LIMIT 5;
```
