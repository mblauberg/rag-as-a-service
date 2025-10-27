import { useQuery } from '@tanstack/react-query';
import { useDebounce } from './useDebounce';
import { api } from '../services/api';

/** Search with automatic debouncing (300ms). Only triggers when query length > 0. */
export function useSearchWithDebounce(
  query: string,
  model?: string | null,
  limit: number = 20
) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ['search', debouncedQuery, model, limit],
    queryFn: () => api.search({
      query: debouncedQuery,
      limit,
      model: model || undefined
    }),
    enabled: debouncedQuery.length > 0,
    staleTime: 10000, // Results fresh for 10 seconds
  });
}
