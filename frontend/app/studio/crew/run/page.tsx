"use client";

import React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { useCrewById } from "@/hooks/useCrewById";
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

interface TaskSnapshot {
  key: string;
  name?: string;
  task_description?: string;
  description?: string;
  expected_output?: string;
  agent?: string;
  [key: string]: any;
}

const taskColorMap: Record<string, string> = {
  marketing_research: "#c878e0ff",
  content_strategy: "#389e7eff",
  social_media_schedule: "#cc6262ff",
  copywriter: "#f59e0bff",
  image_generator: "#e1f24cff",
  orshot_render: "#5881c3ff",
};

const getTaskColor = (taskKey: string): string => {
  return taskColorMap[taskKey] || "#6B7280";
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

  const { data: crewData, isLoading: isLoadingCrew } = useCrewById(crewId);
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

  // Find the selected run from crew data
  const selectedRun = React.useMemo(() => {
    if (crewData) {
      const crewDataWithRuns = crewData as any;
      const runs = crewDataWithRuns.crew_runs || [];
      return runs.find((run: any) => run.id === runId);
    }
    return null;
  }, [crewData, runId]);

  const crewRuns = React.useMemo(() => {
    if (crewData) {
      const crewDataWithRuns = crewData as any;
      return crewDataWithRuns.crew_runs || [];
    }
    return [];
  }, [crewData]);

  const runNumber = React.useMemo(() => {
    if (selectedRun && crewRuns.length > 0) {
      const index = crewRuns.findIndex((r: any) => r.id === selectedRun.id);
      return index !== -1 ? crewRuns.length - index : null;
    }
    return null;
  }, [selectedRun, crewRuns]);

  // Build nodes and edges from tasks_snapshot
  const { nodes, edges, nodeTypes } = React.useMemo(() => {
    if (!selectedRun || !selectedRun.run_metadata?.tasks_snapshot) {
      return { nodes: [START_NODE], edges: [], nodeTypes: { start: StartNode } };
    }

    const tasksSnapshot = selectedRun.run_metadata.tasks_snapshot as TaskSnapshot[];

    const nodeTypeConfigs = tasksSnapshot.map((task) => {
      // Try to get name and description from snapshot first
      let name = task.name;
      let description = task.task_description || task.description;

      // If missing, fallback to pre-defined tasks
      if (!name || !description) {
        const preDefined = preDefinedTasks.find((pt) => pt.key === task.key);
        if (preDefined) {
          name = name || preDefined.name;
          description = description || preDefined.task_description;
        }
      }

      // Final fallback to key or agent_key
      name = name || task.agent || task.key;
      description = description || "No description available";

      return {
        type: task.key,
        name,
        color: getTaskColor(task.key),
        description,
      };
    });

    const loadedNodes = tasksSnapshot.map((task, index) => {
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
        },
        style: {
          background: getTaskColor(task.key),
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

    // Build edges connecting tasks in sequence
    const constructedEdges: Edge[] = [];
    if (tasksSnapshot.length > 0) {
      constructedEdges.push({
        id: `start-node-${tasksSnapshot[0].key}`,
        source: "start-node",
        target: tasksSnapshot[0].key,
      });
    }
    for (let i = 0; i < tasksSnapshot.length - 1; i++) {
      constructedEdges.push({
        id: `${tasksSnapshot[i].key}-${tasksSnapshot[i + 1].key}`,
        source: tasksSnapshot[i].key,
        target: tasksSnapshot[i + 1].key,
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
  }, [selectedRun, preDefinedTasks]);

  React.useEffect(() => {
    if (!token) {
      router.push("/auth/login");
    }
  }, [token, router]);

  // Get completed tasks from task_states
  const completedTasks = React.useMemo(() => {
    if (!selectedRun?.output?.task_states) {
      console.log("No task_states found:", selectedRun?.output);
      return [];
    }
    
    const tasks = Object.entries(selectedRun.output.task_states)
      .filter(([_, taskState]: [string, any]) => taskState.status === "COMPLETED")
      .map(([taskKey, taskState]: [string, any]) => ({
        key: taskKey,
        order: taskState.order,
      }))
      .sort((a, b) => a.order - b.order);
    
    console.log("Completed tasks:", tasks);
    return tasks;
  }, [selectedRun]);

  const handleBack = () => {
    router.push(`/studio/crew?id=${crewId}&title=${encodeURIComponent(crewName || "")}&mode=view`);
  };

  const handleCancel = async () => {
    if (!selectedRun || !token) return;

    setIsCancelling(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_CREW_API_BASE_URL || "http://localhost:8001";
      const response = await fetch(
        `${apiUrl}/crew/crew-run/${selectedRun.id}/cancel`,
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
        // Refetch crew data to update the UI
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

  const handleRetry = async () => {
    if (!selectedRun || !token || !selectedRetryTask || !retryFeedback.trim()) {
      toast.error("Please select a task and provide feedback");
      return;
    }

    const apiUrl = process.env.NEXT_PUBLIC_CREW_API_BASE_URL || "http://localhost:8001";
    
    try {
      const response = await fetch(
        `${apiUrl}/crew/crew-run/${selectedRun.id}/retry`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            retry_from_task_key: selectedRetryTask,
            feedback: retryFeedback,
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success("Crew run retry initiated successfully");
        // Navigate to the new retry run
        setTimeout(() => {
          router.push(
            `/studio/crew/run?crewId=${crewId}&runId=${result.id}&crewName=${encodeURIComponent(crewName || "")}`
          );
        }, 1000);
      } else {
        let errorMessage = "Unknown error";
        try {
          const error = await response.json();
          errorMessage = error.detail || JSON.stringify(error);
        } catch {
          errorMessage = await response.text();
        }
        toast.error(`Failed to retry crew run: ${errorMessage}`);
      }
    } catch (error) {
      console.error("Error retrying crew run:", error);
      toast.error(`Failed to retry crew run: ${error}`);
    } finally {
      setIsRetrying(false);
      setSelectedRetryTask("");
      setRetryFeedback("");
    }
  };

  if (isLoadingCrew) {
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

  if (!selectedRun) {
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
                Run #{runNumber || "N/A"}
              </h1>
              <p className="text-sm text-muted-foreground">
                Run ID: {selectedRun.id}
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
                    disabled={!selectedRetryTask || !retryFeedback.trim()}
                  >
                    <RotateCcw className="mr-2 h-4 w-4" />
                    Retry
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
            <h2 className="text-2xl font-semibold mb-4">Task Flow</h2>
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

          {/* Output Section */}
          <div className="bg-card border-2 border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Output</h2>
            <div className="bg-muted border border-border rounded-lg p-4 max-h-96 overflow-y-auto">
              {selectedRun.output ? (
                <pre className="text-sm whitespace-pre-wrap font-mono">
                  {JSON.stringify(selectedRun.output, null, 2)}
                </pre>
              ) : (
                <p className="text-muted-foreground">No output available</p>
              )}
            </div>
          </div>

          {/* Artifacts Section */}
          <div className="bg-card border-2 border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Artifacts</h2>
            <div className="bg-muted border border-border rounded-lg p-4">
              {selectedRun.artifacts && selectedRun.artifacts.length > 0 ? (
                <div className="space-y-3">
                  {selectedRun.artifacts.map((artifact: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-4 bg-card border border-border rounded-lg hover:bg-accent transition-colors"
                    >
                      <div className="flex-1">
                        <p className="font-medium">
                          {artifact.file_name || "Unnamed artifact"}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Type: {artifact.type}
                        </p>
                      </div>
                      <span className="text-sm text-muted-foreground ml-4">
                        {artifact.id}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No artifacts available</p>
              )}
            </div>
          </div>

          {/* Additional Information Section */}
          {selectedRun.created_at && (
            <div className="bg-card border-2 border-border rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4">
                Additional Information
              </h2>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Created at:</span>
                  <span className="text-muted-foreground">
                    {new Date(selectedRun.created_at).toLocaleString()}
                  </span>
                </div>
                {selectedRun.status && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Status:</span>
                    <span className="text-muted-foreground">
                      {selectedRun.status}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
