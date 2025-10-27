import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

/** Hook to fetch and cache available models. */
export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const response = await api.listModels();
      return response.models;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1
  });
}
