-- Add file_path column to documents table
ALTER TABLE documents ADD COLUMN file_path VARCHAR(1000);

-- Update existing records with reconstructed path (will be NULL, that's ok)
-- New uploads will have the path stored
