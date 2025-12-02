import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    getRequiredInputsCrewCrewIdRequiredInputsGet,
    crewKickoffCrewKickoffPost,
    type RequiredInputsResponse,
} from '@/lib/api/crew';

/**
 * Hook to fetch required inputs for a crew
 */
export function useRequiredInputs(crewId: string | null) {
    return useQuery<RequiredInputsResponse>({
        queryKey: ['crew', crewId, 'required-inputs'],
        queryFn: async () => {
            if (!crewId) {
                throw new Error('Crew ID is required');
            }
            const response = await getRequiredInputsCrewCrewIdRequiredInputsGet({
                path: { crew_id: crewId },
            });
            if (!response.data) {
                throw new Error('Failed to fetch required inputs');
            }
            return response.data;
        },
        enabled: !!crewId,
    });
}

/**
 * Hook to kickoff a crew run
 */
export function useCrewKickoff() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async ({ crewId, inputs }: { crewId: string; inputs: Record<string, any> }) => {
            const response = await crewKickoffCrewKickoffPost({
                body: {
                    crew_id: crewId,
                    inputs: inputs,
                },
            });
            if (!response.data) {
                throw new Error('Failed to kickoff crew');
            }
            return response.data;
        },
        onSuccess: (_, variables) => {
            // Invalidate the crew query to refresh crew runs
            queryClient.invalidateQueries({ queryKey: ['crew', variables.crewId] });
        },
    });
}

