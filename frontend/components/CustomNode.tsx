"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

interface CustomNodeData extends Record<string, unknown> {
  label: string;
  taskType: string;
  icon: string;
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
        <div style={{ fontSize: "12px", fontWeight: "600" }}>{nodeData.label}</div>
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
