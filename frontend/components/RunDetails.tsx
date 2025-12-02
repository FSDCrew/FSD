import React, { useEffect, useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import type { RunDetailsProps } from "@/types/ComponentProps";
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

const createNodeTypes = (nodeTypeConfigs: Array<{ type: string; name: string; color: string; description: string }>) => {
  const dynamicTypes = nodeTypeConfigs.reduce((acc, config) => {
    acc[config.type] = CustomNode;
    return acc;
  }, {} as Record<string, any>);

  return {
    start: StartNode,
    ...dynamicTypes,
  };
};

export function RunDetails({ selectedRun, crewRuns, onClose }: RunDetailsProps) {
  const [preDefinedTasks, setPreDefinedTasks] = useState<PreDefinedTask[]>([]);
  const [isLoadingTasks, setIsLoadingTasks] = useState(true);

  // Fetch pre-defined tasks
  useEffect(() => {
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

  // Build nodes and edges from tasks_snapshot
  const { nodes, edges, nodeTypes } = useMemo(() => {
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
        const preDefined = preDefinedTasks.find(pt => pt.key === task.key);
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
      nodeTypes: types
    };
  }, [selectedRun, preDefinedTasks]);

  if (!selectedRun) {
    return null;
  }

  return (
    <div className="bg-[#1a1a1a] border-2 border-white rounded-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold text-white mb-2">
            Run Details - #{crewRuns.findIndex(r => r.id === selectedRun.id) !== -1 
              ? crewRuns.length - crewRuns.findIndex(r => r.id === selectedRun.id) 
              : 'N/A'}
          </h3>
          <p className="text-sm text-gray-300">ID: {selectedRun.id}</p>
        </div>
        <Button
          onClick={onClose}
          variant="secondary"
          className="bg-white text-black hover:bg-gray-200"
        >
          Close
        </Button>
      </div>

      {/* Canvas Section */}
      <div className="mb-6">
        <h4 className="text-lg font-semibold text-white mb-3">Task Flow</h4>
        <div className="h-[400px] border border-white rounded-lg bg-card">
          {isLoadingTasks ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-300">Loading task flow...</p>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable={false}
              fitView
              fitViewOptions={{ padding: 0.2 }}
            >
              <Controls showInteractive={false} />
              <MiniMap />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            </ReactFlow>
          )}
        </div>
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
  );
}
