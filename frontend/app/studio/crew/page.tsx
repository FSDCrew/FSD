"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import StartNode from "@/components/StartNode";
import CustomNode from "@/components/CustomNode";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  createCrewCrewPost,
  updateCrewCrewPut,
  getAllCrewsCrewGet,
  replaceAllTasksForCrewTaskCrewIdSavePut,
  type CrewRead,
} from "@/lib/api/crud";
import { getPreDefinedTasksTasksPreDefinedGet } from "@/lib/api/crew";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogClose, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { RotateCcw } from "lucide-react";
import { useCrewForm } from "@/hooks/useCrewForm";
import { useCrewFlow } from "@/hooks/useCrewFlow";
import { KickoffForm } from "@/components/KickoffForm";
import { CrewRunsHistory } from "@/components/CrewRunsHistory";
import { ToastNotificationService } from "@/services/ToastNotificationService";
import { useCrewById } from "@/hooks/useCrewById";
import type { InteractiveNodeData, NodeData } from "@/types/NodeData";

interface PreDefinedTask {
  key: string;
  name: string;
  task_description: string;
}

interface NodeTypeConfig {
  type: string;
  name: string;
  color: string;
  description: string;
}

const taskColorMap: Record<string, string> = {
  marketing_research: "#c878e0ff",
  content_strategy: "#389e7eff",
  social_media_schedule: "#cc6262ff", 
  copywriter: "#f59e0bff",
  image_generator: "#f531b7",
  orshot_render: "#5881c3ff",
};

const getTaskColor = (taskKey: string): string => {
  return taskColorMap[taskKey] || "#6B7280";
};

// Move createNodeTypes outside component to ensure stable reference
const createNodeTypes = (nodeConfigs: NodeTypeConfig[]) => {
  const dynamicTypes = nodeConfigs.reduce((acc, config) => {
    acc[config.type] = CustomNode;
    return acc;
  }, {} as Record<string, any>);

  return {
    start: StartNode,
    ...dynamicTypes,
  };
};

const START_NODE: Node = {
  id: "start-node",
  type: "start",
  position: { x: 50, y: 250 },
  data: { label: "START" },
  draggable: true,
  deletable: false,
  selectable: true,
  connectable: true,
};

const initialNodes: Node[] = [START_NODE];
const initialEdges: Edge[] = [];

