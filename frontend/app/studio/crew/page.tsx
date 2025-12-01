"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import StartNode from "@/components/StartNode";
import CustomNode from "@/components/CustomNode";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
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
import { createCrewCrewPost, updateCrewCrewPut, getCrewByIdCrewCrewIdGet, getAllCrewsCrewGet, replaceAllTasksForCrewTaskCrewIdSavePut, type CrewRead, type TaskCreate } from "@/lib/api/crud";
import { client } from "@/lib/api/crud/client.gen";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"


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
// UPDATE THIS WHEN MORE TASKS KEYS ARE ADDED!
const taskColorMap: Record<string, string> = {
  marketing_research: "#c878e0ff",
  content_strategy: "#389e7eff",
  social_media_schedule: "#cc6262ff", 
};

const getTaskColor = (taskKey: string): string => {
  return taskColorMap[taskKey] || "#6B7280"; // default 
};

const kickoffFormSchema = z.object({
  theme: z.string().min(1, { message: "Theme is required" }),
  brandDescription: z.string().min(1, { message: "Brand description is required" }),
  targetAudience: z.string().min(1, { message: "Target audience is required" }),
  templateId: z.string().min(1, { message: "Template ID is required" }),
  orshotField: z.string().min(1, { message: "Orshot field is required" }),
  orshotDataType: z.string().min(1, { message: "Data type is required" }),
  orshotDescription: z.string().min(1, { message: "Description is required" }),
});

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

interface NodeData extends Record<string, unknown> {
  label: string;
  taskType: string;
  onChange?: (field: string, value: string) => void;
  onDelete?: () => void;
}

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
  const [hoveredNodeType, setHoveredNodeType] = useState<string | null>(null);
  const [nodeTypeConfigs, setNodeTypeConfigs] = useState<NodeTypeConfig[]>([]);
  const [preDefinedTasks, setPreDefinedTasks] = useState<PreDefinedTask[]>([]);
  
  
  const nodeTypes = React.useMemo(() => createNodeTypes(nodeTypeConfigs), [nodeTypeConfigs]);
  const [selectedRun, setSelectedRun] = useState<any | null>(null);
  const [notification, setNotification] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);
  
  // Initialize kickoff form
  const kickoffForm = useForm<z.infer<typeof kickoffFormSchema>>({
    resolver: zodResolver(kickoffFormSchema),
    defaultValues: {
      theme: "",
      brandDescription: "",
      targetAudience: "",
      templateId: "",
      orshotField: "",
      orshotDataType: "",
      orshotDescription: "",
    },
  });

  function onKickoffSubmit(values: z.infer<typeof kickoffFormSchema>) {
    console.log("Kickoff form values:", values);
    showNotification("Kickoff started successfully!", "success");
    handleRun();
    kickoffForm.reset();
  }
  
  useEffect(() => {
    const fetchPreDefinedTasks = async () => {
      try {
        const response = await fetch('http://localhost:8001/tasks/pre-defined');
        if (response.ok) {
          const tasks: PreDefinedTask[] = await response.json();
          setPreDefinedTasks(tasks); 
          const configs = tasks.map((task) => ({
            type: task.key,
            name: task.name,
            color: getTaskColor(task.key), 
            description: task.task_description
          }));
          setNodeTypeConfigs(configs);
        } else {
          console.error('Failed to fetch pre-defined tasks');
          setNodeTypeConfigs([]);
        }
      } catch (error) {
        console.error('Error fetching pre-defined tasks:', error);
        setNodeTypeConfigs([]);
      }
    };

    fetchPreDefinedTasks();
  }, []);

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
    const hasPositionChange = changes.some(change => change.type === 'position' && change.dragging === false);
    if (hasPositionChange) {
      setHasUnsavedChanges(true);
    }
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

//convert nodes to ordered predefined tasks for backend
const convertNodesToOrderedTasks = (nodes: Node[], edges: Edge[]) => {
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
    // Find the original predefined task using taskType from node data
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
};

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
    if (nodes.length > 0) {
      try {
        const tasks = convertNodesToOrderedTasks(nodes, edges);
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
    setLastSavedNodes(nodes);
    setLastSavedEdges(edges);
    setLastSavedTitle(title);
    setHasUnsavedChanges(false);
    
    
    queryClient.invalidateQueries({ queryKey: ['crews'] });
    router.push(`/studio/crew?id=${crewData.id}&title=${encodeURIComponent(crewData.name)}`);
    showNotification("Crew created successfully!", "success");
  },

  onError: (error) => {
    console.error("Error creating crew:", error);
    showNotification("Failed to create crew. Please try again.", "error");
  }
});


