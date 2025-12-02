import React from "react";
import { Button } from "@/components/ui/button";
import type { RunDetailsProps } from "@/types/ComponentProps";

export function RunDetails({ selectedRun, crewRuns, onClose }: RunDetailsProps) {
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
