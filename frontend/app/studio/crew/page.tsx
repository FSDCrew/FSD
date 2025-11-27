"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import ResearchNode from "@/components/ResearchNode";
import CopywritingNode from "@/components/CopywritingNode";
import OrshotNode from "@/components/OrshotNode";
import SurveyNode from "@/components/SurveyNode";
import SchedulerNode from "@/components/SchedulerNode";
import StartNode from "@/components/StartNode";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  type Connection,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { createCrewCrewPost, updateCrewCrewPut, getCrewsCrewGet, replaceAllTasksForCrewTaskCrewIdSavePut, type CrewRead, type TaskCreate } from "@/lib/api/crud";
import { client } from "@/lib/api/crud/client.gen";
import { useMutation, useQueryClient } from "@tanstack/react-query";

const nodeTypes = {
  start: StartNode,
  research: ResearchNode,
  copywriting: CopywritingNode,
  orshot: OrshotNode,
  survey: SurveyNode,
  scheduler: SchedulerNode,
};

const START_NODE: Node = {
  id: 'start-node',
  type: 'start',
  position: { x: 50, y: 250 },
  data: { label: 'START' },
  draggable: true,
  deletable: false,
  selectable: true,
};

const initialNodes: Node[] = [START_NODE];
const initialEdges: Edge[] = [];

type TaskType = "research" | "copywriting" | "orshot" | "survey" | "scheduler";

interface NodeData extends Record<string, unknown> {
  label: string;
  taskType: TaskType;
  description: string;
  expectedOutput: string;
  crewInput: {
    topic: string;
  };
  taskInput?: {
    designTemplate?: string;
    numOfWeeks?: number;
  };
  onChange?: (field: string, value: string) => void;
  onDelete?: () => void;
}

const nodeTypeConfigs = [
  {
    type: "research" as TaskType,
    label: "Research Node",
    color: "#4b82dbff",
    icon: "🔍",
  },
  {
    type: "copywriting" as TaskType,
    label: "Copywriting Node",
    color: "#7357b5ff",
    icon: "✍️",
  },
  {
    type: "orshot" as TaskType,
    label: "Orshot Node",
    color: "#dc5699ff",
    icon: "🎨",
  },
  {
    type: "survey" as TaskType,
    label: "Survey Node",
    color: "#51a88bff",
    icon: "📊",
  },
  {
    type: "scheduler" as TaskType,
    label: "Scheduler Node",
    color: "#f4ad34ff",
    icon: "📅",
  },
];

export default function CrewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [hasDuplicateTitle, setHasDuplicateTitle] = useState(false);
  const [mode, setMode] = useState<"edit" | "view">("edit");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showUnsavedWarning, setShowUnsavedWarning] = useState(false);
  const [pendingMode, setPendingMode] = useState<"edit" | "view" | null>(null);
  const [showRunsHistory, setShowRunsHistory] = useState(false);
  const [runsRefreshKey, setRunsRefreshKey] = useState(0);
  const [crewRuns, setCrewRuns] = useState<any[]>([]);
  const [selectedRun, setSelectedRun] = useState<any | null>(null);
  const [notification, setNotification] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);
  
  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  // Keep track of last saved state for reverting
  const [lastSavedNodes, setLastSavedNodes] = useState<Node[]>([START_NODE]);
  const [lastSavedEdges, setLastSavedEdges] = useState<Edge[]>(initialEdges);
  const [lastSavedTitle, setLastSavedTitle] = useState("");

  // Wrap onNodesChange to detect position changes
  const handleNodesChange = useCallback((changes: any[]) => {
    // Check if any change is a position change
    const hasPositionChange = changes.some(change => change.type === 'position' && change.dragging === false);
    
    if (hasPositionChange) {
      setHasUnsavedChanges(true);
    }
    
    // Apply the changes
    onNodesChange(changes);
  }, [onNodesChange]);

  const onConnect = useCallback(
    (params: Connection) => {
      // Prevent connections TO the start node
      if (params.target === 'start-node') {
        showNotification("The START node cannot receive connections. It's the beginning of the flow.", "error");
        return;
      }
      
      // Check if source node already has an outgoing connection (all nodes including start node can only have ONE outgoing connection)
      const sourceHasConnection = edges.some(edge => edge.source === params.source);
      
      // Check if target node already has an incoming connection
      const targetHasConnection = edges.some(edge => edge.target === params.target);
      
      if (sourceHasConnection) {
        showNotification("This node already has an outgoing connection. Each node can only connect to one other node for linear flow.", "error");
        return;
      }
      
      if (targetHasConnection) {
        showNotification("The target node already has an incoming connection. Each node can only receive one connection for linear flow.", "error");
        return;
      }
      
      setEdges((eds) => addEdge(params, eds));
      setHasUnsavedChanges(true);
    },
    [edges, setEdges]
  );

  
