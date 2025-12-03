"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

const StartNode = memo(({ isConnectable }: NodeProps) => {
  return (
    <>
      <div 
        style={{ 
          padding: "10px", 
          minWidth: "120px", 
          position: "relative",
          background: "#0d0f0eff",
          border: "1px solid rgba(230, 230, 230, 0.96)",
          borderRadius: "8px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
        }}
      >
        <div style={{ 
          fontSize: "12px", 
          fontWeight: "600", 
          textAlign: "center",
          color: "white",
        }}>
          Kickoff
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
          right: "-6px",
        }}
      />
    </>
  );
});

StartNode.displayName = "StartNode";

export default StartNode;
