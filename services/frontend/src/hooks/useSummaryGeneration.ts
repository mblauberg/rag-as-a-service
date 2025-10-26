import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface GenerateSummaryRequest {
  query: string;
  chunk_ids: string[];
  model: string;
}

interface GenerateSummaryResponse {
  summary: string;
  model_used: string;
}

export function useSummaryGeneration(
  query: string,
  chunkIds: string[],
  model: string | null
) {
  const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  return useQuery<GenerateSummaryResponse>({
    queryKey: ['summary', query, chunkIds, model],
    queryFn: async () => {
      const response = await axios.post<GenerateSummaryResponse>(
        `${baseURL}/api/v1/generate/summary`,
        {
          query,
          chunk_ids: chunkIds,
          model: model!,
        } as GenerateSummaryRequest
      );
      return response.data;
    },
    enabled: !!model && model !== 'none' && chunkIds.length > 0 && !!query,
    retry: 1,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}
