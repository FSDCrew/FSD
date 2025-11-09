"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import ResearchNode from "@/components/ResearchNode";
import CopywritingNode from "@/components/CopywritingNode";
import CanvaDesignNode from "@/components/CanvaDesignNode";
import SurveyNode from "@/components/SurveyNode";
import SchedulerNode from "@/components/SchedulerNode";
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

const nodeTypes = {
  research: ResearchNode,
  copywriting: CopywritingNode,
  "canva design": CanvaDesignNode,
  survey: SurveyNode,
  scheduler: SchedulerNode,
};

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

type TaskType = "research" | "copywriting" | "canva design" | "survey" | "scheduler";

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
    color: "#3b82f6",
    icon: "🔍",
  },
  {
    type: "copywriting" as TaskType,
    label: "Copywriting Node",
    color: "#8b5cf6",
    icon: "✍️",
  },
  {
    type: "canva design" as TaskType,
    label: "Canva Design Node",
    color: "#ec4899",
    icon: "🎨",
  },
  {
    type: "survey" as TaskType,
    label: "Survey Node",
    color: "#10b981",
    icon: "📊",
  },
  {
    type: "scheduler" as TaskType,
    label: "Scheduler Node",
    color: "#f59e0b",
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
  const [notification, setNotification] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);
  
  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Keep track of last saved state for reverting
  const [lastSavedNodes, setLastSavedNodes] = useState<Node[]>(initialNodes);
  const [lastSavedEdges, setLastSavedEdges] = useState<Edge[]>(initialEdges);
  const [lastSavedTitle, setLastSavedTitle] = useState("");

  const onConnect = useCallback(
    (params: Connection) => {
      // Check if source node already has an outgoing connection
      const sourceHasConnection = edges.some(edge => edge.source === params.source);
      
      // Check if target node already has an incoming connection
      const targetHasConnection = edges.some(edge => edge.target === params.target);
      
      if (sourceHasConnection) {
        showNotification("This node already has an outgoing connection. Each node can only connect to one other node.", "error");
        return;
      }
      
      if (targetHasConnection) {
        showNotification("The target node already has an incoming connection. Each node can only receive one connection.", "error");
        return;
      }
      
      setEdges((eds) => addEdge(params, eds));
      setHasUnsavedChanges(true);
    },
    [edges, setEdges]
  );

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
            type === "canva design"
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



  useEffect(() => {
    const token = localStorage.getItem("fsd_token");
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
    }

    // Load saved nodes and edges if editing existing card
    if (cardId) {
      const savedCards = localStorage.getItem("studio_cards");
      if (savedCards) {
        const cards = JSON.parse(savedCards);
        const card = cards.find((c: any) => c.id === cardId);
        if (card) {
          if (card.nodes) {
            // Re-attach onChange and onDelete handlers to loaded nodes
            const nodesWithHandlers = card.nodes.map((node: Node) => ({
              ...node,
              data: {
                ...node.data,
                onChange: (field: string, value: string) => handleNodeDataChange(node.id, field, value),
                onDelete: () => handleDeleteNode(node.id),
              },
            }));
            setNodes(nodesWithHandlers);
            setLastSavedNodes(nodesWithHandlers);
          }
          if (card.edges) {
            setEdges(card.edges);
            setLastSavedEdges(card.edges);
          }
        }
      }
    }

    // If it's a new card (Untitled), start editing the title immediately
    if (cardTitle === "Untitled") {
      setIsEditingTitle(true);
    }
  }, [router, searchParams, setNodes, setEdges]);

  const handleSave = () => {
    // Save the card data back to localStorage or your backend
    const cardId = searchParams.get("id");
    
    // Check for duplicate titles
    const savedCards = localStorage.getItem("studio_cards");
    const cards = savedCards ? JSON.parse(savedCards) : [];
    const duplicateTitle = cards.find((card: any) => 
      card.title.trim().toLowerCase() === title.trim().toLowerCase() && card.id !== cardId
    );
    
    if (duplicateTitle) {
      showNotification(`A crew with the title "${title}" already exists. Please choose a different title.`, "error");
      return;
    }
    
    const cardData = {
      title,
      description,
      nodes,
      edges,
    };
    
    if (cardId) {
      // Update existing card
      if (savedCards) {
        const updatedCards = cards.map((card: any) =>
          card.id === cardId ? { ...card, ...cardData } : card
        );
        localStorage.setItem("studio_cards", JSON.stringify(updatedCards));
      }
    } else {
      // Save new card
      const newCard = {
        id: Date.now().toString(),
        ...cardData,
      };
      cards.push(newCard);
      localStorage.setItem("studio_cards", JSON.stringify(cards));
    }

    // Update last saved state
    setLastSavedNodes(nodes);
    setLastSavedEdges(edges);
    setLastSavedTitle(title);
    
    // Reset unsaved changes flag
    setHasUnsavedChanges(false);
    
    showNotification("Crew saved successfully!", "success");
  };

  const handleCancel = () => {
    router.push("/studio");
  };

  const handleRun = () => {
    const cardId = searchParams.get("id") || Date.now().toString();
    
    // Simulate run output based on nodes
    const output = nodes.map(node => {
      const nodeData = node.data as NodeData;
      return `${nodeData.label}: ${nodeData.expectedOutput || 'Processing...'}`;
    }).join('\n');
    
    // Create a new run record
    const newRun = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      status: "completed",
      duration: `${Math.floor(Math.random() * 5) + 1}m ${Math.floor(Math.random() * 60)}s`,
      nodesExecuted: nodes.length,
      output: output || "No output generated",
    };
    
    // Save run to localStorage
    const runsKey = `crew_runs_${cardId}`;
    const existingRuns = localStorage.getItem(runsKey);
    const runs = existingRuns ? JSON.parse(existingRuns) : [];
    runs.unshift(newRun); // Add to beginning
    localStorage.setItem(runsKey, JSON.stringify(runs));
    
    // Force refresh of runs history
    setRunsRefreshKey(prev => prev + 1);
    
    // Show notification
    showNotification("Flow execution started! Run completed successfully.", "success");
    
    // TODO: Implement actual run flow logic with backend
    console.log("Running flow with nodes:", nodes);
    console.log("Running flow with edges:", edges);
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
                onClick={() => setShowRunsHistory(!showRunsHistory)}
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
            <div className="w-64 flex-shrink-0 bg-card border border-border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-4">Node Types</h3>
              <div className="space-y-3">
                {nodeTypeConfigs.map((nodeType) => (
                  <div
                    key={nodeType.type}
                    draggable
                    onDragStart={(e) => onDragStart(e, nodeType.type)}
                    className="flex items-center gap-3 p-3 rounded-lg border-2 border-border cursor-move hover:border-primary transition-colors"
                    style={{
                      background: `${nodeType.color}20`,
                    }}
                  >
                    <span className="text-2xl">{nodeType.icon}</span>
                    <div>
                      <div className="font-medium text-sm">{nodeType.label}</div>
                      <div className="text-xs text-muted-foreground">
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
            <div key={runsRefreshKey} className="w-96 flex-shrink-0 bg-card border border-border rounded-lg p-4 overflow-y-auto max-h-[600px]">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Past Runs</h3>
              </div>
              <div className="space-y-3">
                {(() => {
                  const cardId = searchParams.get("id") || "";
                  const runsKey = `crew_runs_${cardId}`;
                  const runsData = localStorage.getItem(runsKey);
                  const runs = runsData ? JSON.parse(runsData) : [];
                  
                  if (runs.length === 0) {
                    return (
                      <div className="text-center text-muted-foreground py-8">
                        No runs yet. Click "Run Flow" to execute this crew.
                      </div>
                    );
                  }
                  
                  return runs.map((run: any, index: number) => (
                    <div
                      key={run.id}
                      className="p-4 border border-border rounded-lg hover:border-primary transition-colors cursor-pointer bg-card hover:bg-muted"
                      onClick={() => {
                        // Show run details in alert (you can replace this with a modal later)
                        alert(`Run Details:\n\nStatus: ${run.status}\nDuration: ${run.duration}\nNodes Executed: ${run.nodesExecuted}\n\nOutput:\n${run.output}`);
                      }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="font-semibold text-sm mb-1">
                            Run #{runs.length - index}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(run.timestamp).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric'
                            })} at {new Date(run.timestamp).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        </div>
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${
                          run.status === "completed" 
                            ? "bg-green-100 text-green-800" 
                            : run.status === "failed"
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}>
                          {run.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-sm space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Duration:</span>
                          <span className="font-medium">{run.duration}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Nodes Executed:</span>
                          <span className="font-medium">{run.nodesExecuted}</span>
                        </div>
                        {run.output && (
                          <div className="mt-3 pt-3 border-t border-border">
                            <div className="text-xs text-muted-foreground mb-1">Output Preview:</div>
                            <div className="text-xs bg-muted p-2 rounded max-h-20 overflow-hidden">
                              {run.output.substring(0, 100)}
                              {run.output.length > 100 && '...'}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="mt-3 text-xs text-primary">
                        Click to view full details →
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>
          )}

          {/* React Flow Canvas */}
          <div className={`flex-1 h-[600px] border-2 border-border rounded-lg bg-card relative`}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodesChange={mode === "edit" ? onNodesChange : undefined}
              onEdgesChange={mode === "edit" ? onEdgesChange : undefined}
              onConnect={mode === "edit" ? onConnect : undefined}
              onDrop={mode === "edit" ? onDrop : undefined}
              onDragOver={mode === "edit" ? onDragOver : undefined}
              onNodesDelete={mode === "edit" ? onNodesDelete : undefined}
              deleteKeyCode={mode === "edit" ? "Delete" : undefined}
              nodesDraggable={mode === "edit"}
              nodesConnectable={mode === "edit"}
              elementsSelectable={mode === "edit"}
              fitView
            >
              <Controls />
              <MiniMap />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            </ReactFlow>
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
