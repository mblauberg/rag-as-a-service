import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { DocumentUploadResponse } from '../types';

// Query keys
export const documentKeys = {
  all: ['documents'] as const,
  lists: () => [...documentKeys.all, 'list'] as const,
  list: (page: number, limit: number) => [...documentKeys.lists(), { page, limit }] as const,
  details: () => [...documentKeys.all, 'detail'] as const,
  detail: (id: string) => [...documentKeys.details(), id] as const,
};

// List documents with pagination
export function useDocuments(page: number = 1, limit: number = 20) {
  return useQuery({
    queryKey: documentKeys.list(page, limit),
    queryFn: () => api.listDocuments(page, limit),
    staleTime: 5000, // Consider data fresh for 5 seconds
  });
}

// Get single document with chunks
export function useDocument(documentId: string) {
  return useQuery({
    queryKey: documentKeys.detail(documentId),
    queryFn: () => api.getDocument(documentId),
    enabled: !!documentId,
  });
}

// Upload document mutation
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      title,
      description,
    }: {
      file: File;
      title: string;
      description?: string;
    }) => api.uploadDocument(file, title, description),
    onSuccess: (data: DocumentUploadResponse) => {
      // Invalidate documents list to refetch
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
      // Set the new document in the cache
      queryClient.setQueryData(documentKeys.detail(data.id), data);
    },
  });
}

// Delete document mutation
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => api.deleteDocument(documentId),
    onSuccess: (_, documentId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: documentKeys.detail(documentId) });
      // Invalidate list to refetch
      queryClient.invalidateQueries({ queryKey: documentKeys.lists() });
    },
  });
}
