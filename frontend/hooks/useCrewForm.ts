import { useState, useCallback } from "react";
import type { RequiredInputField } from "@/lib/api/crew";
import type { CrewRead } from "@/lib/api/crud";
import type { ICrewApiService } from "@/services/interfaces/ICrewApiService";
import type { INotificationService } from "@/services/interfaces/INotificationService";
import { getCrewByIdCrewCrewIdGet } from "@/lib/api/crud";

export function useCrewForm(
  crewId: string | null,
  crewApiService: ICrewApiService,
  notificationService: INotificationService
) {
  const [requiredInputs, setRequiredInputs] = useState<RequiredInputField[]>([]);
  const [isLoadingRequiredInputs, setIsLoadingRequiredInputs] = useState(false);
  const [dynamicFormData, setDynamicFormData] = useState<Record<string, any>>({});
  const [orshotSchemaFields, setOrshotSchemaFields] = useState<Array<{field: string, dataType: string, description: string}>>([
    {field: "", dataType: "", description: ""}
  ]);

  const fetchRequiredInputs = useCallback(async () => {
    if (!crewId) {
      notificationService.error("No crew ID found");
      return;
    }
    
    setIsLoadingRequiredInputs(true);
    try {
      const response = await crewApiService.getRequiredInputs(crewId);
      
      setRequiredInputs(response.fields);
      const initialData: Record<string, any> = {};
      response.fields.forEach((field: RequiredInputField) => {
        if (field.type_info.is_list) {
          initialData[field.field_name] = [];
        } else {
          initialData[field.field_name] = "";
        }
      });
      setDynamicFormData(initialData);
    } catch (error) {
      console.error("Error fetching required inputs:", error);
      notificationService.error("Failed to fetch required inputs");
    } finally {
      setIsLoadingRequiredInputs(false);
    }
  }, [crewId, crewApiService, notificationService]);

  const handleDynamicFormChange = useCallback((fieldName: string, value: any) => {
    setDynamicFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  }, []);

  const onKickoffSubmit = useCallback(async (
    e: React.FormEvent,
    onSuccess: () => void
  ) => {
    e.preventDefault();
    
    if (!crewId) {
      notificationService.error("No crew ID found");
      return;
    }
    
    const missingFields = requiredInputs
      .filter(field => field.required && !dynamicFormData[field.field_name])
      .map(field => field.field_name);
    
    if (missingFields.length > 0) {
      notificationService.error(`Please fill in required fields: ${missingFields.join(", ")}`);
      return;
    }
    
    const submitData = { ...dynamicFormData };
    if (orshotSchemaFields.some(f => f.field && f.dataType && f.description)) {
      submitData.orshot_schema = orshotSchemaFields.filter(f => f.field && f.dataType && f.description);
    }
    
    try {
      console.log("Kickoff form values:", submitData);
      
      const response = await crewApiService.kickoff(crewId, submitData);
      
      notificationService.success("Crew run started successfully!");
      onSuccess();
    } catch (error) {
      console.error("Error starting crew run:", error);
      notificationService.error("Failed to start crew run. Please try again.");
    }
  }, [crewId, requiredInputs, dynamicFormData, orshotSchemaFields, crewApiService, notificationService]);

  return {
    requiredInputs,
    isLoadingRequiredInputs,
    dynamicFormData,
    orshotSchemaFields,
    setOrshotSchemaFields,
    fetchRequiredInputs,
    handleDynamicFormChange,
    onKickoffSubmit,
  };
}
