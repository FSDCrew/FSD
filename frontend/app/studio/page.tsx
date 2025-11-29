"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import { Button } from "@/components/ui/button";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CrewRead, getAllCrewsCrewGet, syncUserUserSyncPost } from "@/lib/api/crud";
import { client } from "@/lib/api/crud/client.gen";

export default function StudioPage() {
  const router = useRouter();
  const { isAuthenticated, token } = useAuth();
  const queryClient = useQueryClient();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [crewToDelete, setCrewToDelete] = useState<CrewRead | null>(null);
  const [notification, setNotification] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);
  
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
      const response = await fetch(`${client.getConfig().baseUrl}/crew/${crewId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete crew');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crews'] });
      showNotification("Crew deleted successfully", "success");
      setShowDeleteConfirm(false);
      setCrewToDelete(null);
    },
    onError: (error: Error) => {
      showNotification(`Failed to delete crew: ${error.message}`, "error");
    },
  });

  const handleDeleteCard = (crew: CrewRead) => {
    setCrewToDelete(crew);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = () => {
    if (crewToDelete) {
      deleteMutation.mutate(crewToDelete.id);
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
    setCrewToDelete(null);
  };

  const showNotification = (message: string, type: "success" | "error" | "info" = "info") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };  

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
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCard(crew);
                  }}
                  variant="ghost"
                  size="icon-sm"
                  className="text-muted-foreground hover:text-destructive"
                  title="Delete card"
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

        {/* Notification */}
        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && crewToDelete && (
          <div className="fixed inset-0 bg-background/10 backdrop-blur-sm flex items-center justify-center z-50">
            {/* blur bg --> fixed inset-0 bg-background/10 backdrop-blur-sm flex items-center justify-center z-50
            grey bg --> fixed inset-0 bg-black/50 flex items-center justify-center z-50 */}
            <div className="bg-card border border-border rounded-lg p-6 max-w-md w-full mx-4 shadow-2xl">
              <h3 className="text-xl font-semibold mb-4">Delete Crew</h3>
              <p className="text-muted-foreground mb-6">
                Are you sure you want to delete <strong>{crewToDelete.name}</strong>? This action cannot be undone.
              </p>
              <div className="flex gap-3 justify-end">
                <Button
                  onClick={cancelDelete}
                  variant="secondary"
                  disabled={deleteMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  onClick={confirmDelete}
                  variant="destructive"
                  disabled={deleteMutation.isPending}
                >
                  {deleteMutation.isPending ? "Deleting..." : "Delete"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Notification Toast */}
        {notification && (
          <div 
            className={`fixed top-20 right-6 z-[60] px-6 py-4 rounded-lg shadow-lg border-2 animate-in slide-in-from-top-5 duration-300 ${
              notification.type === "success" 
                ? "bg-green-50 border-green-500 text-green-800" 
                : notification.type === "error"
                ? "bg-red-50 border-red-500 text-red-800"
                : "bg-blue-50 border-blue-500 text-blue-800"
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">
                {notification.type === "success" ? "✅" : notification.type === "error" ? "❌" : "ℹ️"}
              </span>
              <span className="font-medium">{notification.message}</span>
              <button 
                onClick={() => setNotification(null)}
                className="ml-4 text-xl hover:opacity-70"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
