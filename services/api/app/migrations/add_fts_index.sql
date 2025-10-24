-- Add full-text search support for BM25-like ranking
-- This enables hybrid search (vector + lexical)

-- Add tsvector column for full-text search
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS text_search_vector tsvector
GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED;

-- Create GIN index for fast lexical search
CREATE INDEX IF NOT EXISTS idx_text_search
ON document_chunks
USING GIN (text_search_vector);

-- Add comment for documentation
COMMENT ON COLUMN document_chunks.text_search_vector IS 'Full-text search vector for BM25-like ranking in hybrid search';
COMMENT ON INDEX idx_text_search IS 'GIN index for fast lexical/keyword search';
