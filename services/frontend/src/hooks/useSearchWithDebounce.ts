import { useQuery } from '@tanstack/react-query';
import { useDebounce } from './useDebounce';
import { api } from '../services/api';

/**
 * Search with automatic debouncing (300ms).
 * Only triggers search when query length > 0.
 *
 * @param query - Search query string
 * @param limit - Maximum number of results (default 20)
 * @returns React Query result with search data
 */
export function useSearchWithDebounce(query: string, limit: number = 20) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ['search', debouncedQuery, limit],
    queryFn: () => api.search({ query: debouncedQuery, limit }),
    enabled: debouncedQuery.length > 0,
    staleTime: 10000, // Results fresh for 10 seconds
  });
}
