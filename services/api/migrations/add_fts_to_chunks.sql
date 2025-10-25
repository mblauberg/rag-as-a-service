-- Add full-text search column to chunks table
-- Run this migration only if using PostgreSQL

-- Add text_search_vector column
ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS text_search_vector tsvector;

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_chunks_text_search
ON chunks USING GIN (text_search_vector);

-- Create trigger to auto-update text_search_vector
CREATE OR REPLACE FUNCTION chunks_text_search_trigger()
RETURNS trigger AS $$
BEGIN
  NEW.text_search_vector :=
    to_tsvector('english', COALESCE(NEW.content, ''));
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsvector_update_chunks ON chunks;
CREATE TRIGGER tsvector_update_chunks
BEFORE INSERT OR UPDATE ON chunks
FOR EACH ROW EXECUTE FUNCTION chunks_text_search_trigger();

-- Populate existing rows
UPDATE chunks
SET text_search_vector = to_tsvector('english', COALESCE(content, ''))
WHERE text_search_vector IS NULL;
