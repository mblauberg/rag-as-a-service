import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import type { SearchRequest, SearchResponse } from '../types';

// Search mutation (not a query because it's a POST request with body)
export function useSearch() {
  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: (request: SearchRequest) => api.search(request),
  });
}
