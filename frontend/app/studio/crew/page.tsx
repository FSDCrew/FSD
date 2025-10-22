"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Header from "@/components/Header";
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

const initialNodes: Node[] = [
  {
    id: "1",
    position: { x: 250, y: 100 },
    data: { label: "Start Node" },
  },
];

const initialEdges: Edge[] = [];

type TaskType = "research" | "copywriting" | "canva design" | "survey" | "scheduler";

export default function CrewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  
  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Node Creator Modal state
  const [showNodeCreator, setShowNodeCreator] = useState(false);
  const [newNodeName, setNewNodeName] = useState("");
  const [selectedTaskType, setSelectedTaskType] = useState<TaskType>("research");

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const taskTypes: TaskType[] = ["research", "copywriting", "canva design", "survey", "scheduler"];

  const getTaskColor = (taskType: TaskType) => {
    const colors = {
      research: "#3b82f6",
      copywriting: "#8b5cf6",
      "canva design": "#ec4899",
      survey: "#10b981",
      scheduler: "#f59e0b",
    };
    return colors[taskType];
  };

  const openNodeCreator = () => {
    setNewNodeName("");
    setSelectedTaskType("research");
    setShowNodeCreator(true);
  };

  const addNode = () => {
    if (!newNodeName.trim()) return;

    const newNode: Node = {
      id: `node-${Date.now()}`,
      position: {
        x: Math.random() * 400 + 100,
        y: Math.random() * 400 + 100,
      },
      data: { 
        label: String(newNodeName).trim(),
      },
      style: {
        background: getTaskColor(selectedTaskType),
        color: "white",
        border: "1px solid #222",
        borderRadius: "8px",
        padding: "10px",
        fontSize: "14px",
        fontWeight: "500",
      },
    };
    
    setNodes((nds) => nds.concat(newNode));
    setShowNodeCreator(false);
    setNewNodeName("");
    setSelectedTaskType("research");
  };

  useEffect(() => {
    const token = localStorage.getItem("fsd_token");
    if (!token) router.push("/auth/login");

    // Get card data from URL params
    const cardTitle = searchParams.get("title") || "Untitled";
    const cardDescription = searchParams.get("description") || "";
    const cardId = searchParams.get("id");

    setTitle(cardTitle);
    setDescription(cardDescription);

    // Load saved nodes and edges if editing existing card
    if (cardId) {
      const savedCards = localStorage.getItem("studio_cards");
      if (savedCards) {
        const cards = JSON.parse(savedCards);
        const card = cards.find((c: any) => c.id === cardId);
        if (card) {
          if (card.nodes) setNodes(card.nodes);
          if (card.edges) setEdges(card.edges);
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
    
    const cardData = {
      title,
      description,
      nodes,
      edges,
    };
    
    if (cardId) {
      // Update existing card
      const savedCards = localStorage.getItem("studio_cards");
      if (savedCards) {
        const cards = JSON.parse(savedCards);
        const updatedCards = cards.map((card: any) =>
          card.id === cardId ? { ...card, ...cardData } : card
        );
        localStorage.setItem("studio_cards", JSON.stringify(updatedCards));
      }
    } else {
      // Save new card
      const savedCards = localStorage.getItem("studio_cards");
      const cards = savedCards ? JSON.parse(savedCards) : [];
      const newCard = {
        id: Date.now().toString(),
        ...cardData,
      };
      cards.push(newCard);
      localStorage.setItem("studio_cards", JSON.stringify(cards));
    }

    // Navigate back to studio
    router.push("/studio");
  };

  const handleCancel = () => {
    router.push("/studio");
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="p-6">
        {/* Top Section with Title */}
        <div className="mb-8">
          {isEditingTitle ? (
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={() => setIsEditingTitle(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") setIsEditingTitle(false);
              }}
              className="text-4xl font-bold bg-transparent border-b-2 border-primary focus:outline-none pb-2"
              autoFocus
              placeholder="Enter title..."
              style={{ width: 'fit-content', minWidth: '300px' }}
            />
          ) : (
            <h1
              onClick={() => setIsEditingTitle(true)}
              className="text-4xl font-bold cursor-pointer hover:text-primary transition-colors pb-2 border-b-2 border-transparent hover:border-muted inline-block"
            >
              {title || "Untitled"}
            </h1>
          )}
        </div>

        {/* React Flow Canvas */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Crew Flow</h2>
            <button
              onClick={openNodeCreator}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm"
            >
              + Add Node
            </button>
          </div>
          <div className="h-[600px] border-2 border-border rounded-lg bg-card">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
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
          <button
            onClick={handleCancel}
            className="px-6 py-2 bg-secondary text-secondary-foreground rounded-lg hover:opacity-90 transition-opacity"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
          >
            Save Changes
          </button>
        </div>

        {/* Node Creator Modal */}
        {showNodeCreator && (
          <div 
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                setShowNodeCreator(false);
                setNewNodeName("");
                setSelectedTaskType("research");
              }
            }}
          >
            <div className="bg-card border border-border rounded-lg p-6 w-full max-w-sm mx-4">
              <h2 className="text-xl font-semibold mb-4">Node Creator</h2>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="nodeName" className="block text-sm font-medium mb-2">
                    Name
                  </label>
                  <input
                    id="nodeName"
                    type="text"
                    value={newNodeName}
                    onChange={(e) => {
                      e.preventDefault();
                      setNewNodeName(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newNodeName.trim()) {
                        e.preventDefault();
                        addNode();
                      }
                    }}
                    className="w-full px-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Enter node name"
                    autoFocus
                  />
                </div>

                <div>
                  <label htmlFor="taskType" className="block text-sm font-medium mb-2">
                    Shape
                  </label>
                  <select
                    id="taskType"
                    value={selectedTaskType}
                    onChange={(e) => {
                      e.preventDefault();
                      setSelectedTaskType(e.target.value as TaskType);
                    }}
                    className="w-full px-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="research">Research</option>
                    <option value="copywriting">Copywriting</option>
                    <option value="canva design">Canva Design</option>
                    <option value="survey">Survey</option>
                    <option value="scheduler">Scheduler</option>
                  </select>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.preventDefault();
                  addNode();
                }}
                disabled={!newNodeName.trim()}
                className="w-full mt-6 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                Add
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
