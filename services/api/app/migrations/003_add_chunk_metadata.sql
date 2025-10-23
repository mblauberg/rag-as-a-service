-- Add metadata columns to document_chunks table for semantic chunking
ALTER TABLE document_chunks
ADD COLUMN section_title TEXT,
ADD COLUMN section_level INTEGER DEFAULT 0,
ADD COLUMN page_number INTEGER,
ADD COLUMN chunk_tokens INTEGER,
ADD COLUMN parent_chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
ADD COLUMN chunk_metadata JSONB DEFAULT '{}';

-- Add index for section queries
CREATE INDEX idx_chunks_section_title ON document_chunks(section_title);

-- Add index for parent relationship queries
CREATE INDEX idx_chunks_parent ON document_chunks(parent_chunk_id);

-- Add index for page number queries
CREATE INDEX idx_chunks_page_number ON document_chunks(page_number);

-- Add document type column to documents table
ALTER TABLE documents
ADD COLUMN document_type VARCHAR(50);
