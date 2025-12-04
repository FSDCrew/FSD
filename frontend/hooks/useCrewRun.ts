import { useQuery } from "@tanstack/react-query";
import { getCrewRunCrewRunCrewRunIdGet } from "@/lib/api/crud";

interface UseCrewRunOptions {
  refetchInterval?: number | false;
  enabled?: boolean;
}

const TERMINAL_QUEUE_STATUSES = [
  "COMPLETED",
  "FAILED",
  "CANCELLED"
];

export function useCrewRun(crewRunId: string | null, options?: UseCrewRunOptions) {
  return useQuery({
    queryKey: ["crew-run", crewRunId],
    queryFn: async () => {
      if (!crewRunId) {
        throw new Error("Crew run ID is required");
      }
      const response = await getCrewRunCrewRunCrewRunIdGet({
        path: { crew_run_id: crewRunId },
      });

      // console.log("=== API Response ===");
      // console.log("Full response:", response);
      // console.log("Response data:", response.data);
      // console.log("Task states:", response.data?.output?.task_states);
      // console.log("===================");

      return response.data;
    },
    enabled: !!crewRunId && (options?.enabled ?? true),
    refetchInterval: (query) => {
      const data = query.state.data as any;
      const queueStatus = data?.queue_status;
      
      // Stop polling if queue status is terminal
      if (queueStatus && TERMINAL_QUEUE_STATUSES.includes(queueStatus)) {
        console.log(`Terminal queue status reached: ${queueStatus}. Stopping polling.`);
        return false;
      }
      
      // Otherwise, use the provided interval or default to false
      return options?.refetchInterval ?? false;
    },
    refetchIntervalInBackground: false,
  });
}