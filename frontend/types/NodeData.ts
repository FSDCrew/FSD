/**
 * Base node data that all nodes must have
 */
export interface BaseNodeData extends Record<string, unknown> {
  label: string;
  taskType: string;
}

/**
 * Node data for nodes that support editing
 */
export interface EditableNodeData extends BaseNodeData {
  onChange: (field: string, value: string) => void;
}

/**
 * Node data for nodes that can be deleted
 */
export interface DeletableNodeData extends BaseNodeData {
  onDelete: () => void;
}

/**
 * Node data for fully interactive nodes (editable and deletable)
 */
export interface InteractiveNodeData extends BaseNodeData {
  onChange: (field: string, value: string) => void;
  onDelete: () => void;
}

/**
 * Generic node data type that allows additional properties
 */
export type NodeData = BaseNodeData | EditableNodeData | DeletableNodeData | InteractiveNodeData;

/**
 * Type guard to check if node data is editable
 */
export function isEditableNodeData(data: BaseNodeData): data is EditableNodeData {
  return 'onChange' in data;
}

/**
 * Type guard to check if node data is deletable
 */
export function isDeletableNodeData(data: BaseNodeData): data is DeletableNodeData {
  return 'onDelete' in data;
}

/**
 * Type guard to check if node data is interactive
 */
export function isInteractiveNodeData(data: BaseNodeData): data is InteractiveNodeData {
  return 'onChange' in data && 'onDelete' in data;
}
