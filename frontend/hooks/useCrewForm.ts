import { useState, useCallback, useEffect } from "react";
import type { RequiredInputField } from "@/lib/api/crew";
import type { INotificationService } from "@/services/interfaces/INotificationService";
import { useRequiredInputs, useCrewKickoff } from "./useCrewApi";

// Helper function to check if a field is nullable
function checkIfFieldIsNullable(field: RequiredInputField, typeInfo: any): boolean {
  // Check if type_info itself indicates nullable (e.g., has anyOf)
  if (typeInfo.anyOf) {
    return typeInfo.anyOf.some((s: any) => s.type === "null");
  }
  // Check if it's a custom model with nullable properties at the top level
  if (typeInfo.model_schema?.properties) {
    const properties = typeInfo.model_schema.properties;
    // Check if any property is nullable
    return Object.values(properties).some((propSchema: any) =>
      propSchema.anyOf?.some((s: any) => s.type === "null")
    );
  }
  return false;
}

export function useCrewForm(
  crewId: string | null,
  notificationService: INotificationService,
  enabled: boolean = false
) {
  const { data: requiredInputsData, isLoading: isLoadingRequiredInputs, error: requiredInputsError, refetch: fetchRequiredInputs } = useRequiredInputs(crewId, enabled);
  const kickoffMutation = useCrewKickoff();
  const [dynamicFormData, setDynamicFormData] = useState<Record<string, any>>({});

  const getCacheKey = () => crewId ? `kickoff_form_${crewId}` : null;

  const requiredInputs = requiredInputsData?.fields || [];

  // Initialize dynamicFormData when requiredInputs data is available
  useEffect(() => {
    if (requiredInputsData?.fields) {
      const cacheKey = getCacheKey();
      let initialData: Record<string, any> = {};

      // Try to restore from localStorage first
      if (cacheKey) {
        try {
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            initialData = JSON.parse(cached);
            setDynamicFormData(initialData);
            return;
          }
        } catch (error) {
          console.error("Failed to restore cached form data:", error);
        }
      }

      // Initialize with default values if no cache
      requiredInputsData.fields.forEach((field: RequiredInputField) => {
        const typeInfo = field.type_info as any;

        // Check if field is nullable
        const isNullable = checkIfFieldIsNullable(field, typeInfo);

        if (isNullable) {
          initialData[field.field_name] = null;
        } else if (typeInfo.is_list) {
          initialData[field.field_name] = [];
        } else if (typeInfo.is_custom_model && typeInfo.model_schema) {
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

  // Save form data to localStorage whenever it changes
  useEffect(() => {
    const cacheKey = getCacheKey();
    if (cacheKey && Object.keys(dynamicFormData).length > 0) {
      try {
        localStorage.setItem(cacheKey, JSON.stringify(dynamicFormData));
      } catch (error) {
        console.error("Failed to cache form data:", error);
      }
    }
  }, [dynamicFormData, crewId]);

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
          // Clear localStorage cache on successful submission
          const cacheKey = getCacheKey();
          if (cacheKey) {
            localStorage.removeItem(cacheKey);
          }
          onSuccess();
        },
        onError: (error) => {
          console.error("Error starting crew run:", error);
          notificationService.error("Failed to start crew run. Please try again.");
        },
      }
    );
  }, [crewId, requiredInputs, dynamicFormData, kickoffMutation, notificationService]);

  const resetForm = useCallback(() => {
    if (requiredInputsData?.fields) {
      const initialData: Record<string, any> = {};
      requiredInputsData.fields.forEach((field: RequiredInputField) => {
        const typeInfo = field.type_info as any;

        // Check if field is nullable
        const isNullable = checkIfFieldIsNullable(field, typeInfo);

        if (isNullable) {
          initialData[field.field_name] = null;
        } else if (typeInfo.is_list) {
          initialData[field.field_name] = [];
        } else if (typeInfo.is_custom_model && typeInfo.model_schema) {
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

      // Clear localStorage cache
      const cacheKey = getCacheKey();
      if (cacheKey) {
        localStorage.removeItem(cacheKey);
      }

      notificationService.success("Form reset successfully");
    }
  }, [requiredInputsData, notificationService, crewId]);

  const invalidateRequiredInputs = useCallback(() => {
    // Clear form data and cache
    setDynamicFormData({});
    const cacheKey = getCacheKey();
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
    }
    // Refetch required inputs
    fetchRequiredInputs();
  }, [fetchRequiredInputs, crewId]);

  return {
    requiredInputs,
    isLoadingRequiredInputs,
    dynamicFormData,
    fetchRequiredInputs,
    handleDynamicFormChange,
    onKickoffSubmit,
    resetForm,
    invalidateRequiredInputs,
    isSubmitting: kickoffMutation.isPending,
  };
}
