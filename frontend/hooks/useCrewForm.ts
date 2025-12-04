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
    onSuccess: (runId?: string) => void
  ) => {
    e.preventDefault();

    if (kickoffMutation.isPending) {
      return;
    }

    if (!crewId) {
      notificationService.error("No crew ID found");
      return;
    }

    const missingFields: string[] = [];

    console.log('=== VALIDATION DEBUG ===');
    console.log('Required inputs:', requiredInputs);
    console.log('Form data:', dynamicFormData);

    requiredInputs.forEach(field => {
      const value = dynamicFormData[field.field_name];
      const typeInfo = field.type_info as any;
      
      console.log(`Checking field: ${field.field_name}`, { value, typeInfo, required: field.required });
      
      // If field is not required but is a custom model, check if it's null or empty
      if (!field.required) {
        // For custom models, if value is null, it means it hasn't been filled
        // Check if this will cause backend errors by looking at nested required fields
        if (typeInfo.is_custom_model) {
          const modelSchema = typeInfo.model_schema;
          // If the custom model has required nested fields and the value is null or empty, flag it
          if (modelSchema?.required && Array.isArray(modelSchema.required) && modelSchema.required.length > 0) {
            if (value === null || value === undefined) {
              missingFields.push(field.field_name);
              return;
            }
          }
        }
        
        // For optional custom models, if they have any value, validate nested required fields
        if (typeInfo.is_custom_model && typeof value === "object" && value !== null) {
          const modelSchema = typeInfo.model_schema;
          console.log(`Optional custom model ${field.field_name} has value, checking nested required fields:`, { value, modelSchema });
          
          if (modelSchema?.required && Array.isArray(modelSchema.required)) {
            modelSchema.required.forEach((propName: string) => {
              const propValue = value[propName];
              const propSchema = modelSchema.properties?.[propName];
              
              // Check if nested field is empty
              if (propValue === null || propValue === undefined || propValue === "") {
                missingFields.push(`${field.field_name}.${propName}`);
                return;
              }
              
              // Check for empty strings
              if (typeof propValue === "string" && propValue.trim() === "") {
                missingFields.push(`${field.field_name}.${propName}`);
                return;
              }
              
              // Check for empty arrays
              if (Array.isArray(propValue) && propValue.length === 0) {
                missingFields.push(`${field.field_name}.${propName}`);
                return;
              }
              
              // Check for dynamic objects (nested key-value pairs)
              if (typeof propValue === "object" && propValue !== null && !Array.isArray(propValue) && propSchema?.additionalProperties) {
                const validEntries = Object.entries(propValue).filter(([k, v]) => {
                  if (k.startsWith('__empty_key_') || k.startsWith('__duplicate_') || k === '') return false;
                  if (v === null || v === undefined || v === "" || (typeof v === "string" && (v as string).trim() === "")) return false;
                  return true;
                });
                if (validEntries.length === 0) {
                  missingFields.push(`${field.field_name}.${propName}`);
                }
              }
            });
          }
        }
        return;
      }

      // Check for arrays (including arrays of custom models)
      if (Array.isArray(value)) {
        if (value.length === 0) {
          missingFields.push(field.field_name);
          return;
        }
        
        // If it's an array of custom models (is_list and is_custom_model), validate each item
        if (typeInfo.is_list && typeInfo.is_custom_model && typeInfo.model_schema) {
          const modelSchema = typeInfo.model_schema;
          const requiredProps = modelSchema.required || [];
          
          // Check each item in the array for required nested fields
          value.forEach((item, itemIndex) => {
            if (typeof item === "object" && item !== null) {
              requiredProps.forEach((propName: string) => {
                const propValue = item[propName];
                const propSchema = modelSchema.properties?.[propName];
                
                // Check if nested field is empty
                if (propValue === null || propValue === undefined || propValue === "") {
                  missingFields.push(`${field.field_name}[${itemIndex + 1}].${propName}`);
                  return;
                }
                
                // Check for empty strings
                if (typeof propValue === "string" && propValue.trim() === "") {
                  missingFields.push(`${field.field_name}[${itemIndex + 1}].${propName}`);
                  return;
                }
                
                // Check for dynamic objects (nested key-value pairs)
                if (typeof propValue === "object" && propValue !== null && propSchema?.additionalProperties) {
                  const validEntries = Object.entries(propValue).filter(([k, v]) => {
                    if (k.startsWith('__empty_key_') || k.startsWith('__duplicate_') || k === '') return false;
                    if (v === null || v === undefined || v === "" || (typeof v === "string" && (v as string).trim() === "")) return false;
                    return true;
                  });
                  if (validEntries.length === 0) {
                    missingFields.push(`${field.field_name}[${itemIndex + 1}].${propName}`);
                  }
                }
              });
            }
          });
        }
        return;
      }

      // Check for dynamic objects (key-value pairs like posting_cadence)
      if (typeof value === "object" && value !== null && !typeInfo.is_custom_model) {
        // Filter out temporary/empty keys
        const validEntries = Object.entries(value).filter(([k, v]) => {
          // Skip temporary markers and empty keys
          if (k.startsWith('__empty_key_') || k.startsWith('__duplicate_') || k === '') {
            return false;
          }
          // Skip empty values
          if (v === null || v === undefined || v === "" || (typeof v === "string" && v.trim() === "")) {
            return false;
          }
          return true;
        });
        // If no valid entries, consider it empty
        if (validEntries.length === 0) {
          missingFields.push(field.field_name);
        }
        return;
      }

      // Check for empty objects (custom models) - check nested required fields
      if (typeInfo.is_custom_model && typeof value === "object" && value !== null) {
        const modelSchema = typeInfo.model_schema;
        console.log(`Custom model ${field.field_name}:`, { value, modelSchema });
        
        // Check if the object has any content at all
        const hasAnyValue = Object.values(value).some((v: any) => {
          if (typeof v === "string") return v.trim() !== "";
          if (typeof v === "boolean") return true;
          if (typeof v === "object" && v !== null) {
            // For nested objects, check if they have valid entries
            if (Object.keys(v).length > 0) {
              const validEntries = Object.entries(v).filter(([k, val]) => {
                if (k.startsWith('__empty_key_') || k.startsWith('__duplicate_') || k === '') return false;
                if (val === null || val === undefined || val === "" || (typeof val === "string" && (val as string).trim() === "")) return false;
                return true;
              });
              return validEntries.length > 0;
            }
            return false;
          }
          return v !== null && v !== undefined;
        });

        if (!hasAnyValue) {
          missingFields.push(field.field_name);
          return;
        }

        // Check required nested fields within the custom model
        if (modelSchema?.required && Array.isArray(modelSchema.required)) {
          const missingNestedFields: string[] = [];
          console.log(`Checking required nested fields for ${field.field_name}:`, modelSchema.required);
          
          modelSchema.required.forEach((propName: string) => {
            const propValue = value[propName];
            const propSchema = modelSchema.properties?.[propName];
            
            // Check if nested field is empty
            if (propValue === null || propValue === undefined || propValue === "") {
              missingNestedFields.push(propName);
              return;
            }
            
            // Check for empty strings
            if (typeof propValue === "string" && propValue.trim() === "") {
              missingNestedFields.push(propName);
              return;
            }
            
            // Check for empty arrays
            if (Array.isArray(propValue) && propValue.length === 0) {
              missingNestedFields.push(propName);
              return;
            }
            
            // Check for dynamic objects (nested key-value pairs)
            if (typeof propValue === "object" && propValue !== null && !Array.isArray(propValue) && propSchema?.additionalProperties) {
              const validEntries = Object.entries(propValue).filter(([k, v]) => {
                if (k.startsWith('__empty_key_') || k.startsWith('__duplicate_') || k === '') return false;
                if (v === null || v === undefined || v === "" || (typeof v === "string" && (v as string).trim() === "")) return false;
                return true;
              });
              if (validEntries.length === 0) {
                missingNestedFields.push(propName);
              }
            }
          });
          
          if (missingNestedFields.length > 0) {
            // Add nested field names to missing fields with parent context
            missingNestedFields.forEach(nestedField => {
              missingFields.push(`${field.field_name}.${nestedField}`);
            });
          }
        }
        return;
      }

      // Check for empty strings, null, undefined
      if (!value || (typeof value === "string" && value.trim() === "")) {
        missingFields.push(field.field_name);
      }
    });

    if (missingFields.length > 0) {
      // Format field names for better readability
      const formattedFields = missingFields.map(name => {
        // Handle array indices and nested fields (e.g., "phases[1].name" or "content_strategy.posting_cadence")
        const parts = name.split('.');
        return parts.map(part => {
          // Check if part contains array index (e.g., "phases[1]")
          const arrayMatch = part.match(/^(.+)\[(\d+)\]$/);
          if (arrayMatch) {
            const fieldName = arrayMatch[1].split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
            const index = arrayMatch[2];
            return `${fieldName} Item ${index}`;
          }
          return part.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
        }).join(" > ");
      });
      notificationService.error(`Please fill in required fields: ${formattedFields.join(", ")}`);
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
        // For dynamic objects (like key-value pairs), filter out empty/temporary keys and empty values
        const filteredObj: Record<string, any> = {};
        for (const [k, v] of Object.entries(value)) {
          // Skip temporary markers and empty keys
          if (k.startsWith('__empty_key_') || k.startsWith('__duplicate_') || k === '') {
            continue;
          }
          // Skip empty values
          if (typeof v === "string" && v.trim() === "") {
            continue;
          }
          if (v === null || v === undefined || v === "") {
            continue;
          }
          filteredObj[k] = v;
        }
        
        // Only include if there are valid key-value pairs
        if (Object.keys(filteredObj).length > 0) {
          submitData[key] = filteredObj;
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
        onSuccess: (data) => {
          // console.log("=== KICKOFF SUCCESS ===");
          // console.log("Kickoff result:", data);
          // console.log("Crew run ID:", data?.id);
          // console.log("Full response:", JSON.stringify(data, null, 2));
          // console.log("======================");
          
          notificationService.success("Crew run started successfully!");
      
          // Clear localStorage cache on successful submission
          const cacheKey = getCacheKey();
          if (cacheKey) {
            localStorage.removeItem(cacheKey);
          }
          // Pass the run ID back to the parent
          const newRunId = data?.id
          onSuccess(newRunId);
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
