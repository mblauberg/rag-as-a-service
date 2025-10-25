import axios, { AxiosInstance } from 'axios';
import type {
  DocumentDetail,
  DocumentUploadResponse,
  PaginatedDocuments,
  SearchRequest,
  SearchResponse,
  HealthStatus,
  ReadinessStatus,
  ModelsResponse,
} from '../types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 seconds
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Server responded with error status
          const message = error.response.data?.detail || error.message;
          console.error('API Error:', message);
          throw new Error(message);
        } else if (error.request) {
          // Request made but no response
          console.error('Network Error:', error.message);
          throw new Error('Network error: Unable to reach the server');
        } else {
          // Something else happened
          console.error('Error:', error.message);
          throw error;
        }
      }
    );
  }

  // Health endpoints
  async checkHealth(): Promise<HealthStatus> {
    const response = await this.client.get<HealthStatus>('/api/v1/health');
    return response.data;
  }

  async checkReadiness(): Promise<ReadinessStatus> {
    const response = await this.client.get<ReadinessStatus>('/api/v1/ready');
    return response.data;
  }

  // Document endpoints
  async uploadDocument(
    file: File,
    title: string,
    description?: string
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) {
      formData.append('description', description);
    }

    const response = await this.client.post<DocumentUploadResponse>(
      '/api/v1/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  async listDocuments(page: number = 1, limit: number = 20): Promise<PaginatedDocuments> {
    const response = await this.client.get<PaginatedDocuments>('/api/v1/documents', {
      params: { page, limit },
    });
    return response.data;
  }

  async getDocument(documentId: string): Promise<DocumentDetail> {
    const response = await this.client.get<DocumentDetail>(`/api/v1/documents/${documentId}`);
    return response.data;
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.client.delete(`/api/v1/documents/${documentId}`);
  }

  // Search endpoints
  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await this.client.post<SearchResponse>('/api/v1/search', request);
    return response.data;
  }

  // Models endpoints
  async listModels(): Promise<ModelsResponse> {
    const response = await this.client.get<ModelsResponse>('/api/v1/models');
    return response.data;
  }
}

// Export a singleton instance
export const api = new ApiClient();
