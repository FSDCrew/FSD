"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

const StartNode = memo(({ isConnectable }: NodeProps) => {
  return (
    <>
      <div 
        style={{ 
          padding: "20px 30px", 
          minWidth: "120px", 
          position: "relative",
        //   background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          background: "black",
          border: "3px solid #fff",
          borderRadius: "50px",
          boxShadow: "0 4px 15px rgba(0, 0, 0, 0.2)",
        }}
      >
        <div style={{ 
          fontSize: "16px", 
          fontWeight: "700", 
          textAlign: "center",
          color: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px"
        }}>
          {/* <span style={{ fontSize: "20px" }}>🚀</span> */}
          <span>START</span>
        </div>
        <div style={{ 
          fontSize: "9px", 
          textAlign: "center",
          color: "rgba(255, 255, 255, 0.8)",
          marginTop: "4px",
          fontWeight: "500"
        }}>
          {/* Connect tasks here */}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={isConnectable}
        style={{
          background: "#fff",
          width: "14px",
          height: "14px",
          border: "3px solid #667eea",
          right: "-7px",
        }}
      />
    </>
  );
});

StartNode.displayName = "StartNode";

export default StartNode;
