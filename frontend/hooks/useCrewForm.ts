import { useState, useCallback } from "react";
import { toast } from "sonner";
import { getRequiredInputsCrewCrewIdRequiredInputsGet, crewKickoffCrewKickoffPost, type RequiredInputField } from "@/lib/api/crew";
import { getCrewByIdCrewCrewIdGet, type CrewRead } from "@/lib/api/crud";

export function useCrewForm(crewId: string | null) {
  const [requiredInputs, setRequiredInputs] = useState<RequiredInputField[]>([]);
  const [isLoadingRequiredInputs, setIsLoadingRequiredInputs] = useState(false);
  const [dynamicFormData, setDynamicFormData] = useState<Record<string, any>>({});
  const [orshotSchemaFields, setOrshotSchemaFields] = useState<Array<{field: string, dataType: string, description: string}>>([
    {field: "", dataType: "", description: ""}
  ]);

  const fetchRequiredInputs = useCallback(async () => {
    if (!crewId) {
      toast.error("No crew ID found");
      return;
    }
    
    setIsLoadingRequiredInputs(true);
    try {
      const response = await getRequiredInputsCrewCrewIdRequiredInputsGet({
        path: { crew_id: crewId }
      });
      
      if (response.data) {
        setRequiredInputs(response.data.fields);
        const initialData: Record<string, any> = {};
        response.data.fields.forEach(field => {
          if (field.type_info.is_list) {
            initialData[field.field_name] = [];
          } else {
            initialData[field.field_name] = "";
          }
        });
        setDynamicFormData(initialData);
      }
    } catch (error) {
      console.error("Error fetching required inputs:", error);
      toast.error("Failed to fetch required inputs");
    } finally {
      setIsLoadingRequiredInputs(false);
    }
  }, [crewId]);

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
      toast.error("No crew ID found");
      return;
    }
    
    const missingFields = requiredInputs
      .filter(field => field.required && !dynamicFormData[field.field_name])
      .map(field => field.field_name);
    
    if (missingFields.length > 0) {
      toast.error(`Please fill in required fields: ${missingFields.join(", ")}`);
      return;
    }
    
    const submitData = { ...dynamicFormData };
    if (orshotSchemaFields.some(f => f.field && f.dataType && f.description)) {
      submitData.orshot_schema = orshotSchemaFields.filter(f => f.field && f.dataType && f.description);
    }
    
    try {
      console.log("Kickoff form values:", submitData);
      
      const response = await crewKickoffCrewKickoffPost({
        body: {
          crew_id: crewId,
          inputs: submitData
        }
      });
      
      if (response.data) {
        toast.success("Crew run started successfully!");
        onSuccess();
      }
    } catch (error) {
      console.error("Error starting crew run:", error);
      toast.error("Failed to start crew run. Please try again.");
    }
  }, [crewId, requiredInputs, dynamicFormData, orshotSchemaFields]);

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
