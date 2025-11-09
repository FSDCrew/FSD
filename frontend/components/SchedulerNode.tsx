"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

interface SchedulerNodeData extends Record<string, unknown> {
  label: string;
  expectedOutput?: string;
  crewInput?: {
    topic?: string;
  };
  taskInput?: {
    numOfWeeks?: number;
  };
  onDelete?: () => void;
}

const SchedulerNode = memo(({ data, isConnectable, id }: NodeProps) => {
  const nodeData = data as SchedulerNodeData;
  
  return (
    <>
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
        style={{
          background: "#555",
          width: "12px",
          height: "12px",
          border: "2px solid white",
        }}
      />
      <div style={{ padding: "12px", minWidth: "200px", position: "relative" }}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (nodeData.onDelete) nodeData.onDelete();
          }}
          style={{
            position: "absolute",
            top: "4px",
            right: "4px",
            background: "transparent",
            border: "none",
            cursor: "pointer",
            fontSize: "14px",
            padding: "0",
            lineHeight: "1",
          }}
          title="Delete node"
        >
          🗑️
        </button>
        <div style={{ fontSize: "12px", fontWeight: "600", marginBottom: "8px", textAlign: "center" }}>
          Scheduler
        </div>
        <div style={{ marginBottom: "8px" }}>
          <label style={{ fontSize: "10px", display: "block", marginBottom: "2px" }}>Expected Output:</label>
          <textarea
            value={nodeData.expectedOutput || ""}
            onChange={(e) => {
              if (data.onChange) {
                (data.onChange as (field: string, value: string) => void)("expectedOutput", e.target.value);
              }
            }}
            style={{
              width: "100%",
              fontSize: "11px",
              padding: "4px",
              border: "1px solid #ccc",
              borderRadius: "4px",
              resize: "vertical",
              minHeight: "40px",
            }}
            placeholder="Enter expected output..."
          />
        </div>
        <div style={{ marginBottom: "8px" }}>
          <label style={{ fontSize: "10px", display: "block", marginBottom: "2px" }}>Topic:</label>
          <input
            type="text"
            value={nodeData.crewInput?.topic || ""}
            onChange={(e) => {
              if (data.onChange) {
                (data.onChange as (field: string, value: string) => void)("crewInput.topic", e.target.value);
              }
            }}
            style={{
              width: "100%",
              fontSize: "11px",
              padding: "4px",
              border: "1px solid #ccc",
              borderRadius: "4px",
            }}
            placeholder="Enter topic..."
          />
        </div>
        <div>
          <label style={{ fontSize: "10px", display: "block", marginBottom: "2px" }}>Number of Weeks:</label>
          <input
            type="number"
            value={nodeData.taskInput?.numOfWeeks || 1}
            onChange={(e) => {
              if (data.onChange) {
                (data.onChange as (field: string, value: string) => void)("taskInput.numOfWeeks", e.target.value);
              }
            }}
            style={{
              width: "100%",
              fontSize: "11px",
              padding: "4px",
              border: "1px solid #ccc",
              borderRadius: "4px",
            }}
            min="1"
          />
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={isConnectable}
        style={{
          background: "#555",
          width: "12px",
          height: "12px",
          border: "2px solid white",
        }}
      />
    </>
  );
});

SchedulerNode.displayName = "SchedulerNode";

export default SchedulerNode;
