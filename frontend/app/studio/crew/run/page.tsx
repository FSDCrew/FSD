"use client";

import React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { useCrewById } from "@/hooks/useCrewById";
import { useCrewRun } from "@/hooks/useCrewRun";
import { getArtifactForUserArtifactViewArtifactIdGet } from "@/lib/api/crud";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, XCircle, RotateCcw } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import StartNode from "@/components/StartNode";
import CustomNode from "@/components/CustomNode";
import { getPreDefinedTasksTasksPreDefinedGet } from "@/lib/api/crew";

interface PreDefinedTask {
  key: string;
  name: string;
  task_description: string;
}

interface TaskState {
  state: {
    reads?: Record<string, any>;
    writes?: Record<string, any>;
  };
  completed_at: string | null;
  status: string;
  order: number;
}

interface TaskSnapshot {
  key: string;
  name?: string;
  task_description?: string;
  description?: string;
  expected_output?: string;
  agent?: string;
  [key: string]: any;
}

const statusColorMap: Record<string, string> = {
  QUEUED: "#6B7280", // Gray
  RUNNING: "#3B82F6", // Blue
  COMPLETED: "#10B981", // Green
  FAILED: "#EF4444", // Red
};

const getQueueStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    QUEUED: "#6B7280", // Gray
    CLAIMED: "#3B82F6", // Blue
    COMPLETED: "#10B981", // Green
    FAILED: "#EF4444", // Red
    CANCELLED: "#6B7280", // Gray
  };
  return colorMap[status] || "#6B7280";
};

const getQueueStatusLabel = (status: string): string => {
  const labelMap: Record<string, string> = {
    QUEUED: "Queued",
    CLAIMED: "Running",
    COMPLETED: "Completed",
    FAILED: "Failed",
    CANCELLED: "Cancelled",
  };
  return labelMap[status] || status;
};

const getStatusColor = (status: string): string => {
  return statusColorMap[status] || "#6B7280";
};

const START_NODE: Node = {
  id: "start-node",
  type: "start",
  position: { x: 50, y: 250 },
  data: { label: "START" },
  draggable: false,
  deletable: false,
  selectable: false,
  connectable: false,
};

const createNodeTypes = (
  nodeTypeConfigs: Array<{
    type: string;
    name: string;
    color: string;
    description: string;
  }>
) => {
  const dynamicTypes = nodeTypeConfigs.reduce((acc, config) => {
    acc[config.type] = CustomNode;
    return acc;
  }, {} as Record<string, any>);

  return {
    start: StartNode,
    ...dynamicTypes,
  };
};

