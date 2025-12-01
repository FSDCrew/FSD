"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CrewRead, getAllCrewsCrewGet, syncUserUserSyncPost, deleteCrewCrewCrewIdDelete } from "@/lib/api/crud";
import { client } from "@/lib/api/crud/client.gen";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

export default function StudioPage() {
  const router = useRouter();
  const { isAuthenticated, token } = useAuth();
  const queryClient = useQueryClient();
  
  const { data: user } = useQuery({
    queryKey: ['user'],
    queryFn: () => syncUserUserSyncPost(),
    enabled: isAuthenticated,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['crews'],
    queryFn: () => getAllCrewsCrewGet({ responseStyle: 'data' }),
  })
  const crews = Array.isArray(data) ? data : data ? [data] : [];

  const handleAddCard = () => {
    router.push("/studio/crew?title=Untitled&description=");
  };

  const handleEditCard = (crew: CrewRead) => {
    // Navigate to crew page with existing card data
    router.push(`/studio/crew?id=${crew.id}&title=${encodeURIComponent(crew.name)}`);
  };

  const deleteMutation = useMutation({
    mutationFn: async (crewId: string) => {
      return await deleteCrewCrewCrewIdDelete({
        path: { crew_id: crewId }
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crews'] });
      toast.success("Crew deleted successfully");
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete crew: ${error.message}`);
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Studio Dashboard</h1>
            <p className="text-muted-foreground">Manage your Crews</p>
          </div>
          <Button
            onClick={handleAddCard}
            variant="default"
          >
            + Add Crew
          </Button>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {crews.map((crew) => (
            <div
              key={crew.id}
              className="bg-card border border-border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer group"
              onClick={() => handleEditCard(crew)}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-xl font-semibold text-card-foreground group-hover:text-primary transition-colors">
                  {crew.name}
                </h3>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                      variant="ghost"
                      size="icon-sm"
                      className="text-muted-foreground hover:text-destructive"
                      title="Delete crew"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
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
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent onClick={(e) => e.stopPropagation()}>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete Crew</AlertDialogTitle>
                      <AlertDialogDescription>
                        Are you sure you want to delete <strong>{crew.name}</strong>? This action cannot be undone and will permanently remove this crew and all its data.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction 
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteMutation.mutate(crew.id);
                        }}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        disabled={deleteMutation.isPending}
                      >
                        {deleteMutation.isPending ? "Deleting..." : "Delete"}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
              <div className="mt-4 text-sm text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                Click to edit →
              </div>
            </div>
          ))}
        </div>

        {crews.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No crews yet. Create your first crew to get started!</p>
            <button
              onClick={handleAddCard}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
            >
              + Create First Crew
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