const updateCrewMutation = useMutation({
  mutationFn: async (crewData: { id: string; name: string }) => {
    
    await updateCrewCrewPut({ body: crewData });
    
    const tasks = convertNodesToOrderedTasks(nodes, edges);
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
    setLastSavedNodes(nodes);
    setLastSavedEdges(edges);
    setLastSavedTitle(title);
    setHasUnsavedChanges(false);
    queryClient.invalidateQueries({ queryKey: ['crews'] });
    showNotification("Crew updated successfully!", "success");
  },
  
  onError: (error) => {
    console.error("Error updating crew:", error);
    showNotification("Failed to update crew. Please try again.", "error");
  }
});

  const handleNodeDataChange = useCallback((nodeId: string, field: string, value: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          const currentData = node.data as NodeData;
          
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

  
  const handleDeleteNode = useCallback((nodeId: string) => {
    if (nodeId === 'start-node') {
      showNotification("The START node cannot be deleted.", "error");
      return;
    }
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    setHasUnsavedChanges(true);
  }, [setNodes, setEdges]);
  const onNodesDelete = useCallback((deleted: Node[]) => {
    deleted.forEach((node) => handleDeleteNode(node.id));
  }, [handleDeleteNode]);

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
      if (!type) return;

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      };

      const nodeTypeConfig = nodeTypeConfigs.find((n) => n.type === type);
      if (!nodeTypeConfig) return;

      const existingNode = nodes.find(n => {
        const nodeData = n.data as NodeData;
        return nodeData.taskType === type && n.id !== 'start-node';
      });
      if (existingNode) {
        showNotification(`Task "${nodeTypeConfig.name}" is already on the canvas. Each task type can only be added once.`, "error");
        return;
      }

      const nodeId = type; 
      
      const newNode: Node = {
        id: nodeId,
        type: type,
        position,
        data: {
          label: nodeTypeConfig.name,
          taskType: type,
          onChange: (field: string, value: string) => handleNodeDataChange(nodeId, field, value),
          onDelete: () => handleDeleteNode(nodeId),
        } as NodeData,
        style: {
          background: getTaskColor(type),
          color: "white",
          border: "2px solid #222",
          borderRadius: "8px",
          minWidth: "120px",
        },
      };

      setNodes((nds) => nds.concat(newNode));
      setHasUnsavedChanges(true);
    },
    [setNodes, handleNodeDataChange, handleDeleteNode, nodeTypeConfigs, nodes]
  );



  const { isAuthenticated, token } = useAuth();

  useEffect(() => {
    if (!token) router.push("/auth/login");

    const cardTitle = searchParams.get("title") || "Untitled";
    const cardDescription = searchParams.get("description") || "";
    const cardId = searchParams.get("id");

    setTitle(cardTitle);
    setDescription(cardDescription);
    setLastSavedTitle(cardTitle);

    if (cardId && nodeTypeConfigs.length > 0) {
      const savedMode = localStorage.getItem(`crew_mode_${cardId}`);
      if (savedMode === "view" || savedMode === "edit") {
        setMode(savedMode);
      }
      
      const loadCrewData = async () => {
        try {
          const response = await getCrewByIdCrewCrewIdGet({
            path: { crew_id: cardId }
          });
          
          const crewData = response.data;
          if (crewData && crewData.tasks) {
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
              const nodeTypeConfig = nodeTypeConfigs.find((n) => n.type === task.key);
              
              const defaultPosition = { 
                x: 300 + (index * 300), 
                y: 250                    
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
                } as NodeData,
                style: {
                  background: getTaskColor(task.key),
                  color: "white",
                  border: "2px solid #222",
                  borderRadius: "8px",
                  minWidth: "120px",
                },
              } as Node;
            });
            
            // Reconstruct edges based on task order
            const reconstructedEdges: Edge[] = [];
            if (sortedTasks.length > 0) {
              reconstructedEdges.push({
                id: `start-node-${sortedTasks[0].key}`,
                source: 'start-node',
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
              position: savedPositions['start-node'] || START_NODE.position,
            };
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

    if (cardTitle === "Untitled") {
      setIsEditingTitle(true);
    }
  }, [router, searchParams, setNodes, setEdges, nodeTypeConfigs]);

  // Fit view when ReactFlow instance is ready and nodes are loaded
  useEffect(() => {
    if (reactFlowInstance && nodes.length > 1) { 
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
      }, 100);
    }
  }, [reactFlowInstance, nodes.length]);

  const handleSave = async () => {
    const cardId = searchParams.get("id");
    
    if (!title || title.trim() === "") {
      showNotification("Crew name cannot be empty", "error");
      return;
    }
    
    // Validate linear flow: Check if nodes form a single connected chain from START
    const taskNodes = nodes.filter(n => n.id !== 'start-node');
    if (taskNodes.length > 0) {
      const connectionMap = new Map<string, string>();
      edges.forEach(edge => {
        connectionMap.set(edge.source, edge.target);
      });
      
      if (!connectionMap.has('start-node')) {
        showNotification("Please connect the START node to the first task in your flow.", "error");
        return;
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
        showNotification(`Linear flow incomplete: ${connectedCount} of ${taskNodes.length} tasks are connected. Please connect all tasks in a single chain starting from START.`, "error");
        return;
      }
    }
    try {
      const response = await getAllCrewsCrewGet();
      const allCrews = Array.isArray(response.data) ? response.data : response.data ? [response.data] : [];
      
      const duplicateCrew = allCrews.find((crew: CrewRead) => 
        crew.name.trim().toLowerCase() === title.trim().toLowerCase() && crew.id !== cardId
      );
      
      if (duplicateCrew) {
        showNotification(`A crew with the name "${title}" already exists. Please choose a different name.`, "error");
        return;
      }
      
      if (cardId) {
        updateCrewMutation.mutate({ id: cardId, name: title });
      } else {
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
      
      const cardId = searchParams.get("id");
      if (cardId) {
        try {
          const response = await getCrewByIdCrewCrewIdGet({ 
            path: { crew_id: cardId }
          });
          
          const crewData = response.data;
          if (crewData) {
            const crewDataWithRuns = crewData as CrewRead & { crew_runs?: any[] };
            if (crewDataWithRuns.crew_runs) {
              setCrewRuns(crewDataWithRuns.crew_runs);
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
    setTimeout(() => setNotification(null), 4000); 
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
            <div className="w-64 flex-shrink-0 bg-[#1a1a1a] border-2 border-white rounded-lg p-4 relative">
              <h3 className="text-lg font-semibold mb-2 text-white">Node Types</h3>
              <p className="text-xs text-gray-300 mb-4">Drag to canvas</p>
              
              <div className="space-y-3">
                {nodeTypeConfigs.length > 0 ? (
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
                  <div className="text-center text-white py-8">
                    Loading node types...
                  </div>
                )}
              </div>
              
              {/* Hover Card */}
              {hoveredNodeType && (
                <div 
                  className="absolute left-full top-0 ml-4 w-80 border-2 border-white rounded-lg p-4 shadow-lg z-50"
                  style={{
                    backgroundColor: getTaskColor(hoveredNodeType)
                  }}
                >
                  {(() => {
                    const nodeType = nodeTypeConfigs.find(n => n.type === hoveredNodeType);
                    if (!nodeType) return null;
                    return (
                      <>
                        <h4 className="font-semibold text-white mb-2">{nodeType.name}</h4>
                        <p className="text-sm text-white leading-relaxed opacity-90">
                          {nodeType.description}
                        </p>
                      </>
                    );
                  })()}
                </div>
              )}
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
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="outline">Kickoff</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[800px]">
                <DialogHeader>
                  <DialogTitle>Required Inputs for Kickoff</DialogTitle>
                </DialogHeader>
                <Form {...kickoffForm}>
                  <form onSubmit={kickoffForm.handleSubmit(onKickoffSubmit)} className="space-y-4">
                    <FormField
                      control={kickoffForm.control}
                      name="theme"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Theme</FormLabel>
                          <FormControl>
                            <Textarea placeholder="Type your theme here." {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={kickoffForm.control}
                      name="brandDescription"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Brand Description</FormLabel>
                          <FormControl>
                            <Textarea placeholder="Type your brand description here." {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={kickoffForm.control}
                      name="targetAudience"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Target Audience</FormLabel>
                          <FormControl>
                            <Textarea placeholder="Type your target audience here." {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={kickoffForm.control}
                      name="templateId"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Template ID</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Select template" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="1201">1201</SelectItem>
                              <SelectItem value="1909">1909</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <div className="space-y-3">
                      <Label className="text-base font-semibold">Orshot Schema</Label>
                      <div className="flex gap-2 items-start">
                        <FormField
                          control={kickoffForm.control}
                          name="orshotField"
                          render={({ field }) => (
                            <FormItem className="flex-1">
                              <FormLabel className="text-xs">Field</FormLabel>
                              <FormControl>
                                <Textarea placeholder="Type your field here." className="min-h-[60px]" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={kickoffForm.control}
                          name="orshotDataType"
                          render={({ field }) => (
                            <FormItem className="flex-1">
                              <FormLabel className="text-xs">Data Type</FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-full h-[60px]">
                                    <SelectValue placeholder="Select type" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  <SelectItem value="image">IMAGE</SelectItem>
                                  <SelectItem value="text">TEXT</SelectItem>
                                  <SelectItem value="background">BACKGROUND</SelectItem>
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={kickoffForm.control}
                          name="orshotDescription"
                          render={({ field }) => (
                            <FormItem className="flex-1">
                              <FormLabel className="text-xs">Description</FormLabel>
                              <FormControl>
                                <Textarea placeholder="Type your description here." className="min-h-[60px]" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    </div>
                    
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button type="button" variant="outline">Cancel</Button>
                      </DialogClose>
                      <Button type="submit">Kickoff!</Button>
                    </DialogFooter>
                  </form>
                </Form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </main>
    </div>
  );
}
