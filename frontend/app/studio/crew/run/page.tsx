"use client";

import React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { useCrewById } from "@/hooks/useCrewById";
import { ArrowLeft } from "lucide-react";

export default function RunDetailsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, token } = useAuth();

  const crewId = searchParams.get("crewId");
  const runId = searchParams.get("runId");
  const crewName = searchParams.get("crewName");

  const { data: crewData, isLoading: isLoadingCrew } = useCrewById(crewId);

  // Find the selected run from crew data
  const selectedRun = React.useMemo(() => {
    if (crewData) {
      const crewDataWithRuns = crewData as any;
      const runs = crewDataWithRuns.crew_runs || [];
      return runs.find((run: any) => run.id === runId);
    }
    return null;
  }, [crewData, runId]);

  const crewRuns = React.useMemo(() => {
    if (crewData) {
      const crewDataWithRuns = crewData as any;
      return crewDataWithRuns.crew_runs || [];
    }
    return [];
  }, [crewData]);

  const runNumber = React.useMemo(() => {
    if (selectedRun && crewRuns.length > 0) {
      const index = crewRuns.findIndex((r: any) => r.id === selectedRun.id);
      return index !== -1 ? crewRuns.length - index : null;
    }
    return null;
  }, [selectedRun, crewRuns]);

  React.useEffect(() => {
    if (!token) {
      router.push("/auth/login");
    }
  }, [token, router]);

  const handleBack = () => {
    router.push(`/studio/crew?id=${crewId}&title=${encodeURIComponent(crewName || "")}&mode=view`);
  };

  if (isLoadingCrew) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="p-6">
          <div className="flex justify-center items-center py-16">
            <div className="text-gray-500">Loading run details...</div>
          </div>
        </main>
      </div>
    );
  }

  if (!selectedRun) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="p-6">
          <div className="flex flex-col items-center justify-center py-16">
            <div className="text-gray-500 mb-4">Run not found</div>
            <Button onClick={handleBack} variant="default">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Crew
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="p-6 max-w-6xl mx-auto">
        {/* Header Section */}
        <div className="mb-8">
          <Button
            onClick={handleBack}
            variant="ghost"
            className="mb-4 hover:bg-muted"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to {crewName || "Crew"}
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">
                Run #{runNumber || "N/A"}
              </h1>
              <p className="text-sm text-muted-foreground">
                Run ID: {selectedRun.id}
              </p>
              {crewName && (
                <p className="text-sm text-muted-foreground mt-1">
                  Crew: {crewName}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Content Section */}
        <div className="space-y-6">
          {/* Output Section */}
          <div className="bg-card border-2 border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Output</h2>
            <div className="bg-muted border border-border rounded-lg p-4 max-h-96 overflow-y-auto">
              {selectedRun.output ? (
                <pre className="text-sm whitespace-pre-wrap font-mono">
                  {JSON.stringify(selectedRun.output, null, 2)}
                </pre>
              ) : (
                <p className="text-muted-foreground">No output available</p>
              )}
            </div>
          </div>

          {/* Artifacts Section */}
          <div className="bg-card border-2 border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Artifacts</h2>
            <div className="bg-muted border border-border rounded-lg p-4">
              {selectedRun.artifacts && selectedRun.artifacts.length > 0 ? (
                <div className="space-y-3">
                  {selectedRun.artifacts.map((artifact: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-4 bg-card border border-border rounded-lg hover:bg-accent transition-colors"
                    >
                      <div className="flex-1">
                        <p className="font-medium">
                          {artifact.file_name || "Unnamed artifact"}
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Type: {artifact.type}
                        </p>
                      </div>
                      <span className="text-sm text-muted-foreground ml-4">
                        {artifact.id}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No artifacts available</p>
              )}
            </div>
          </div>

          {/* Additional Information Section */}
          {selectedRun.created_at && (
            <div className="bg-card border-2 border-border rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4">
                Additional Information
              </h2>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Created at:</span>
                  <span className="text-muted-foreground">
                    {new Date(selectedRun.created_at).toLocaleString()}
                  </span>
                </div>
                {selectedRun.status && (
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Status:</span>
                    <span className="text-muted-foreground">
                      {selectedRun.status}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
