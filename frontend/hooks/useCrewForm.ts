import { useState, useCallback, useEffect } from "react";
import type { RequiredInputField } from "@/lib/api/crew";
import type { INotificationService } from "@/services/interfaces/INotificationService";
import { useRequiredInputs, useCrewKickoff } from "./useCrewApi";

export function useCrewForm(
  crewId: string | null,
  notificationService: INotificationService
) {
  const { data: requiredInputsData, isLoading: isLoadingRequiredInputs, error: requiredInputsError, refetch: fetchRequiredInputs } = useRequiredInputs(crewId);
  const kickoffMutation = useCrewKickoff();
  const [dynamicFormData, setDynamicFormData] = useState<Record<string, any>>({});

  const requiredInputs = requiredInputsData?.fields || [];

  // Initialize dynamicFormData when requiredInputs data is available
  useEffect(() => {
    if (requiredInputsData?.fields) {
      const initialData: Record<string, any> = {};
      requiredInputsData.fields.forEach((field: RequiredInputField) => {
        const typeInfo = field.type_info as any;
        if (typeInfo.is_list) {
          // For custom model lists, initialize with empty array
          // For enum lists, initialize with empty array
          // For primitive lists, initialize with empty array
          initialData[field.field_name] = [];
        } else if (typeInfo.is_custom_model && typeInfo.model_schema) {
          // Initialize custom model with empty object
          initialData[field.field_name] = {};
        } else if (typeInfo.type === "boolean" || typeInfo.type === "bool") {
          initialData[field.field_name] = false;
        } else if (typeInfo.type === "number" || typeInfo.type === "integer" || typeInfo.type === "int" || typeInfo.type === "float") {
          initialData[field.field_name] = "";
        } else {
          initialData[field.field_name] = "";
        }
      });
      setDynamicFormData(initialData);
    }
  }, [requiredInputsData]);

  // Handle error from required inputs query
  useEffect(() => {
    if (requiredInputsError) {
      console.error("Error fetching required inputs:", requiredInputsError);
      notificationService.error("Failed to fetch required inputs");
    }
  }, [requiredInputsError, notificationService]);

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

    if (kickoffMutation.isPending) {
      return;
    }

    if (!crewId) {
      notificationService.error("No crew ID found");
      return;
    }

    const missingFields = requiredInputs
      .filter(field => {
        if (!field.required) return false;
        const value = dynamicFormData[field.field_name];
        const typeInfo = field.type_info as any;

        // Check for empty arrays
        if (Array.isArray(value)) {
          return value.length === 0;
        }

        // Check for empty objects (custom models)
        if (typeInfo.is_custom_model && typeof value === "object" && value !== null) {
          return !Object.values(value).some((v: any) => {
            if (typeof v === "string") return v.trim() !== "";
            if (typeof v === "boolean") return true;
            return v !== null && v !== undefined;
          });
        }

        // Check for empty strings, null, undefined
        return !value || (typeof value === "string" && value.trim() === "");
      })
      .map(field => field.field_name);

    if (missingFields.length > 0) {
      notificationService.error(`Please fill in required fields: ${missingFields.join(", ")}`);
      return;
    }

    // Filter out empty list items for custom models
    const submitData: Record<string, any> = {};
    for (const [key, value] of Object.entries(dynamicFormData)) {
      if (Array.isArray(value)) {
        // Filter out empty objects/items from lists
        const filtered = value.filter((item) => {
          if (typeof item === "object" && item !== null) {
            // For objects, check if at least one property has a value
            return Object.values(item).some((v) => {
              if (typeof v === "string") return v.trim() !== "";
              if (typeof v === "boolean") return true;
              return v !== null && v !== undefined;
            });
          }
          // For primitives, check if not empty
          if (typeof item === "string") return item.trim() !== "";
          return item !== null && item !== undefined;
        });
        if (filtered.length > 0) {
          submitData[key] = filtered;
        }
      } else if (typeof value === "object" && value !== null) {
        // For single custom models, check if at least one property has a value
        const hasValue = Object.values(value).some((v) => {
          if (typeof v === "string") return v.trim() !== "";
          if (typeof v === "boolean") return true;
          return v !== null && v !== undefined;
        });
        if (hasValue) {
          submitData[key] = value;
        }
      } else {
        // For primitives, include if not empty
        if (value !== "" && value !== null && value !== undefined) {
          submitData[key] = value;
        }
      }
    }

    kickoffMutation.mutate(
      { crewId, inputs: submitData },
      {
        onSuccess: () => {
          notificationService.success("Crew run started successfully!");
          onSuccess();
        },
        onError: (error) => {
          console.error("Error starting crew run:", error);
          notificationService.error("Failed to start crew run. Please try again.");
        },
      }
    );
  }, [crewId, requiredInputs, dynamicFormData, kickoffMutation, notificationService]);

  return {
    requiredInputs,
    isLoadingRequiredInputs,
    dynamicFormData,
    fetchRequiredInputs,
    handleDynamicFormChange,
    onKickoffSubmit,
    isSubmitting: kickoffMutation.isPending,
  };
}
