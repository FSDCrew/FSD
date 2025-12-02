import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import type { Node, Edge } from "@xyflow/react";
import type { INotificationService } from "@/services/interfaces/INotificationService";
import type { BaseNodeData, InteractiveNodeData } from "@/types/NodeData";

interface PreDefinedTask {
  key: string;
  name: string;
  task_description: string;
}

export function useCrewFlow(
  nodes: Node[],
  edges: Edge[],
  setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void,
  setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void,
  preDefinedTasks: PreDefinedTask[],
  notificationService: INotificationService
) {
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [lastSavedNodes, setLastSavedNodes] = useState<Node[]>([]);
  const [lastSavedEdges, setLastSavedEdges] = useState<Edge[]>([]);

  const handleNodeDataChange = useCallback((nodeId: string, field: string, value: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              [field]: value,
            },
          };
        }
        return node;
      })
    );
    setHasUnsavedChanges(true);
  }, [setNodes]);

  const handleDeleteNode = useCallback((nodeId: string) => {
    if (nodeId === "start-node") {
      notificationService.error("The START node cannot be deleted.");
      return;
    }
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    setHasUnsavedChanges(true);
  }, [setNodes, setEdges, notificationService]);

  const convertNodesToOrderedTasks = useCallback((nodes: Node[], edges: Edge[]) => {
    const connectionMap = new Map<string, string>();
    edges.forEach(edge => {
      connectionMap.set(edge.source, edge.target);
    });
    const orderedTasks: any[] = [];
    let currentNodeId = connectionMap.get('start-node');
    let order = 1;
    
    while (currentNodeId) {
      const node = nodes.find(n => n.id === currentNodeId);
      if (!node) break;
      const taskType = node.data.taskType as string;
      const originalTask = preDefinedTasks.find(task => task.key === taskType);
      if (originalTask) {
        orderedTasks.push({
          ...originalTask,
          order: order,
        });
      }
      order++;
      currentNodeId = connectionMap.get(currentNodeId);
    }
    return orderedTasks;
  }, [preDefinedTasks]);

  const validateLinearFlow = useCallback((nodes: Node[], edges: Edge[]) => {
    const taskNodes = nodes.filter(n => n.id !== 'start-node');
    if (taskNodes.length === 0) return true;

    const connectionMap = new Map<string, string>();
    edges.forEach(edge => {
      connectionMap.set(edge.source, edge.target);
    });
    
    if (!connectionMap.has('start-node')) {
      notificationService.error("Please connect the START node to the first task in your flow.");
      return false;
    }

    let currentNodeId = connectionMap.get('start-node');
    let connectedCount = 0;
    const visited = new Set<string>();
    
    while (currentNodeId && !visited.has(currentNodeId)) {
      visited.add(currentNodeId);
      connectedCount++;
      currentNodeId = connectionMap.get(currentNodeId);
    }

    if (connectedCount !== taskNodes.length) {
      notificationService.error(`Linear flow incomplete: ${connectedCount} of ${taskNodes.length} tasks are connected. Please connect all tasks in a single chain starting from START.`);
      return false;
    }

    return true;
  }, [notificationService]);

  return {
    hasUnsavedChanges,
    setHasUnsavedChanges,
    lastSavedNodes,
    setLastSavedNodes,
    lastSavedEdges,
    setLastSavedEdges,
    handleNodeDataChange,
    handleDeleteNode,
    convertNodesToOrderedTasks,
    validateLinearFlow,
  };
}
