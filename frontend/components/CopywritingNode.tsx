"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

interface CopywritingNodeData extends Record<string, unknown> {
  label: string;
  expectedOutput?: string;
  crewInput?: {
    topic?: string;
  };
  onDelete?: () => void;
}

const CopywritingNode = memo(({ data, isConnectable, id }: NodeProps) => {
  const nodeData = data as CopywritingNodeData;
  
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
            padding: "2px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          title="Delete node"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ color: "white", opacity: 0.8 }}
          >
            <path d="M3 6h18" />
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
          </svg>
        </button>
        <div style={{ fontSize: "12px", fontWeight: "600", marginBottom: "8px", textAlign: "center" }}>
          Copywriting
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
        <div>
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

CopywritingNode.displayName = "CopywritingNode";

export default CopywritingNode;
