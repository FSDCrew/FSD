import { useQuery } from '@tanstack/react-query';
import { getCrewByIdCrewCrewIdGet, type CrewRead } from '@/lib/api/crud';

/**
 * Hook to fetch a crew by ID
 */
export function useCrewById(crewId: string | null) {
  return useQuery<CrewRead>({
    queryKey: ['crew', crewId],
    queryFn: async () => {
      if (!crewId) {
        throw new Error('Crew ID is required');
      }
      const response = await getCrewByIdCrewCrewIdGet({
        path: { crew_id: crewId },
      });
      if (!response.data) {
        throw new Error('Failed to fetch crew');
      }
      return response.data;
    },
    enabled: !!crewId,
  });
}