const queryClient = useQueryClient();

// Helper function to convert nodes to TaskCreate format with linear order
const convertNodesToTasks = (nodes: Node[], edges: Edge[]): TaskCreate[] => {
  // Build a map of connections: nodeId -> connected nodeId
  const connectionMap = new Map<string, string>();
  edges.forEach(edge => {
    connectionMap.set(edge.source, edge.target);
  });
  
  // Traverse from START node to build ordered list
  const orderedTasks: TaskCreate[] = [];
  let currentNodeId = connectionMap.get('start-node');
  let order = 1;  // Start at 1 so tasks are numbered 1, 2, 3...
  
  while (currentNodeId) {
    const node = nodes.find(n => n.id === currentNodeId);
    if (!node) break;
    
    const nodeData = node.data as NodeData;
    orderedTasks.push({
      key: node.id,
      description: nodeData.description || "",
      expected_output: nodeData.expectedOutput || "",
      order: order,
      agent_key: nodeData.taskType || "default",
    });
    
    order++;
    currentNodeId = connectionMap.get(currentNodeId);
  }
  
  return orderedTasks;
};

// Create crew mutation
const createCrewMutation = useMutation({
  mutationFn: async (crewData: { name: string }) => {
    const response = await createCrewCrewPost({ body: crewData });
    return response.data;
  },

  onSuccess: async (crewData) => {
    if (!crewData) {
      showNotification("Crew created but no data returned", "error");
      return;
    }
    
    // Save tasks if any nodes exist
    if (nodes.length > 0) {
      try {
        const tasks = convertNodesToTasks(nodes, edges);
        await replaceAllTasksForCrewTaskCrewIdSavePut({
          body: tasks,
          path: { crew_id: crewData.id }
        });
      } catch (error) {
        console.error("Error saving tasks:", error);
        showNotification("Crew created but failed to save tasks", "error");
        return;
      }
    }
    
    // Save node positions to localStorage
    const nodePositions = nodes.reduce((acc, node) => {
      acc[node.id] = node.position;
      return acc;
    }, {} as Record<string, { x: number; y: number }>);
    localStorage.setItem(`crew_positions_${crewData.id}`, JSON.stringify(nodePositions));
    
    // Update last saved state
    setLastSavedNodes(nodes);
    setLastSavedEdges(edges);
    setLastSavedTitle(title);
    setHasUnsavedChanges(false);
    
    // Refresh crews list
    queryClient.invalidateQueries({ queryKey: ['crews'] });
    
    // Navigate to the newly created crew
    router.push(`/studio/crew?id=${crewData.id}&title=${encodeURIComponent(crewData.name)}`);
    
    showNotification("Crew created successfully!", "success");
  },

  onError: (error) => {
    console.error("Error creating crew:", error);
    showNotification("Failed to create crew. Please try again.", "error");
  }
});

