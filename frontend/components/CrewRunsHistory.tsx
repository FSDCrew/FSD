import React from "react";
import { Button } from "@/components/ui/button";

interface CrewRunsHistoryProps {
  crewRuns: any[];
  onSelectRun: (run: any) => void;
}

export function CrewRunsHistory({ crewRuns, onSelectRun }: CrewRunsHistoryProps) {
  return (
    <div className="w-96 flex-shrink-0 bg-[#1a1a1a] border-2 border-white rounded-lg p-4 overflow-y-auto max-h-[600px]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Your Runs</h3>
      </div>
      <div className="space-y-3">
        {crewRuns.length === 0 ? (
          <div className="text-center text-white py-8">
            No runs yet. Click "Kickoff" to execute this crew.
          </div>
        ) : (
          crewRuns.map((run: any, index: number) => (
            <div
              key={run.id}
              className="p-4 border-2 border-transparent rounded-lg hover:border-white transition-colors cursor-pointer bg-[#3a3a3a] hover:bg-[#2a2a2a]"
              onClick={() => onSelectRun(run)}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="font-semibold text-sm mb-1 text-white">
                    Run #{crewRuns.length - index}
                  </div>
                  <div className="text-xs text-gray-300">
                    {run.id}
                  </div>
                </div>
              </div>
              <div className="text-sm space-y-2">
                {run.output && (
                  <div className="mt-3 pt-3 border-t border-white">
                    <div className="text-xs text-gray-300 mb-1">Output Preview:</div>
                    <div className="text-xs bg-[#1a1a1a] text-white p-2 rounded max-h-20 overflow-hidden">
                      {JSON.stringify(run.output).substring(0, 100)}
                      {JSON.stringify(run.output).length > 100 && '...'}
                    </div>
                  </div>
                )}
              </div>
              <div className="mt-3 text-xs text-white">
                Click to view full details →
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
