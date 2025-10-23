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

export interface DocumentUploadResponse {
  id: string;
  title: string;
  description: string | null;
  file_name: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  upload_status: string;
  embedding_status: string;
  created_at: string;
}

export interface PaginatedDocuments {
  documents: Document[];
  total: number;
  page: number;
  limit: number;
}

export interface SearchResult {
  document_id: string;
  document_title: string;
  chunk_text: string;
  chunk_index: number;
  similarity_score: number;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  document_ids?: string[];
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
}

export interface ReadinessStatus {
  status: 'ready' | 'not_ready';
  services: {
    database: boolean;
    qdrant: boolean;
    embedder: boolean;
  };
}

// API error type
export interface ApiError {
  detail: string;
}