// Update crew mutation
const updateCrewMutation = useMutation({
  mutationFn: async (crewData: { id: string; name: string }) => {
    // Update crew name
    await updateCrewCrewPut({ body: crewData });
    
    // Update tasks
    const tasks = convertNodesToTasks(nodes, edges);
    await replaceAllTasksForCrewTaskCrewIdSavePut({
      body: tasks,
      path: { crew_id: crewData.id }
    });
    
    // Save node positions to localStorage
    const nodePositions = nodes.reduce((acc, node) => {
      acc[node.id] = node.position;
      return acc;
    }, {} as Record<string, { x: number; y: number }>);
    localStorage.setItem(`crew_positions_${crewData.id}`, JSON.stringify(nodePositions));
    
    return crewData;
  },
    
  onSuccess: () => {
    // Update last saved state
    setLastSavedNodes(nodes);
    setLastSavedEdges(edges);
    setLastSavedTitle(title);
    setHasUnsavedChanges(false);
    
    // Refresh crews list
    queryClient.invalidateQueries({ queryKey: ['crews'] });
    
    showNotification("Crew updated successfully!", "success");
  },
  
  onError: (error) => {
    console.error("Error updating crew:", error);
    showNotification("Failed to update crew. Please try again.", "error");
  }
});

  // Function to update node data from within the node component
  const handleNodeDataChange = useCallback((nodeId: string, field: string, value: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          const currentData = node.data as NodeData;
          
          // Handle nested field updates (e.g., "crewInput.topic")
          if (field.includes('.')) {
            const [parent, child] = field.split('.');
            return {
              ...node,
              data: {
                ...currentData,
                [parent]: {
                  ...(currentData[parent] as Record<string, unknown>),
                  [child]: value,
                },
              },
            };
          }
          
          // Handle simple field updates
          return {
            ...node,
            data: {
              ...currentData,
              [field]: value,
            },
          };
        }
        return node;
      })
    );
    setHasUnsavedChanges(true);
  }, [setNodes]);

  // Function to delete a node
  const handleDeleteNode = useCallback((nodeId: string) => {
    // Prevent deletion of start node
    if (nodeId === 'start-node') {
      showNotification("The START node cannot be deleted.", "error");
      return;
    }
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    setHasUnsavedChanges(true);
  }, [setNodes, setEdges]);

  // Handle keyboard delete
  const onNodesDelete = useCallback((deleted: Node[]) => {
    deleted.forEach((node) => handleDeleteNode(node.id));
  }, [handleDeleteNode]);

  const onDragStart = (event: React.DragEvent, nodeType: TaskType) => {
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

      const type = event.dataTransfer.getData("application/reactflow") as TaskType;
      if (!type) return;

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      };

      const nodeTypeConfig = nodeTypeConfigs.find((n) => n.type === type);
      if (!nodeTypeConfig) return;

      const nodeId = `${type}-${Date.now()}`;
      
      const newNode: Node = {
        id: nodeId,
        type: type,
        position,
        data: {
          label: nodeTypeConfig.label,
          taskType: type,
          icon: nodeTypeConfig.icon,
          description: "",
          expectedOutput: "",
          crewInput: {
            topic: "",
          },
          taskInput:
            type === "orshot"
              ? { designTemplate: "" }
              : type === "scheduler"
              ? { numOfWeeks: 1 }
              : undefined,
          onChange: (field: string, value: string) => handleNodeDataChange(nodeId, field, value),
          onDelete: () => handleDeleteNode(nodeId),
        } as NodeData,
        style: {
          background: nodeTypeConfig.color,
          color: "white",
          border: "2px solid #222",
          borderRadius: "8px",
          minWidth: "120px",
        },
      };

      setNodes((nds) => nds.concat(newNode));
      setHasUnsavedChanges(true);
    },
    [setNodes, handleNodeDataChange, handleDeleteNode]
  );



  const { isAuthenticated, token } = useAuth();

  useEffect(() => {
    if (!token) router.push("/auth/login");

    // Get card data from URL params
    const cardTitle = searchParams.get("title") || "Untitled";
    const cardDescription = searchParams.get("description") || "";
    const cardId = searchParams.get("id");

    setTitle(cardTitle);
    setDescription(cardDescription);
    setLastSavedTitle(cardTitle);

    // Load saved mode for this specific card
    if (cardId) {
      const savedMode = localStorage.getItem(`crew_mode_${cardId}`);
      if (savedMode === "view" || savedMode === "edit") {
        setMode(savedMode);
      }
      
      // Load tasks from backend for existing crew
      const loadCrewData = async () => {
        try {
          // Use direct fetch to GET /crew/{id} which returns a single crew object
          const response = await fetch(`${client.getConfig().baseUrl}/crew/${cardId}`, {
            credentials: 'include',
          });
          
          if (!response.ok) {
            throw new Error('Failed to load crew data');
          }
          
          const crewData = await response.json();
          if (crewData && crewData.tasks) {
            // Store crew runs for display in runs history (using type assertion until SDK is regenerated)
            const crewDataWithRuns = crewData as CrewRead & { crew_runs?: any[] };
            if (crewDataWithRuns.crew_runs) {
              setCrewRuns(crewDataWithRuns.crew_runs);
            }
            
            // Sort tasks by order to ensure correct sequence
            const sortedTasks = [...crewData.tasks].sort((a, b) => a.order - b.order);
            
            // Load saved node positions from localStorage
            const savedPositionsStr = localStorage.getItem(`crew_positions_${cardId}`);
            const savedPositions = savedPositionsStr ? JSON.parse(savedPositionsStr) as Record<string, { x: number; y: number }> : {};
            
            // Convert backend tasks to React Flow nodes
            const loadedNodes = sortedTasks.map((task, index) => {
              const nodeTypeConfig = nodeTypeConfigs.find((n) => n.type === task.agent_key as TaskType);
              
              // Use saved position if available, otherwise create straight horizontal line layout
              // START node is at (50, 250), so first task starts at x=300
              const defaultPosition = { 
                x: 300 + (index * 300),  // Horizontal spacing of 300px between nodes
                y: 250                    // Same vertical position as START node (straight line)
              };
              const position = savedPositions[task.key] || defaultPosition;
              
              return {
                id: task.key,
                type: task.agent_key as TaskType,
                position: position,
                data: {
                  label: nodeTypeConfig?.label || task.agent_key,
                  taskType: task.agent_key as TaskType,
                  icon: nodeTypeConfig?.icon || "📝",
                  description: task.description,
                  expectedOutput: task.expected_output,
                  crewInput: { topic: "" },
                  onChange: (field: string, value: string) => handleNodeDataChange(task.key, field, value),
                  onDelete: () => handleDeleteNode(task.key),
                } as NodeData,
                style: {
                  background: nodeTypeConfig?.color || "#6b7280",
                  color: "white",
                  border: "2px solid #222",
                  borderRadius: "8px",
                  minWidth: "120px",
                },
              } as Node;
            });
            
            // Reconstruct edges based on task order
            const reconstructedEdges: Edge[] = [];
            
            // Connect START node to first task
            if (sortedTasks.length > 0) {
              reconstructedEdges.push({
                id: `start-node-${sortedTasks[0].key}`,
                source: 'start-node',
                target: sortedTasks[0].key,
              });
            }
            
            // Connect tasks in sequence
            for (let i = 0; i < sortedTasks.length - 1; i++) {
              reconstructedEdges.push({
                id: `${sortedTasks[i].key}-${sortedTasks[i + 1].key}`,
                source: sortedTasks[i].key,
                target: sortedTasks[i + 1].key,
              });
            }
            
            // Restore START node position if saved, otherwise use default
            const startNodeWithPosition = {
              ...START_NODE,
              position: savedPositions['start-node'] || START_NODE.position,
            };
            
            // Always include the start node at the beginning
            setNodes([startNodeWithPosition, ...loadedNodes]);
            setLastSavedNodes([startNodeWithPosition, ...loadedNodes]);
            setEdges(reconstructedEdges);
            setLastSavedEdges(reconstructedEdges);
            
            // Fit view after loading crew data
            if (reactFlowInstance) {
              setTimeout(() => {
                reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
              }, 100);
            }
          }
        } catch (error) {
          console.error("Error loading crew data:", error);
        }
      };
      
      loadCrewData();
    }

    // If it's a new card (Untitled), start editing the title immediately
    if (cardTitle === "Untitled") {
      setIsEditingTitle(true);
    }
  }, [router, searchParams, setNodes, setEdges]);

  // Fit view when ReactFlow instance is ready and nodes are loaded
  useEffect(() => {
    if (reactFlowInstance && nodes.length > 1) { // More than just START node
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
      }, 100);
    }
  }, [reactFlowInstance, nodes.length]);

  const handleSave = async () => {
    const cardId = searchParams.get("id");
    
    // Validate title
    if (!title || title.trim() === "") {
      showNotification("Crew name cannot be empty", "error");
      return;
    }
    
    // Validate linear flow: Check if nodes form a single connected chain from START
    const taskNodes = nodes.filter(n => n.id !== 'start-node');
    if (taskNodes.length > 0) {
      // Build connection map
      const connectionMap = new Map<string, string>();
      edges.forEach(edge => {
        connectionMap.set(edge.source, edge.target);
      });
      
      // Check if START node has a connection
      if (!connectionMap.has('start-node')) {
        showNotification("Please connect the START node to the first task in your flow.", "error");
        return;
      }
      
      // Traverse and count connected nodes
      let currentNodeId = connectionMap.get('start-node');
      let connectedCount = 0;
      const visited = new Set<string>();
      
      while (currentNodeId && !visited.has(currentNodeId)) {
        visited.add(currentNodeId);
        connectedCount++;
        currentNodeId = connectionMap.get(currentNodeId);
      }
      
      // Check if all task nodes are connected in the chain
      if (connectedCount !== taskNodes.length) {
        showNotification(`Linear flow incomplete: ${connectedCount} of ${taskNodes.length} tasks are connected. Please connect all tasks in a single chain starting from START.`, "error");
        return;
      }
    }
    
    // Check for duplicate crew names
    try {
      const response = await getCrewsCrewGet();
      const allCrews = Array.isArray(response.data) ? response.data : response.data ? [response.data] : [];
      
      // Check if another crew with the same name exists (case-insensitive)
      const duplicateCrew = allCrews.find((crew: CrewRead) => 
        crew.name.trim().toLowerCase() === title.trim().toLowerCase() && crew.id !== cardId
      );
      
      if (duplicateCrew) {
        showNotification(`A crew with the name "${title}" already exists. Please choose a different name.`, "error");
        return;
      }
      
      // Proceed with create or update
      if (cardId) {
        // Update existing crew
        updateCrewMutation.mutate({ id: cardId, name: title });
      } else {
        // Create new crew
        createCrewMutation.mutate({ name: title });
      }
    } catch (error) {
      console.error("Error checking for duplicate crews:", error);
      showNotification("Failed to validate crew name. Please try again.", "error");
    }
  };

  const handleCancel = () => {
    router.push("/studio");
  };

  // Create crew run mutation
  const createCrewRunMutation = useMutation({
    mutationFn: async (crewId: string) => {
      const response = await fetch(`${client.getConfig().baseUrl}/crew-run/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          crew_id: crewId,
          output: null,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to create crew run');
      }
      
      return response.json();
    },
    onSuccess: async () => {
      showNotification("Flow execution started! Run created successfully.", "success");
      
      // Refetch crew data to get updated crew_runs
      const cardId = searchParams.get("id");
      if (cardId) {
        try {
          const response = await getCrewsCrewGet({ 
            query: { crew_id: cardId }
          });
          
          const crewData = response.data;
          if (crewData && !Array.isArray(crewData)) {
            const crewDataWithRuns = crewData as CrewRead & { crew_runs?: any[] };
            if (crewDataWithRuns.crew_runs) {
              setCrewRuns(crewDataWithRuns.crew_runs);
              // Force refresh of runs history display
              setRunsRefreshKey(prev => prev + 1);
            }
          }
        } catch (error) {
          console.error("Failed to refresh crew runs:", error);
        }
      }
    },
    onError: (error: Error) => {
      showNotification(`Failed to create crew run: ${error.message}`, "error");
    },
  });

  const handleRun = () => {
    const cardId = searchParams.get("id");
    if (!cardId) {
      showNotification("Cannot run flow: No crew ID found", "error");
      return;
    }
    
    createCrewRunMutation.mutate(cardId);
  };

  const handleModeChange = (newMode: "edit" | "view") => {
    if (mode === newMode) return;
    
    if (hasUnsavedChanges) {
      setPendingMode(newMode);
      setShowUnsavedWarning(true);
    } else {
      setMode(newMode);
      // Save mode to localStorage
      const cardId = searchParams.get("id");
      if (cardId) {
        localStorage.setItem(`crew_mode_${cardId}`, newMode);
      }
      
      // Fit view when switching modes
      if (reactFlowInstance) {
        setTimeout(() => {
          reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
        }, 100);
      }
    }
  };

  const confirmModeChange = () => {
    // Revert to last saved state
    const revertedNodes = lastSavedNodes.map((node: Node) => ({
      ...node,
      data: {
        ...node.data,
        onChange: (field: string, value: string) => handleNodeDataChange(node.id, field, value),
        onDelete: () => handleDeleteNode(node.id),
      },
    }));
    
    setNodes(revertedNodes);
    setEdges(lastSavedEdges);
    setTitle(lastSavedTitle);
    setHasUnsavedChanges(false);
    
    if (pendingMode) {
      setMode(pendingMode);
      // Save mode to localStorage
      const cardId = searchParams.get("id");
      if (cardId) {
        localStorage.setItem(`crew_mode_${cardId}`, pendingMode);
      }
      
      // Fit view when switching modes
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

  const showNotification = (message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000); // Auto-hide after 4 seconds
  };

  const checkDuplicateTitle = (newTitle: string) => {
    const cardId = searchParams.get("id");
    const savedCards = localStorage.getItem("studio_cards");
    const cards = savedCards ? JSON.parse(savedCards) : [];
    const duplicate = cards.find((card: any) => 
      card.title.trim().toLowerCase() === newTitle.trim().toLowerCase() && card.id !== cardId
    );
    setHasDuplicateTitle(!!duplicate);
    return !!duplicate;
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Custom Notification */}
      {notification && (
        <div 
          className={`fixed top-20 right-6 z-50 px-6 py-4 rounded-lg shadow-lg border-2 animate-in slide-in-from-top-5 duration-300 ${
            notification.type === "success" 
              ? "bg-green-50 border-green-500 text-green-800" 
              : notification.type === "error"
              ? "bg-red-50 border-red-500 text-red-800"
              : "bg-blue-50 border-blue-500 text-blue-800"
          }`}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {notification.type === "success" ? "✅" : notification.type === "error" ? "❌" : "ℹ️"}
            </span>
            <span className="font-medium">{notification.message}</span>
            <button 
              onClick={() => setNotification(null)}
              className="ml-4 text-xl hover:opacity-70"
            >
              ✕
            </button>
          </div>
        </div>
      )}
      
      <main className="p-6">
        {/* Top Section with Title and Mode Toggle */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Crew Run History Button - Only in view mode */}
            {mode === "view" && (
              <Button
                onClick={() => {
                  setShowRunsHistory(!showRunsHistory);
                  // Close run details when hiding runs history
                  if (showRunsHistory) {
                    setSelectedRun(null);
                  }
                  // Fit view after toggling runs history to adjust for sidebar visibility
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
                      setHasUnsavedChanges(true);
                      checkDuplicateTitle(newTitle);
                    }}
                    onBlur={() => setIsEditingTitle(false)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") setIsEditingTitle(false);
                    }}
                    className={`text-4xl font-bold bg-transparent border-b-2 focus:outline-none pb-2 ${
                      hasDuplicateTitle ? "border-destructive" : "border-primary"
                    }`}
                    autoFocus
                    placeholder="Enter title..."
                    style={{ width: 'fit-content', minWidth: '300px' }}
                  />
                  {hasDuplicateTitle && (
                    <span className="text-sm text-destructive mt-1">
                      A crew with this title already exists
                    </span>
                  )}
                </div>
              ) : (
                <h1
                  onClick={() => mode === "edit" && setIsEditingTitle(true)}
                  className={`text-4xl font-bold pb-2 border-b-2 border-transparent inline-block ${
                    mode === "edit" 
                      ? "cursor-pointer hover:text-primary transition-colors hover:border-muted" 
                      : "cursor-default"
                  }`}
                >
                  {title || "Untitled"}
                </h1>
              )}
            </div>
          </div>
          
          {/* Mode Toggle */}
          <div className="flex gap-2 bg-card border border-border rounded-lg p-1">
            <Button
              onClick={() => handleModeChange("edit")}
              variant={mode === "edit" ? "default" : "ghost"}
              size="sm"
            >
              Edit Mode
            </Button>
            <Button
              onClick={() => handleModeChange("view")}
              variant={mode === "view" ? "default" : "ghost"}
              size="sm"
            >
              View Mode
            </Button>
          </div>
        </div>

        {/* Unsaved Changes Warning Modal */}
        {showUnsavedWarning && (
          <div 
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                cancelModeChange();
              }
            }}
          >
            <div className="bg-card border border-border rounded-lg p-6 w-full max-w-md mx-4">
              <h2 className="text-xl font-semibold mb-4">Unsaved Changes</h2>
              <p className="text-muted-foreground mb-6">
                You have unsaved changes. Do you want to discard them and switch modes?
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={cancelModeChange}
                  variant="secondary"
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={confirmModeChange}
                  variant="destructive"
                  className="flex-1"
                >
                  Discard Changes
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* React Flow Canvas with Sidebar */}
        <div className="mb-8 flex gap-4">
          {/* Node Palette Sidebar - Only show in edit mode */}
          {mode === "edit" && (
            <div className="w-64 flex-shrink-0 bg-[#1a1a1a] border-2 border-white rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-4 text-white">Node Types</h3>
              <div className="space-y-3">
                {nodeTypeConfigs.map((nodeType) => (
                  <div
                    key={nodeType.type}
                    draggable
                    onDragStart={(e) => onDragStart(e, nodeType.type)}
                    className="flex items-center gap-3 p-3 rounded-lg border-2 border-transparent hover:border-white cursor-move transition-colors bg-[#3a3a3a] hover:bg-[#2a2a2a]"
                  >
                    <span className="text-2xl">{nodeType.icon}</span>
                    <div>
                      <div className="font-medium text-sm text-white">{nodeType.label}</div>
                      <div className="text-xs text-gray-300">
                        Drag to canvas
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Runs History Sidebar - Only show in view mode when toggled */}
          {mode === "view" && showRunsHistory && (
            <div key={runsRefreshKey} className="w-96 flex-shrink-0 bg-[#1a1a1a] border-2 border-white rounded-lg p-4 overflow-y-auto max-h-[600px]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Your Runs</h3>
              </div>
              <div className="space-y-3">
                {crewRuns.length === 0 ? (
                  <div className="text-center text-white py-8">
                    No runs yet. Click "Run Flow" to execute this crew.
                  </div>
                ) : (
                  crewRuns.map((run: any, index: number) => (
                    <div
                      key={run.id}
                      className="p-4 border-2 border-transparent rounded-lg hover:border-white transition-colors cursor-pointer bg-[#3a3a3a] hover:bg-[#2a2a2a]"
                      onClick={() => {
                        setSelectedRun(run);
                      }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="font-semibold text-sm mb-1 text-white">
                            Run #{crewRuns.length - index}
                          </div>
                          <div className="text-xs text-gray-300">
                            {run.id}
                          </div>
                        </div>
                      </div>
                      <div className="text-sm space-y-2">
                        {run.output && (
                          <div className="mt-3 pt-3 border-t border-white">
                            <div className="text-xs text-gray-300 mb-1">Output Preview:</div>
                            <div className="text-xs bg-[#1a1a1a] text-white p-2 rounded max-h-20 overflow-hidden">
                              {JSON.stringify(run.output).substring(0, 100)}
                              {JSON.stringify(run.output).length > 100 && '...'}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="mt-3 text-xs text-white">
                        Click to view full details →
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* React Flow Canvas */}
          <div className="flex-1 flex flex-col gap-4">
            {/* Selected Run Details Card - Only show when a run is selected */}
            {selectedRun && mode === "view" && (
              <div className="bg-[#1a1a1a] border-2 border-white rounded-lg p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                      Run Details - #{crewRuns.findIndex(r => r.id === selectedRun.id) !== -1 ? crewRuns.length - crewRuns.findIndex(r => r.id === selectedRun.id) : 'N/A'}
                    </h3>
                    <p className="text-sm text-gray-300">ID: {selectedRun.id}</p>
                  </div>
                  <Button
                    onClick={() => setSelectedRun(null)}
                    variant="secondary"
                    className="bg-white text-black hover:bg-gray-200"
                  >
                    Close
                  </Button>
                </div>
                
                {/* Output Section */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-white mb-3">Output</h4>
                  <div className="bg-[#2a2a2a] border border-white rounded-lg p-4 max-h-60 overflow-y-auto">
                    {selectedRun.output ? (
                      <pre className="text-sm text-white whitespace-pre-wrap font-mono">
                        {JSON.stringify(selectedRun.output, null, 2)}
                      </pre>
                    ) : (
                      <p className="text-gray-300">No output available</p>
                    )}
                  </div>
                </div>
                
                {/* Artifacts Section */}
                <div>
                  <h4 className="text-lg font-semibold text-white mb-3">Artifacts</h4>
                  <div className="bg-[#2a2a2a] border border-white rounded-lg p-4">
                    {selectedRun.artifacts && selectedRun.artifacts.length > 0 ? (
                      <div className="space-y-2">
                        {selectedRun.artifacts.map((artifact: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-[#3a3a3a] rounded">
                            <div>
                              <p className="text-white font-medium">{artifact.file_name || 'Unnamed artifact'}</p>
                              <p className="text-xs text-gray-300">{artifact.type}</p>
                            </div>
                            <span className="text-xs text-gray-400">{artifact.id}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-300">No artifacts available</p>
                    )}
                  </div>
                </div>
              </div>
            )}
            
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
              onInit={setReactFlowInstance}
              fitView
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
              <Button
                onClick={handleCancel}
                variant="secondary"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={!hasUnsavedChanges}
                variant="default"
              >
                Save Changes
              </Button>
            </>
          ) : (
            <Button
              onClick={handleRun}
              variant="default"
            >
              Run Flow
            </Button>
          )}
        </div>
      </main>
    </div>
  );
}
