import type { RequiredInputField } from "@/lib/api/crew";

/**
 * Props for the KickoffForm component
 */
export interface KickoffFormProps {
  requiredInputs: RequiredInputField[];
  dynamicFormData: Record<string, any>;
  onFormChange: (fieldName: string, value: any) => void;
  onSubmit: (e: React.FormEvent) => void;
  onViewTemplate?: () => void;
  hasOrshotTask?: boolean;
}

/**
 * Represents a single crew run item
 */
export interface CrewRunItem {
  id: string;
  status: string;
  created_at: string;
  [key: string]: any;
}

/**
 * Props for the CrewRunsHistory component
 */
export interface CrewRunsHistoryProps {
  crewRuns: CrewRunItem[];
}

/**
 * Props for the RunDetails component
 */
export interface RunDetailsProps {
  selectedRun: CrewRunItem | null;
  crewRuns: CrewRunItem[];
  onClose: () => void;
}

/**
 * Props for custom node components
 */
export interface CustomNodeProps {
  data: {
    label: string;
    taskType: string;
    onChange?: (field: string, value: string) => void;
    onDelete?: () => void;
  };
  id: string;
}

/**
 * Props for start node component
 */
export interface StartNodeProps {
  data: {
    label: string;
  };
  id: string;
}