export default function CrewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { isAuthenticated, token } = useAuth();

  const [title, setTitle] = useState("");
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [mode, setMode] = useState<"edit" | "view">("edit");
  const [showUnsavedWarning, setShowUnsavedWarning] = useState(false);
  const [pendingMode, setPendingMode] = useState<"edit" | "view" | null>(null);
  const [showRunsHistory, setShowRunsHistory] = useState(false);
  const [runsRefreshKey, setRunsRefreshKey] = useState(0);
  const [hoveredNodeType, setHoveredNodeType] = useState<string | null>(null);
  const [nodeTypeConfigs, setNodeTypeConfigs] = useState<NodeTypeConfig[]>([]);
  const [preDefinedTasks, setPreDefinedTasks] = useState<PreDefinedTask[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(true);
  const [kickoffDialogOpen, setKickoffDialogOpen] = useState(false);
  const [lastSavedTitle, setLastSavedTitle] = useState("");

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);
  const nodesLoadedRef = React.useRef(false);
  const hasInitialFitViewRef = React.useRef(false);

  const nodeTypes = React.useMemo(() => createNodeTypes(nodeTypeConfigs), [nodeTypeConfigs]);

  // Service instances
  const notificationService = React.useMemo(() => new ToastNotificationService(), []);

  // Custom hooks
  const crewId = searchParams.get("id");
  const { data: crewData, isLoading: isLoadingCrew } = useCrewById(crewId);
  const crewForm = useCrewForm(crewId, notificationService, kickoffDialogOpen);
  const crewFlow = useCrewFlow(nodes, edges, setNodes, setEdges, preDefinedTasks, notificationService);

  // Extract stable functions from crewFlow to avoid dependency issues
  const {
    handleNodeDataChange,
    handleDeleteNode,
    setLastSavedNodes: setLastSavedNodesFromFlow,
    setLastSavedEdges: setLastSavedEdgesFromFlow,
  } = crewFlow;

  // Extract crew runs from crew data
  const crewRuns = React.useMemo(() => {
    if (crewData) {
      const crewDataWithRuns = crewData as CrewRead & { crew_runs?: any[] };
      const runs = crewDataWithRuns.crew_runs || [];
      return runs
    }
    return [];
  }, [crewData]);

  // Fetch pre-defined tasks
  useEffect(() => {
    const fetchPreDefinedTasks = async () => {
      setIsLoadingTasks(true);
      try {
        const response = await getPreDefinedTasksTasksPreDefinedGet();
        if (response.data) {
          const tasks: PreDefinedTask[] = response.data;
          setPreDefinedTasks(tasks);
          const configs = tasks.map((task) => ({
            type: task.key,
            name: task.name,
            color: getTaskColor(task.key),
            description: task.task_description,
          }));
          setNodeTypeConfigs(configs);
        } else {
          setNodeTypeConfigs([]);
        }
      } catch (error) {
        console.error("Error fetching pre-defined tasks:", error);
        setNodeTypeConfigs([]);
      } finally {
        setIsLoadingTasks(false);
      }
    };

    fetchPreDefinedTasks();
  }, []);

  // Handle nodes change with unsaved detection
  const handleNodesChange = useCallback(
    (changes: any[]) => {
      const hasPositionChange = changes.some((change) => change.type === "position" && change.dragging === false);
      if (hasPositionChange) {
        crewFlow.setHasUnsavedChanges(true);
      }
      onNodesChange(changes);
    },
    [onNodesChange, crewFlow]
  );

  // Handle connection
  const onConnect = useCallback(
    (params: Connection) => {
      if (params.target === "start-node") {
        toast.error("The START node cannot receive connections. It's the beginning of the flow.");
        return;
      }
      const sourceHasConnection = edges.some((edge) => edge.source === params.source);
      const targetHasConnection = edges.some((edge) => edge.target === params.target);
      if (sourceHasConnection) {
        toast.error("This node already has an outgoing connection. Each node can only connect to one other node for linear flow.");
        return;
      }
      if (targetHasConnection) {
        toast.error("The target node already has an incoming connection. Each node can only receive one connection for linear flow.");
        return;
      }
      setEdges((eds) => addEdge(params, eds));
      crewFlow.setHasUnsavedChanges(true);
    },
    [edges, setEdges, crewFlow]
  );

  // Handle node deletion
  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      deleted.forEach((node) => handleDeleteNode(node.id));
    },
    [handleDeleteNode]
  );

  // Drag and drop handlers
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData("application/reactflow") as string;
      if (!type || !reactFlowInstance) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const nodeTypeConfig = nodeTypeConfigs.find((n) => n.type === type);
      if (!nodeTypeConfig) return;

      const existingNode = nodes.find((n) => {
        const nodeData = n.data as NodeData;
        return nodeData.taskType === type && n.id !== "start-node";
      });
      if (existingNode) {
        toast.error(`Task "${nodeTypeConfig.name}" is already on the canvas. Each task type can only be added once.`);
        return;
      }

      const newNode: Node = {
        id: type,
        type: type,
        position,
        data: {
          label: nodeTypeConfig.name,
          taskType: type,
          onChange: (field: string, value: string) => handleNodeDataChange(type, field, value),
          onDelete: () => handleDeleteNode(type),
        },
        style: {
          background: getTaskColor(type),
          color: "white",
          border: "1px solid rgba(0, 0, 0, 0.2)",
          borderRadius: "8px",
          minWidth: "120px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
        },
        connectable: true,
      };

      setNodes((nds) => nds.concat(newNode));
      crewFlow.setHasUnsavedChanges(true);
    },
    [setNodes, handleNodeDataChange, handleDeleteNode, crewFlow, nodeTypeConfigs, nodes, reactFlowInstance]
  );

  // Create crew mutation
  const createCrewMutation = useMutation({
    mutationFn: async (crewData: { name: string }) => {
      const response = await createCrewCrewPost({ body: crewData });
      return response.data;
    },
    onSuccess: async (crewData) => {
      if (!crewData) {
        toast.error("Crew created but no data returned");
        return;
      }
      if (nodes.length > 0) {
        try {
          const tasks = crewFlow.convertNodesToOrderedTasks(nodes, edges);
          await replaceAllTasksForCrewTaskCrewIdSavePut({
            body: tasks,
            path: { crew_id: crewData.id },
          });
        } catch (error) {
          console.error("Error saving tasks:", error);
          toast.error("Crew created but failed to save tasks");
          return;
        }
      }
      const nodePositions = nodes.reduce((acc, node) => {
        acc[node.id] = node.position;
        return acc;
      }, {} as Record<string, { x: number; y: number }>);
      localStorage.setItem(`crew_positions_${crewData.id}`, JSON.stringify(nodePositions));
      crewFlow.setLastSavedNodes(nodes);
      crewFlow.setLastSavedEdges(edges);
      setLastSavedTitle(title);
      crewFlow.setHasUnsavedChanges(false);

      queryClient.invalidateQueries({ queryKey: ["crews"] });
      router.push(`/studio/crew?id=${crewData.id}&title=${encodeURIComponent(crewData.name || "")}`);
      toast.success("Crew created successfully!");
    },
    onError: (error) => {
      console.error("Error creating crew:", error);
      toast.error("Failed to create crew. Please try again.");
    },
  });

  // Update crew mutation
  const updateCrewMutation = useMutation({
    mutationFn: async (crewData: { id: string; name: string }) => {
      await updateCrewCrewPut({ body: crewData });
      const tasks = crewFlow.convertNodesToOrderedTasks(nodes, edges);
      await replaceAllTasksForCrewTaskCrewIdSavePut({
        body: tasks,
        path: { crew_id: crewData.id },
      });
      const nodePositions = nodes.reduce((acc, node) => {
        acc[node.id] = node.position;
        return acc;
      }, {} as Record<string, { x: number; y: number }>);
      localStorage.setItem(`crew_positions_${crewData.id}`, JSON.stringify(nodePositions));
      return crewData;
    },
    onSuccess: () => {
      crewFlow.setLastSavedNodes(nodes);
      crewFlow.setLastSavedEdges(edges);
      setLastSavedTitle(title);
      crewFlow.setHasUnsavedChanges(false);
      queryClient.invalidateQueries({ queryKey: ["crews"] });
      toast.success("Crew updated successfully!");
      
      // Invalidate required inputs to refetch when tasks change
      if (mode === "edit") {
        crewForm.invalidateRequiredInputs();
      }
    },
    onError: (error) => {
      console.error("Error updating crew:", error);
      toast.error("Failed to update crew. Please try again.");
    },
  });

  // Handle save
  const handleSave = async () => {
    if (!title || title.trim() === "") {
      toast.error("Crew name cannot be empty");
      return;
    }

    if (!crewFlow.validateLinearFlow(nodes, edges)) {
      return;
    }


    try {
      const response = await getAllCrewsCrewGet();
      const allCrews = Array.isArray(response.data) ? response.data : response.data ? [response.data] : [];
      const duplicateCrew = allCrews.find((crew: CrewRead) => crew.name?.trim().toLowerCase() === title.trim().toLowerCase() && crew.id !== crewId);

      if (duplicateCrew) {
        toast.error(`A crew with the name "${title}" already exists. Please choose a different name.`);
        return;
      }

      if (crewId) {
        updateCrewMutation.mutate({ id: crewId, name: title });
      } else {
        createCrewMutation.mutate({ name: title });
      }
    } catch (error) {
      console.error("Error checking for duplicate crews:", error);
      toast.error("Failed to validate crew name. Please try again.");
    }
  };

  // Handle kickoff dialog
  const handleKickoffDialogOpen = (open: boolean) => {
    setKickoffDialogOpen(open);
    // Required inputs will be fetched automatically by useRequiredInputs hook when dialog opens
  };

  const handleKickoffSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await crewForm.onKickoffSubmit(e, async (newRunId?: string) => {
      setKickoffDialogOpen(false);
      // Crew runs will be refreshed automatically via query invalidation in useCrewKickoff hook
      // Force refresh of runs history component
      setRunsRefreshKey((prev) => prev + 1);

      if (newRunId && crewId) {
        router.push(
          `/studio/crew/run?crewId=${crewId}&runId=${newRunId}&crewName=${encodeURIComponent(title)}`
        );
      }
    });
  };

  // Mode change handlers
  const handleModeChange = (newMode: "edit" | "view") => {
    if (mode === newMode) return;

    if (crewFlow.hasUnsavedChanges) {
      setPendingMode(newMode);
      setShowUnsavedWarning(true);
    } else {
      setMode(newMode);
      // Show run history by default when switching to view mode
      if (newMode === "view") {
        setShowRunsHistory(true);
        setIsEditingTitle(false); // Close title editing when entering view mode
      }
      if (crewId) {
        localStorage.setItem(`crew_mode_${crewId}`, newMode);
      }
      if (reactFlowInstance) {
        setTimeout(() => {
          reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
        }, 100);
      }
    }
  };

  const confirmModeChange = () => {
    const revertedNodes = crewFlow.lastSavedNodes.map((node: Node) => ({
      ...node,
      data: {
        ...node.data,
        onChange: (field: string, value: string) => handleNodeDataChange(node.id, field, value),
        onDelete: () => handleDeleteNode(node.id),
      },
    }));

    setNodes(revertedNodes);
    setEdges(crewFlow.lastSavedEdges);
    setTitle(lastSavedTitle);
    crewFlow.setHasUnsavedChanges(false);

    if (pendingMode) {
      setMode(pendingMode);
      // Show run history by default when switching to view mode
      if (pendingMode === "view") {
        setShowRunsHistory(true);
      }
      if (crewId) {
        localStorage.setItem(`crew_mode_${crewId}`, pendingMode);
      }
      if (reactFlowInstance) {
        setTimeout(() => {
          reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
        }, 100);
      }
      setPendingMode(null);
    }
    setShowUnsavedWarning(false);
  };

  const cancelModeChange = () => {
    setPendingMode(null);
    setShowUnsavedWarning(false);
  };

  // Handle cancel/discard
  const handleCancel = () => {
    router.push("/studio");
  };

  const handleDiscardChanges = () => {
    const revertedNodes = crewFlow.lastSavedNodes.map((node: Node) => ({
      ...node,
      data: {
        ...node.data,
        onChange: (field: string, value: string) => handleNodeDataChange(node.id, field, value),
        onDelete: () => handleDeleteNode(node.id),
      },
    }));

    setNodes(revertedNodes);
    setEdges(crewFlow.lastSavedEdges);
    setTitle(lastSavedTitle);
    crewFlow.setHasUnsavedChanges(false);
    router.push("/studio");
  };

  // Reset nodes loaded ref when crewId changes
  useEffect(() => {
    nodesLoadedRef.current = false;
  }, [crewId]);

  // Load crew data on mount
  useEffect(() => {
    if (!token) router.push("/auth/login");

    const cardTitle = searchParams.get("title") || "Untitled";
    const cardId = searchParams.get("id");
    const urlMode = searchParams.get("mode");

    setTitle(cardTitle);
    setLastSavedTitle(cardTitle);

    // Set mode from URL parameter if provided
    if (urlMode === "view" || urlMode === "edit") {
      setMode(urlMode);
      // Show run history by default when in view mode
      if (urlMode === "view") {
        setShowRunsHistory(true);
        setIsEditingTitle(false); // Ensure title is not editable in view mode
      }
    }

    // Only allow editing title if we're in edit mode (or no mode specified, defaults to edit)
    if (cardTitle === "Untitled" && urlMode !== "view") {
      setIsEditingTitle(true);
    }
  }, [router, searchParams, token]);

  // Load crew tasks and nodes when crew data and node configs are available
  useEffect(() => {
    if (crewData && crewData.tasks && nodeTypeConfigs.length > 0 && crewId && !nodesLoadedRef.current) {
      nodesLoadedRef.current = true;
      const sortedTasks = [...crewData.tasks].sort((a, b) => a.order - b.order);
      const savedPositionsStr = localStorage.getItem(`crew_positions_${crewId}`);
      const savedPositions = savedPositionsStr ? (JSON.parse(savedPositionsStr) as Record<string, { x: number; y: number }>) : {};

      const loadedNodes = sortedTasks.map((task, index) => {
        const nodeTypeConfig = nodeTypeConfigs.find((n) => n.type === task.key);
        const defaultPosition = {
          x: 300 + index * 300,
          y: 250,
        };
        const position = savedPositions[task.key] || defaultPosition;

        return {
          id: task.key,
          type: task.key,
          position: position,
          data: {
            label: nodeTypeConfig?.name || task.key,
            taskType: task.key,
            onChange: (field: string, value: string) => handleNodeDataChange(task.key, field, value),
            onDelete: () => handleDeleteNode(task.key),
          },
          style: {
            background: getTaskColor(task.key),
            color: "white",
            border: "1px solid rgba(0, 0, 0, 0.2)",
            borderRadius: "8px",
            minWidth: "120px",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
          },
          connectable: true,
        } as Node;
      });

      const reconstructedEdges: Edge[] = [];
      if (sortedTasks.length > 0) {
        reconstructedEdges.push({
          id: `start-node-${sortedTasks[0].key}`,
          source: "start-node",
          target: sortedTasks[0].key,
        });
      }
      for (let i = 0; i < sortedTasks.length - 1; i++) {
        reconstructedEdges.push({
          id: `${sortedTasks[i].key}-${sortedTasks[i + 1].key}`,
          source: sortedTasks[i].key,
          target: sortedTasks[i + 1].key,
        });
      }
      const startNodeWithPosition = {
        ...START_NODE,
        position: savedPositions["start-node"] || START_NODE.position,
        connectable: true,
      };
      setNodes([startNodeWithPosition, ...loadedNodes]);
      setLastSavedNodesFromFlow([startNodeWithPosition, ...loadedNodes]);
      setEdges(reconstructedEdges);
      setLastSavedEdgesFromFlow(reconstructedEdges);

      if (reactFlowInstance && !hasInitialFitViewRef.current) {
        setTimeout(() => {
          reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
          hasInitialFitViewRef.current = true;
        }, 100);
      }
    }
  }, [crewData, nodeTypeConfigs, crewId, setNodes, setEdges, handleNodeDataChange, handleDeleteNode, setLastSavedNodesFromFlow, setLastSavedEdgesFromFlow, reactFlowInstance]);

  // Fit view when ReactFlow instance is ready (only on first load with saved data)
  useEffect(() => {
    if (reactFlowInstance && nodes.length > 1 && !hasInitialFitViewRef.current && nodesLoadedRef.current) {
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
        hasInitialFitViewRef.current = true;
      }, 100);
    }
  }, [reactFlowInstance, nodes.length]);

  // Update node draggability and selectability when mode changes
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        draggable: mode === "edit",
        selectable: mode === "edit",
      }))
    );
  }, [mode, setNodes]);

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="p-6">
        {/* Top Section with Title and Mode Toggle */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {mode === "view" && (
              <Button
                onClick={() => {
                  setShowRunsHistory(!showRunsHistory);
                  if (reactFlowInstance) {
                    setTimeout(() => {
                      reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
                    }, 100);
                  }
                }}
                variant="default"
              >
                {showRunsHistory ? "Hide" : ""} Crew Run History
              </Button>
            )}

            <div>
              {isEditingTitle ? (
                <div className="flex flex-col">
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => {
                      const newTitle = e.target.value;
                      setTitle(newTitle);
                      crewFlow.setHasUnsavedChanges(true);
                    }}
                    onBlur={() => setIsEditingTitle(false)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") setIsEditingTitle(false);
                    }}
                    className="text-4xl font-bold bg-transparent border-b-2 focus:outline-none pb-2 border-primary"
                    autoFocus
                    placeholder="Enter title..."
                    style={{ width: "fit-content", minWidth: "300px" }}
                  />
                </div>
              ) : (
                <h1
                  onClick={() => mode === "edit" && setIsEditingTitle(true)}
                  className={`text-4xl font-bold pb-2 border-b-2 border-transparent inline-block ${mode === "edit" ? "cursor-pointer hover:text-primary transition-colors hover:border-muted" : "cursor-default"
                    }`}
                >
                  {title || "Untitled"}
                </h1>
              )}
            </div>
          </div>

          {/* Mode Toggle */}
          <div className="flex gap-2 bg-card border border-border rounded-lg p-1">
            <Button onClick={() => handleModeChange("edit")} variant={mode === "edit" ? "default" : "ghost"} size="sm">
              Edit Mode
            </Button>
            <Button onClick={() => handleModeChange("view")} variant={mode === "view" ? "default" : "ghost"} size="sm">
              View Mode
            </Button>
          </div>
        </div>

        {/* Unsaved Changes Warning Modal */}
        <AlertDialog open={showUnsavedWarning} onOpenChange={setShowUnsavedWarning}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Unsaved Changes</AlertDialogTitle>
              <AlertDialogDescription>You have unsaved changes. Do you want to discard them and switch modes?</AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={cancelModeChange} >Keep Editing</AlertDialogCancel>
              <AlertDialogAction onClick={confirmModeChange} className="bg-destructive text-white hover:bg-destructive/90">
                Discard Changes
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* React Flow Canvas with Sidebar */}
        <div className="mb-8 flex gap-4">
          {/* Node Palette Sidebar */}
          {mode === "edit" && (
            <div className="w-64 flex-shrink-0 bg-[#1a1a1a] border-2 border-white rounded-lg p-4 relative">
              <h3 className="text-lg font-semibold mb-2 text-white">Node Types</h3>
              <p className="text-xs text-gray-300 mb-4">Drag to canvas</p>

              <div className="space-y-3">
                {!isLoadingTasks && nodeTypeConfigs.length > 0 ? (
                  nodeTypeConfigs.map((nodeType) => (
                    <div
                      key={nodeType.type}
                      draggable
                      onDragStart={(e) => onDragStart(e, nodeType.type)}
                      onMouseEnter={() => setHoveredNodeType(nodeType.type)}
                      onMouseLeave={() => setHoveredNodeType(null)}
                      className="flex items-center gap-3 p-3 rounded-lg border-2 border-transparent hover:border-white cursor-move transition-colors bg-[#3a3a3a] hover:bg-[#2a2a2a] relative"
                    >
                      <div>
                        <div className="font-medium text-sm text-white">{nodeType.name}</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-white py-8">{isLoadingTasks ? "Loading node types..." : "No node types available"}</div>
                )}
              </div>

              {/* Hover Card */}
              {hoveredNodeType && (
                <div className="absolute left-full top-0 ml-4 w-80 border-2 border-white rounded-lg p-4 shadow-lg z-50" style={{ backgroundColor: getTaskColor(hoveredNodeType) }}>
                  {(() => {
                    const nodeType = nodeTypeConfigs.find((n) => n.type === hoveredNodeType);
                    if (!nodeType) return null;
                    return (
                      <>
                        <h4 className="font-semibold text-white mb-2">{nodeType.name}</h4>
                        <p className="text-sm text-white leading-relaxed opacity-90">{nodeType.description}</p>
                      </>
                    );
                  })()}
                </div>
              )}
            </div>
          )}

          {/* Runs History Sidebar */}
          {mode === "view" && showRunsHistory && (
            <div key={runsRefreshKey}>
              <CrewRunsHistory crewRuns={crewRuns} />
            </div>
          )}

          {/* React Flow Canvas */}
          <div className="flex-1 flex flex-col gap-4">
            {/* Canvas */}
            <div className={`h-[600px] border-2 border-border rounded-lg bg-card relative`}>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                onNodesChange={mode === "edit" ? handleNodesChange : undefined}
                onEdgesChange={mode === "edit" ? onEdgesChange : undefined}
                onConnect={mode === "edit" ? onConnect : undefined}
                onDrop={mode === "edit" ? onDrop : undefined}
                onDragOver={mode === "edit" ? onDragOver : undefined}
                onNodesDelete={mode === "edit" ? onNodesDelete : undefined}
                deleteKeyCode={mode === "edit" ? ["Delete", "Backspace"] : undefined}
                nodesDraggable={mode === "edit"}
                nodesConnectable={mode === "edit"}
                elementsSelectable={mode === "edit"}
                panOnDrag={mode === "edit"}
                zoomOnScroll={mode === "edit"}
                zoomOnPinch={mode === "edit"}
                zoomOnDoubleClick={mode === "edit"}
                onInit={setReactFlowInstance}
              >
                <Controls />
                <MiniMap />
                <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              </ReactFlow>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 justify-end">
          {mode === "edit" ? (
            <>
              {crewFlow.hasUnsavedChanges ? (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="secondary">Cancel</Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Discard Changes?</AlertDialogTitle>
                      <AlertDialogDescription>
                        You have unsaved changes. Are you sure you want to discard them and return to the studio? This action cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Keep Editing</AlertDialogCancel>
                      <AlertDialogAction onClick={handleDiscardChanges} className="bg-destructive text-white hover:bg-destructive/90">
                        Discard Changes
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              ) : (
                <Button onClick={handleCancel} variant="secondary">
                  Cancel
                </Button>
              )}
              <Button onClick={handleSave} disabled={!crewFlow.hasUnsavedChanges} variant="default">
                Save Changes
              </Button>
            </>
          ) : (
            <Dialog open={kickoffDialogOpen} onOpenChange={handleKickoffDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">Kickoff</Button>
              </DialogTrigger>
              <DialogContent className="max-w-[95vw] w-full sm:max-w-[90vw] lg:max-w-[800px] max-h-[90vh] overflow-y-auto">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={crewForm.resetForm}
                  className="absolute right-12 top-4 h-4 w-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground"
                  title="Reset form"
                >
                  <RotateCcw className="h-4 w-4" />
                </Button>
                <DialogHeader>
                  <DialogTitle>Required Inputs for Kickoff</DialogTitle>
                </DialogHeader>
                {crewForm.isLoadingRequiredInputs ? (
                  <div className="flex justify-center items-center py-8">
                    <div className="text-gray-500">Loading form...</div>
                  </div>
                ) : (
                  <>
                    <KickoffForm
                      requiredInputs={crewForm.requiredInputs}
                      dynamicFormData={crewForm.dynamicFormData}
                      onFormChange={crewForm.handleDynamicFormChange}
                      onSubmit={handleKickoffSubmit}
                    />
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button type="button" variant="outline" disabled={crewForm.isSubmitting}>
                          Cancel
                        </Button>
                      </DialogClose>
                      <Button
                        type="submit"
                        onClick={handleKickoffSubmit}
                        disabled={crewForm.isSubmitting}
                      >
                        {crewForm.isSubmitting ? "Submitting..." : "Kickoff!"}
                      </Button>
                    </DialogFooter>
                  </>
                )}
              </DialogContent>
            </Dialog>
          )}
        </div>
      </main>
    </div>
  );
}
