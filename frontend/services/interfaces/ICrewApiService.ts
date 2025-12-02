import type { RequiredInputsResponse } from '@/lib/api/crew';

export interface ICrewApiService {
  /**
   * Fetches the required inputs for a crew
   * @param crewId - The ID of the crew
   * @returns Promise resolving to the required inputs response
   */
  getRequiredInputs(crewId: string): Promise<RequiredInputsResponse>;

  /**
   * Submits a crew kickoff request
   * @param crewId - The ID of the crew
   * @param inputs - The input data for the kickoff
   * @returns Promise resolving to the kickoff response
   */
  kickoff(crewId: string, inputs: Record<string, any>): Promise<any>;
}
