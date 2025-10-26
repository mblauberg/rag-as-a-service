// Document types matching backend schemas

export interface Document {
  id: string;
  title: string;
  description: string | null;
  file_name: string;
  file_type: string;
  file_size: number;
  upload_status: 'pending' | 'processing' | 'completed' | 'failed';
  embedding_status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  chunk_text: string;
  token_count: number | null;
  section_title?: string;
  section_level?: number;
  page_number?: number;
  chunk_tokens?: number;
  chunk_metadata?: Record<string, any>;
  created_at: string;
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[];
}

export interface DocumentUploadResponse extends Document {
  message: string;
  chunk_count: number;
}

export interface PaginatedDocuments {
  documents: Document[];
  total: number;
  page: number;
  limit: number;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  content: string;  // Changed from chunk_text to match API
  score: number;
  tokens: number | null;
  // Optional fields that may be added later
  document_title?: string;
  chunk_index?: number;
  section_title?: string;
  page_number?: number;
  chunk_metadata?: Record<string, any>;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  document_ids?: string[];
  model?: string;  // NEW: Optional model for generation
}

export interface SearchResponse {
  query: string;
  summary?: string | null;  // NEW: Generated summary (optional)
  results: SearchResult[];  // Changed from 'chunks' to match API
  model_used?: string | null;  // NEW: Model that generated summary (optional)
  total_results: number;
}

export interface Model {
  name: string;              // Unique identifier (e.g., "llama3.3:70b", "openai:gpt-5")
  display_name: string;      // Human-readable name (e.g., "Llama 3.3 70B")
  provider: string;          // "ollama", "openai", "anthropic", "google"
  size: string;              // "8B", "70B", "N/A"
  description: string;       // Capability description
  capabilities: string[];    // ["reasoning", "coding"]
  modified_at: string;       // ISO timestamp
}

export interface ModelsResponse {
  models: Model[];
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
}

export interface ServiceStatus {
  name: string;
  status: string;
  details?: string;
}

export interface ReadinessStatus {
  status: string;
  services: ServiceStatus[];
}

// API error type
export interface ApiError {
  detail: string;
}
