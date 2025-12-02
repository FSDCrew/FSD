import type { ICrewApiService } from './interfaces/ICrewApiService';
import type { RequiredInputsResponse } from '@/lib/api/crew';
import { 
  getRequiredInputsCrewCrewIdRequiredInputsGet,
  crewKickoffCrewKickoffPost 
} from '@/lib/api/crew';

export class CrewApiService implements ICrewApiService {
  async getRequiredInputs(crewId: string): Promise<RequiredInputsResponse> {
    const response = await getRequiredInputsCrewCrewIdRequiredInputsGet({
      path: { crew_id: crewId }
    });

    if (!response.data) {
      throw new Error('Failed to fetch required inputs');
    }

    return response.data;
  }

  async kickoff(crewId: string, inputs: Record<string, any>): Promise<any> {
    const response = await crewKickoffCrewKickoffPost({
      body: {
        crew_id: crewId,
        inputs: inputs
      }
    });

    if (!response.data) {
      throw new Error('Failed to kickoff crew');
    }

    return response.data;
  }
}
