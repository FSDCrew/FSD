"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { BaseNodeData } from "@/types/NodeData";

interface CustomNodeData extends BaseNodeData {
  icon: string;
  status?: string;
  onDelete?: () => void;
}

const CustomNode = memo(({ data, isConnectable }: NodeProps) => {
  const nodeData = data as CustomNodeData;
  
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
      <div style={{ padding: "10px", textAlign: "center" }}>
        <div style={{ fontSize: "24px", marginBottom: "4px" }}>{nodeData.icon}</div>
        <div style={{ 
          fontSize: "12px", 
          fontWeight: "600",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px"
        }}>
          {nodeData.label}
          {nodeData.onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                nodeData.onDelete?.();
              }}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "2px",
                display: "flex",
                alignItems: "center",
                color: "inherit",
                opacity: 0.6,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.color = "#ef4444";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = "0.6";
                e.currentTarget.style.color = "inherit";
              }}
              title="Delete task"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M3 6h18" />
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              </svg>
            </button>
          )}
        </div>
        {nodeData.status && (
          <div style={{ fontSize: "10px", fontWeight: "500", marginTop: "4px",opacity: 0.9}}>{nodeData.status}</div>
        )}
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

CustomNode.displayName = "CustomNode";

export default CustomNode;