export default function RunDetailsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, token } = useAuth();

  const crewId = searchParams.get("crewId");
  const runId = searchParams.get("runId");
  const crewName = searchParams.get("crewName");

  // Fetch crew run details with polling (every 2 seconds)
  const { data: crewRunData, isLoading: isLoadingCrewRun } = useCrewRun(runId, {
    refetchInterval: 2000,
  });
  
  const queryClient = useQueryClient();
  const [loadingArtifactId, setLoadingArtifactId] = React.useState<string | null>(null);
  const [preDefinedTasks, setPreDefinedTasks] = React.useState<PreDefinedTask[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = React.useState(true);
  const [isRetrying, setIsRetrying] = React.useState(false);
  const [isCancelling, setIsCancelling] = React.useState(false);
  const [selectedRetryTask, setSelectedRetryTask] = React.useState<string>("");
  const [retryFeedback, setRetryFeedback] = React.useState<string>("");

  // Fetch pre-defined tasks
  React.useEffect(() => {
    const fetchPreDefinedTasks = async () => {
      setIsLoadingTasks(true);
      try {
        const response = await getPreDefinedTasksTasksPreDefinedGet();
        if (response.data) {
          setPreDefinedTasks(response.data as PreDefinedTask[]);
        }
      } catch (error) {
        console.error("Error fetching pre-defined tasks:", error);
      } finally {
        setIsLoadingTasks(false);
      }
    };

    fetchPreDefinedTasks();
  }, []);

  // Build nodes and edges from task_states
  const { nodes, edges, nodeTypes } = React.useMemo(() => {
    if (!crewRunData?.output?.task_states) {
      return { nodes: [START_NODE], edges: [], nodeTypes: { start: StartNode } };
    }

    const taskStates = crewRunData.output.task_states as Record<string, TaskState>;
    
    // Convert task_states object to array and sort by order
    const tasksArray = Object.entries(taskStates)
      .map(([taskKey, taskData]) => ({
        key: taskKey,
        order: taskData.order,
        status: taskData.status,
        completed_at: taskData.completed_at,
        state: taskData.state,
      }))
      .sort((a, b) => a.order - b.order);

    console.log("Tasks array sorted by order:", tasksArray);

    // Create node type configs
    const nodeTypeConfigs = tasksArray.map((task) => {
      // Try to find matching predefined task for name and description
      const preDefined = preDefinedTasks.find((pt) => pt.key === task.key);
      
      const name = preDefined?.name || task.key;
      const description = preDefined?.task_description || "No description available";

      return {
        type: task.key,
        name,
        color: getStatusColor(task.status),
        description,
      };
    });

    // Create nodes based on order
    const loadedNodes = tasksArray.map((task, index) => {
      const config = nodeTypeConfigs.find((n) => n.type === task.key);
      const position = {
        x: 300 + index * 300,
        y: 250,
      };

      return {
        id: task.key,
        type: task.key,
        position,
        data: {
          label: config?.name || task.key,
          taskType: task.key,
          status: task.status,
        },
        style: {
          background: getStatusColor(task.status),
          color: "white",
          border: "1px solid rgba(0, 0, 0, 0.2)",
          borderRadius: "8px",
          minWidth: "120px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
        },
        connectable: false,
        draggable: false,
        selectable: false,
      } as Node;
    });

    // Build edges connecting tasks in sequence (based on sorted order)
    const constructedEdges: Edge[] = [];
    if (tasksArray.length > 0) {
      constructedEdges.push({
        id: `start-node-${tasksArray[0].key}`,
        source: "start-node",
        target: tasksArray[0].key,
      });
    }
    for (let i = 0; i < tasksArray.length - 1; i++) {
      constructedEdges.push({
        id: `${tasksArray[i].key}-${tasksArray[i + 1].key}`,
        source: tasksArray[i].key,
        target: tasksArray[i + 1].key,
      });
    }

    const startNodeInstance = {
      ...START_NODE,
      connectable: false,
      draggable: false,
      selectable: false,
    };

    const types = createNodeTypes(nodeTypeConfigs);

    return {
      nodes: [startNodeInstance, ...loadedNodes],
      edges: constructedEdges,
      nodeTypes: types,
    };
  }, [crewRunData, preDefinedTasks]);

  React.useEffect(() => {
    if (!token) {
      router.push("/auth/login");
    }
  }, [token, router]);

  // Get completed tasks from task_states
  const completedTasks = React.useMemo(() => {
    if (!crewRunData?.output?.task_states) {
      console.log("No task_states found:", crewRunData?.output);
      return [];
    }
    
    const taskStates = crewRunData.output.task_states as Record<string, TaskState>;
    const tasks = Object.entries(taskStates)
      .filter(([_, taskState]) => taskState.status === "COMPLETED")
      .map(([taskKey, taskState]) => ({
        key: taskKey,
        order: taskState.order,
      }))
      .sort((a, b) => a.order - b.order);

    console.log("Completed tasks:", tasks);
    return tasks;
  }, [crewRunData]);

  const handleBack = () => {
    router.push(`/studio/crew?id=${crewId}&title=${encodeURIComponent(crewName || "")}&mode=view`);
  };

  const handleCancel = async () => {
    if (!crewRunData || !token) return;

    setIsCancelling(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_CREW_API_BASE_URL || "http://localhost:8001";
      const response = await fetch(
        `${apiUrl}/crew/crew-run/${crewRunData.id}/cancel`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        toast.success("Crew run cancelled successfully");
        setTimeout(() => {
          router.refresh();
        }, 1000);
      } else {
        let errorMessage = "Unknown error";
        try {
          const error = await response.json();
          errorMessage = error.detail || JSON.stringify(error);
        } catch {
          errorMessage = await response.text();
        }
        toast.error(`Failed to cancel crew run: ${errorMessage}`);
      }
    } catch (error) {
      console.error("Error cancelling crew run:", error);
      toast.error(`Failed to cancel crew run: ${error}`);
    } finally {
      setIsCancelling(false);
    }
  };

  // Retry crew run mutation
  const retryCrewRunMutation = useMutation({
    mutationFn: async ({
      runId,
      retryFromTaskKey,
      feedback,
    }: {
      runId: string;
      retryFromTaskKey: string;
      feedback: string;
    }) => {
      if (!token) {
        throw new Error("Authentication token is required");
      }

      const apiUrl = process.env.NEXT_PUBLIC_CREW_API_BASE_URL || "http://localhost:8001";
      const response = await fetch(`${apiUrl}/crew/crew-run/${runId}/retry`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json", // Added this
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          retry_from_task_key: retryFromTaskKey,
          feedback: feedback,
        }),
      });

      if (!response.ok) {
        let errorMessage = "Unknown error";
        try {
          const error = await response.json();
          errorMessage = error.detail || JSON.stringify(error);
        } catch {
          errorMessage = await response.text();
        }
        throw new Error(errorMessage); // Added this - was missing
      }

      return await response.json();
    },
    onSuccess: (result) => {
      toast.success("Crew run retry initiated successfully");
      // Invalidate crew query to refetch updated data
      if (crewId) {
        queryClient.invalidateQueries({ queryKey: ['crew', crewId] });
      }
      // Navigate to the new retry run
      setTimeout(() => {
        router.push(
          `/studio/crew/run?crewId=${crewId}&runId=${result.id}&crewName=${encodeURIComponent(crewName || "")}`
        );
      }, 1000);
      // Reset form state
      setSelectedRetryTask("");
      setRetryFeedback("");
      setIsRetrying(false);
    },
    onError: (error: Error) => {
      console.error("Error retrying crew run:", error);
      toast.error(`Failed to retry crew run: ${error.message}`);
      setIsRetrying(false);
    },
  });

  const handleRetry = () => {
    if (!crewRunData || !token || !selectedRetryTask || !retryFeedback.trim()) {
      toast.error("Please select a task and provide feedback");
      return;
    }

    retryCrewRunMutation.mutate({
      runId: crewRunData.id,
      retryFromTaskKey: selectedRetryTask,
      feedback: retryFeedback,
    });
  };

  const handleViewArtifact = async (artifactId: string) => {
    if (!token) {
      toast.error("Authentication required to view artifact");
      return;
    }

    setLoadingArtifactId(artifactId);
    
    try {
      console.log("Fetching presigned URL for artifact:", artifactId);
      
      const response = await getArtifactForUserArtifactViewArtifactIdGet({
        path: { artifact_id: artifactId },
      });

      console.log("Presigned URL response:", response.data);

      const presignedUrl = response.data;

      if (presignedUrl && typeof presignedUrl === 'string') {
        // Open the presigned URL in a new tab
        window.open(presignedUrl, "_blank", "noopener,noreferrer");
        toast.success("Opening artifact...");
      } else {
        console.error("Invalid presigned URL in response:", response.data);
        toast.error("Failed to get artifact URL");
      } 
    } catch (error) {
      console.error("Error fetching artifact:", error);
      toast.error("Failed to load artifact");
    } finally {
      setLoadingArtifactId(null);
    }
  };

  if (isLoadingCrewRun || isLoadingTasks) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="p-6">
          <div className="flex justify-center items-center py-16">
            <div className="text-gray-500">Loading run details...</div>
          </div>
        </main>
      </div>
    );
  }

  if (!crewRunData) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="p-6">
          <div className="flex flex-col items-center justify-center py-16">
            <div className="text-gray-500 mb-4">Run not found</div>
            <Button onClick={handleBack} variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Crew
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="p-6 max-w-6xl mx-auto">
        {/* Header Section */}
        <div className="mb-8">
          <Button
            onClick={handleBack}
            variant="outline"
            className="mb-4 hover:bg-muted"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to {crewName || "Crew"}
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">
                Run Details
              </h1>
              <p className="text-sm text-muted-foreground">
                Run ID: {crewRunData.id}
              </p>
              {crewName && (
                <p className="text-sm text-muted-foreground mt-1">
                  Crew: {crewName}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleCancel}
                disabled={isCancelling}
                variant="outline"
                size="sm"
              >
                {isCancelling ? "Cancelling..." : "Cancel Run"}
              </Button>
              <div
                onClick={() => {
                  if (completedTasks.length === 0) {
                    toast.error("No tasks completed. Unable to retry.");
                  }
                }}
              >
                <Button
                  onClick={() => {
                    if (completedTasks.length > 0) {
                      setIsRetrying(true);
                    }
                  }}
                  disabled={completedTasks.length === 0}
                  variant="outline"
                  size="sm"
                  className={completedTasks.length === 0 ? "pointer-events-none" : ""}
                >
                  Retry
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Retry Dialog */}
        {isRetrying && completedTasks.length > 0 && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card border-2 border-border rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-xl font-semibold mb-4">Retry Crew Run</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Retry from task:
                  </label>
                  <Select value={selectedRetryTask} onValueChange={setSelectedRetryTask}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a completed task" />
                    </SelectTrigger>
                    <SelectContent>
                      {completedTasks.map((task) => (
                        <SelectItem key={task.key} value={task.key}>
                          {task.key} (Order: {task.order})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Feedback / Instructions:
                  </label>
                  <textarea
                    value={retryFeedback}
                    onChange={(e) => setRetryFeedback(e.target.value)}
                    placeholder="Provide feedback or instructions for the retry..."
                    className="w-full min-h-[100px] p-3 border border-border rounded-lg bg-muted resize-none"
                  />
                </div>

                <div className="flex gap-2 justify-end">
                  <Button
                    onClick={() => {
                      setIsRetrying(false);
                      setSelectedRetryTask("");
                      setRetryFeedback("");
                    }}
                    variant="outline"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleRetry}
                    disabled={!selectedRetryTask || !retryFeedback.trim() || retryCrewRunMutation.isPending}
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    {retryCrewRunMutation.isPending ? "Retrying..." : "Retry"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content Section */}
        <div className="space-y-6">
          {/* Task Flow Canvas Section */}
          <div className="bg-card border-2 border-border rounded-lg p-6">
            <div className="flex justify-between mb-4">
              <h2 className="text-2xl font-semibold">Task Flow</h2>
              {crewRunData?.queue_status && (
                <div
                  className="flex items-center px-3 py-1 rounded-md text-sm font-semibold"
                  style={{
                    backgroundColor: getQueueStatusColor(crewRunData.queue_status),
                    color: "white",
                  }}
                >
                  {getQueueStatusLabel(crewRunData.queue_status)}
                </div>
              )}
            </div>
            <div className="h-[300px] border border-border rounded-lg bg-muted">
              {isLoadingTasks ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-muted-foreground">Loading task flow...</p>
                </div>
              ) : (
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  nodeTypes={nodeTypes}
                  nodesDraggable={false}
                  nodesConnectable={false}
                  elementsSelectable={false}
                  panOnDrag={false}
                  zoomOnScroll={false}
                  zoomOnPinch={false}
                  zoomOnDoubleClick={false}
                  preventScrolling={true}
                  fitView
                  fitViewOptions={{ padding: 0.2, duration: 200 }}
                  minZoom={0.1}
                  maxZoom={1.5}
                  defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
                >
                  <Controls showInteractive={false} />
                  <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
                </ReactFlow>
              )}
            </div>
          </div>

          <div className="flex gap-6">
            {/* Inputs Section */}
            <div className="w-1/2 bg-card border-2 border-border rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4">Inputs</h2>
              <div className="max-h-96 overflow-y-auto">
                {crewRunData.run_metadata?.inputs ? (
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-semibold">Theme:</span>{' '}
                      <span className="text-muted-foreground">
                        {String(crewRunData.run_metadata.inputs.theme)}
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-semibold">Brand Description:</span>{' '}
                      <span className="text-muted-foreground">
                        {String(crewRunData.run_metadata.inputs.brand_description)}
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-semibold">Target Audience:</span>{' '}
                      <span className="text-muted-foreground">
                        {String(crewRunData.run_metadata.inputs.target_audience_description)}
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-semibold">Start Date:</span>{' '}
                      <span className="text-muted-foreground">
                        {String(crewRunData.run_metadata.inputs.start_date || '').split('T')[0]}
                      </span>
                    </div>
                    
                    <div>
                      <span className="font-semibold">End Date:</span>{' '}
                      <span className="text-muted-foreground">
                        {String(crewRunData.run_metadata.inputs.end_date || '').split('T')[0]}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No inputs found.</p>
                )}
              </div>
            </div>

            {/* Retry Details Section */}
            <div className="w-1/2 bg-card border-2 border-border rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4">Retry Details</h2>
              <div className="max-h-96 overflow-y-auto">
                {crewRunData.run_metadata?.retry_feedback ? (
                  <div className="space-y-2 text-sm">
                    {Object.entries(crewRunData.run_metadata.retry_feedback as any).map(([key, value]) => {
                      const isRetryTask = key === 'retry_from_task_key';
                      const label = isRetryTask ? 'Retry From' : key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                      const displayValue = isRetryTask && typeof value === 'string' 
                        ? preDefinedTasks.find(t => t.key === value)?.name || value
                        : value;
                      
                      return (
                        <div key={key}>
                          <span className="font-semibold">{label}:</span>{' '}
                          <span className="text-muted-foreground">
                            {typeof displayValue === 'object' && displayValue !== null
                              ? JSON.stringify(displayValue, null, 2)
                              : String(displayValue)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No retry details found.</p>
                )}
              </div>
            </div>
          </div>

          {/* Artifacts Section */}
          <div className="bg-card border-2 border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Artifacts</h2>
            <div className="bg-muted border border-border rounded-lg p-4">
              {crewRunData.artifacts && crewRunData.artifacts.length > 0 ? (
                <div className="space-y-3">
                  {crewRunData.artifacts.map((artifact: any, idx: number) => (
                    <button
                      key={idx}
                      onClick={() => handleViewArtifact(artifact.id)}
                      disabled={loadingArtifactId === artifact.id}
                      className="w-full flex items-center justify-between p-4 bg-card border border-border rounded-lg hover:bg-accent transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <div className="flex-1 text-left">
                        <p className="font-medium">
                          {artifact.file_name || "Unnamed artifact"}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Type: {artifact.type}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <span className="text-sm text-muted-foreground">
                          {artifact.id}
                        </span>
                        {loadingArtifactId === artifact.id ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        ) : (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-5 w-5 text-muted-foreground"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            />
                          </svg>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No artifacts available</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
