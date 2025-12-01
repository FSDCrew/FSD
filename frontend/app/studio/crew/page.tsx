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
import { getRequiredInputsCrewCrewIdRequiredInputsGet, crewKickoffCrewKickoffPost, type RequiredInputField, type RequiredInputsResponse } from "@/lib/api/crew";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { CalendarIcon, Minus } from "lucide-react";
import { format } from "date-fns";
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
  connectable: true,
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
  const [isLoadingTasks, setIsLoadingTasks] = useState(true);
  const [requiredInputs, setRequiredInputs] = useState<RequiredInputField[]>([]);
  const [isLoadingRequiredInputs, setIsLoadingRequiredInputs] = useState(false);
  const [kickoffDialogOpen, setKickoffDialogOpen] = useState(false);
  const [dynamicFormData, setDynamicFormData] = useState<Record<string, any>>({});
  const [orshotSchemaFields, setOrshotSchemaFields] = useState<Array<{field: string, dataType: string, description: string}>>([{field: "", dataType: "", description: ""}]);
  
  
  const nodeTypes = React.useMemo(() => createNodeTypes(nodeTypeConfigs), [nodeTypeConfigs]);
  const [selectedRun, setSelectedRun] = useState<any | null>(null);
  
  // Fetch required inputs when dialog is opened
  const fetchRequiredInputs = useCallback(async () => {
    const crewId = searchParams.get("id");
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
        // Initialize form data with empty values
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
  }, [searchParams]);

  const handleKickoffDialogOpen = (open: boolean) => {
    setKickoffDialogOpen(open);
    if (open) {
      fetchRequiredInputs();
    }
  };

  const handleDynamicFormChange = (fieldName: string, value: any) => {
    setDynamicFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const onKickoffSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const crewId = searchParams.get("id");
    if (!crewId) {
      toast.error("No crew ID found");
      return;
    }
    
    // Validate required fields
    const missingFields = requiredInputs
      .filter(field => field.required && !dynamicFormData[field.field_name])
      .map(field => field.field_name);
    
    if (missingFields.length > 0) {
      toast.error(`Please fill in required fields: ${missingFields.join(", ")}`);
      return;
    }
    
    // Transform orshot_schema if it exists
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
        setKickoffDialogOpen(false);
        
        // Refresh crew runs
        try {
          const crewResponse = await getCrewByIdCrewCrewIdGet({ 
            path: { crew_id: crewId }
          });
          
          const crewData = crewResponse.data;
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
    } catch (error) {
      console.error("Error starting crew run:", error);
      toast.error("Failed to start crew run. Please try again.");
    }
  };
  
  useEffect(() => {
    const fetchPreDefinedTasks = async () => {
      console.log('Fetching pre-defined tasks...');
      setIsLoadingTasks(true);
      try {
        const response = await fetch('http://localhost:8001/tasks/pre-defined');
        console.log('Response status:', response.status);
        if (response.ok) {
          const tasks: PreDefinedTask[] = await response.json();
          console.log('Fetched tasks:', tasks);
          setPreDefinedTasks(tasks); 
          const configs = tasks.map((task) => ({
            type: task.key,
            name: task.name,
            color: getTaskColor(task.key), 
            description: task.task_description
          }));
          console.log('Setting node configs:', configs);
          setNodeTypeConfigs(configs);
        } else {
          console.error('Failed to fetch pre-defined tasks');
          setNodeTypeConfigs([]);
        }
      } catch (error) {
        console.error('Error fetching pre-defined tasks:', error);
        setNodeTypeConfigs([]);
      } finally {
        setIsLoadingTasks(false);
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
        toast.error("The START node cannot receive connections. It's the beginning of the flow.");
        return;
      }
      // Check if source node already has an outgoing connection (all nodes including start node can only have ONE outgoing connection)
      const sourceHasConnection = edges.some(edge => edge.source === params.source);
      // Check if target node already has an incoming connection
      const targetHasConnection = edges.some(edge => edge.target === params.target);
      if (sourceHasConnection) {
        toast.error("This node already has an outgoing connection. Each node can only connect to one other node for linear flow.");
        return;
      }
      if (targetHasConnection) {
        toast.error("The target node already has an incoming connection. Each node can only receive one connection for linear flow.");
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
      toast.error("Crew created but no data returned");
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
        toast.error("Crew created but failed to save tasks");
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
    toast.success("Crew created successfully!");
  },

  onError: (error) => {
    console.error("Error creating crew:", error);
    toast.error("Failed to create crew. Please try again.");
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
    toast.success("Crew updated successfully!");
  },
  
  onError: (error) => {
    console.error("Error updating crew:", error);
    toast.error("Failed to update crew. Please try again.");
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
      toast.error("The START node cannot be deleted.");
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

      if (!reactFlowInstance) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const nodeTypeConfig = nodeTypeConfigs.find((n) => n.type === type);
      if (!nodeTypeConfig) return;

      const existingNode = nodes.find(n => {
        const nodeData = n.data as NodeData;
        return nodeData.taskType === type && n.id !== 'start-node';
      });
      if (existingNode) {
        toast.error(`Task "${nodeTypeConfig.name}" is already on the canvas. Each task type can only be added once.`);
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
        connectable: true,
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
                connectable: true,
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
              connectable: true,
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
      toast.error("Crew name cannot be empty");
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
        toast.error("Please connect the START node to the first task in your flow.");
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
        toast.error(`Linear flow incomplete: ${connectedCount} of ${taskNodes.length} tasks are connected. Please connect all tasks in a single chain starting from START.`);
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
        toast.error(`A crew with the name "${title}" already exists. Please choose a different name.`);
        return;
      }
      
      if (cardId) {
        updateCrewMutation.mutate({ id: cardId, name: title });
      } else {
        createCrewMutation.mutate({ name: title });
      }
    } catch (error) {
      console.error("Error checking for duplicate crews:", error);
      toast.error("Failed to validate crew name. Please try again.");
    }
  };

  const handleCancel = () => {
    router.push("/studio");
  };

  const handleDiscardChanges = () => {
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
      toast.success("Flow execution started! Run created successfully.");
      
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
      toast.error(`Failed to create crew run: ${error.message}`);
    },
  });

  const handleRun = () => {
    const cardId = searchParams.get("id");
    if (!cardId) {
      toast.error("Cannot run flow: No crew ID found");
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
        <AlertDialog open={showUnsavedWarning} onOpenChange={setShowUnsavedWarning}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Unsaved Changes</AlertDialogTitle>
              <AlertDialogDescription>
                You have unsaved changes. Do you want to discard them and switch modes?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={cancelModeChange}>Cancel</AlertDialogCancel>
              <AlertDialogAction 
                onClick={confirmModeChange}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Discard Changes
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* React Flow Canvas with Sidebar */}
        <div className="mb-8 flex gap-4">
          {/* Node Palette Sidebar - Only show in edit mode */}
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
                  <div className="text-center text-white py-8">
                    {isLoadingTasks ? "Loading node types..." : "No node types available"}
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
              {hasUnsavedChanges ? (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="secondary">
                      Cancel
                    </Button>
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
                      <AlertDialogAction 
                        onClick={handleDiscardChanges}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        Discard Changes
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              ) : (
                <Button
                  onClick={handleCancel}
                  variant="secondary"
                >
                  Cancel
                </Button>
              )}
              <Button
                onClick={handleSave}
                disabled={!hasUnsavedChanges}
                variant="default"
              >
                Save Changes
              </Button>
            </>
          ) : (
            <Dialog open={kickoffDialogOpen} onOpenChange={handleKickoffDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">Prepare Kickoff</Button>
              </DialogTrigger>
              <DialogContent className="max-w-[95vw] w-full sm:max-w-[90vw] lg:max-w-[800px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Required Inputs for Kickoff</DialogTitle>
                </DialogHeader>
                {isLoadingRequiredInputs ? (
                  <div className="flex justify-center items-center py-8">
                    <div className="text-gray-500">Loading form...</div>
                  </div>
                ) : (
                  <form onSubmit={onKickoffSubmit} className="space-y-4">
                    {requiredInputs.map((field) => {
                      const typeInfo = field.type_info as any;
                      
                      // Handle orshot_schema as a special case with dynamic rows
                      if (field.field_name === "orshot_schema" && typeInfo.is_list) {
                        return (
                          <div key={field.field_name} className="space-y-3">
                            <Label>
                              {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                              {field.required && <span className="text-red-500 ml-1">*</span>}
                            </Label>
                            {orshotSchemaFields.map((schemaField, index) => (
                              <div key={index} className="flex gap-2 items-start">
                                <div className="flex-1">
                                  <Label className="text-xs">Field</Label>
                                  <Input
                                    placeholder="e.g., headline"
                                    value={schemaField.field}
                                    onChange={(e) => {
                                      const newFields = [...orshotSchemaFields];
                                      newFields[index].field = e.target.value;
                                      setOrshotSchemaFields(newFields);
                                    }}
                                  />
                                </div>
                                <div className="w-[160px]">
                                  <Label className="text-xs">Data Type</Label>
                                  <Select
                                    value={schemaField.dataType}
                                    onValueChange={(value) => {
                                      const newFields = [...orshotSchemaFields];
                                      newFields[index].dataType = value;
                                      setOrshotSchemaFields(newFields);
                                    }}
                                  >
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="TEXT">TEXT</SelectItem>
                                      <SelectItem value="IMAGE">IMAGE</SelectItem>
                                      <SelectItem value="BACKGROUND">BACKGROUND</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                                <div className="flex-1">
                                  <Label className="text-xs">Description</Label>
                                  <Textarea
                                    placeholder="e.g., Main title"
                                    value={schemaField.description}
                                    onChange={(e) => {
                                      const newFields = [...orshotSchemaFields];
                                      newFields[index].description = e.target.value;
                                      setOrshotSchemaFields(newFields);
                                    }}
                                    rows={3}
                                    className="resize-y"
                                  />
                                </div>
                                <div className="flex items-center pt-6">
                                  <Button
                                    type="button"
                                    variant="destructive"
                                    size="icon"
                                    className={`h-8 w-8 rounded-full flex-shrink-0 bg-gray-600 ${index === 0 ? 'invisible' : ''}`}
                                    onClick={() => {
                                      const newFields = orshotSchemaFields.filter((_, i) => i !== index);
                                      setOrshotSchemaFields(newFields);
                                    }}
                                  >
                                    <Minus className="h-4 w-4" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setOrshotSchemaFields([...orshotSchemaFields, {field: "", dataType: "", description: ""}]);
                              }}
                            >
                              + Add Row
                            </Button>
                          </div>
                        );
                      }
                      
                      // Handle enum fields (like templateId)
                      if (typeInfo.is_enum && typeInfo.enum_values) {
                        // If it's a list of enums, allow multiple selections
                        if (typeInfo.is_list) {
                          const selectedValues = dynamicFormData[field.field_name] || [];
                          
                          return (
                            <div key={field.field_name} className="space-y-2">
                              <Label>
                                {field.field_name === "templateId" 
                                  ? "Template Id" 
                                  : field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                                {field.required && <span className="text-red-500 ml-1">*</span>}
                              </Label>
                              <div className="flex flex-wrap gap-2">
                                {typeInfo.enum_values.map((value: any) => {
                                  const isSelected = selectedValues.includes(value);
                                  return (
                                    <Button
                                      key={String(value)}
                                      type="button"
                                      variant={isSelected ? "default" : "outline"}
                                      size="sm"
                                      onClick={() => {
                                        const newValues = isSelected
                                          ? selectedValues.filter((v: any) => v !== value)
                                          : [...selectedValues, value];
                                        handleDynamicFormChange(field.field_name, newValues);
                                      }}
                                    >
                                      {String(value)}
                                    </Button>
                                  );
                                })}
                              </div>
                              {selectedValues.length > 0 && (
                                <div className="text-sm text-muted-foreground">
                                  Selected: {selectedValues.join(", ")}
                                </div>
                              )}
                            </div>
                          );
                        }
                        
                        // Single enum selection
                        return (
                          <div key={field.field_name} className="space-y-2">
                            <Label>
                              {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                              {field.required && <span className="text-red-500 ml-1">*</span>}
                            </Label>
                            <Select
                              value={dynamicFormData[field.field_name] ? String(dynamicFormData[field.field_name]) : ""}
                              onValueChange={(value) => handleDynamicFormChange(field.field_name, value)}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder={field.placeholder || `Select ${field.field_name}`} />
                              </SelectTrigger>
                              <SelectContent>
                                {typeInfo.enum_values.map((value: any) => (
                                  <SelectItem key={String(value)} value={String(value)}>
                                    {String(value)}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        );
                      }
                      
                      // Handle date fields
                      if (typeInfo.type === 'date' || field.field_name.includes('date')) {
                        return (
                          <div key={field.field_name} className="space-y-2">
                            <Label>
                              {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                              {field.required && <span className="text-red-500 ml-1">*</span>}
                            </Label>
                            <Popover>
                              <PopoverTrigger asChild>
                                <Button
                                  variant="outline"
                                  className={`w-full justify-start text-left font-normal ${
                                    !dynamicFormData[field.field_name] && "text-muted-foreground"
                                  }`}
                                >
                                  <CalendarIcon className="mr-2 h-4 w-4" />
                                  {dynamicFormData[field.field_name] ? (
                                    format(new Date(dynamicFormData[field.field_name]), "PPP")
                                  ) : (
                                    <span>Select date</span>
                                  )}
                                </Button>
                              </PopoverTrigger>
                              <PopoverContent className="w-auto p-0" align="start">
                                <Calendar
                                  mode="single"
                                  selected={dynamicFormData[field.field_name] ? new Date(dynamicFormData[field.field_name]) : undefined}
                                  onSelect={(date) => {
                                    if (date) {
                                      handleDynamicFormChange(field.field_name, date.toISOString());
                                    }
                                  }}
                                  captionLayout="dropdown"
                                  fromYear={2020}
                                  toYear={2030}
                                  initialFocus
                                />
                              </PopoverContent>
                            </Popover>
                          </div>
                        );
                      }
                      
                      // Handle basic string fields
                      return (
                        <div key={field.field_name} className="space-y-2">
                          <Label>
                            {field.field_name.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                            {field.required && <span className="text-red-500 ml-1">*</span>}
                          </Label>
                          <Textarea
                            placeholder={field.placeholder || `Enter ${field.field_name}`}
                            value={dynamicFormData[field.field_name] || ""}
                            onChange={(e) => handleDynamicFormChange(field.field_name, e.target.value)}
                            rows={3}
                          />
                        </div>
                      );
                    })}
                    
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button type="button" variant="outline">Cancel</Button>
                      </DialogClose>
                      <Button type="submit">Kickoff!</Button>
                    </DialogFooter>
                  </form>
                )}
              </DialogContent>
            </Dialog>
          )}
        </div>
      </main>
    </div>
  );
}
