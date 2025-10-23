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
  document_title: string;
  chunk_text: string;
  chunk_index: number;
  score: number;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  document_ids?: string[];
  model?: string;  // NEW: Optional model for generation
}

export interface SearchResponse {
  query: string;
  summary: string | null;  // NEW: Generated summary
  chunks: SearchResult[];
  model_used: string | null;  // NEW: Model that generated summary
  total_results: number;
}

export interface Model {
  name: string;
  size: string;
  modified_at: string;
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
