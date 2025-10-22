"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";

interface Card {
  id: string;
  title: string;
  description: string;
}

export default function StudioPage() {
  const router = useRouter();
  const [cards, setCards] = useState<Card[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("fsd_token");
    if (!token) router.push("/auth/login");

    // Load cards from localStorage
    const savedCards = localStorage.getItem("studio_cards");
    if (savedCards) {
      setCards(JSON.parse(savedCards));
    }
  }, [router]);

  const handleAddCard = () => {
    // Navigate to crew page with a new untitled card
    router.push("/studio/crew?title=Untitled&description=");
  };

  const handleEditCard = (card: Card) => {
    // Navigate to crew page with existing card data
    router.push(`/studio/crew?id=${card.id}&title=${encodeURIComponent(card.title)}&description=${encodeURIComponent(card.description)}`);
  };

  const handleDeleteCard = (id: string) => {
    const updatedCards = cards.filter(card => card.id !== id);
    setCards(updatedCards);
    localStorage.setItem("studio_cards", JSON.stringify(updatedCards));
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Studio Dashboard</h1>
            <p className="text-muted-foreground">Manage your cards and projects</p>
          </div>
          <button
            onClick={handleAddCard}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
          >
            + Add Crew
          </button>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cards.map((card) => (
            <div
              key={card.id}
              className="bg-card border border-border rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer group"
              onClick={() => handleEditCard(card)}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-xl font-semibold text-card-foreground group-hover:text-primary transition-colors">
                  {card.title}
                </h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCard(card.id);
                  }}
                  className="text-muted-foreground hover:text-destructive transition-colors"
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
                </button>
              </div>
              <p className="text-muted-foreground leading-relaxed line-clamp-3">{card.description}</p>
              <div className="mt-4 text-sm text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                Click to edit →
              </div>
            </div>
          ))}
        </div>

        {cards.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No cards yet. Create your first card to get started!</p>
            <button
              onClick={handleAddCard}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
            >
              + Create First Card
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
