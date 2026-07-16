/**
 * Kanban board - FR-4.1. Renders one column per CardStatus and fetches
 * cards from the backend. Card-level rendering lives in ContentCard.tsx;
 * this component only handles layout and data fetching.
 */
import { useEffect, useState } from "react";
import { api } from "../api";
import type { CardStatus, ContentCard as ContentCardType } from "../types";
import { ContentCard } from "./ContentCard";

const COLUMNS: { status: CardStatus; label: string }[] = [
  { status: "scraped", label: "Scraped" },
  { status: "researched_pending", label: "Researched (pending)" },
  { status: "research_approved", label: "Approved" },
  { status: "scripted_pending", label: "Scripted (pending)" },
  { status: "script_approved", label: "Approved" },
  { status: "filming", label: "Filming" },
  { status: "ready_to_post", label: "Ready to post" },
  { status: "posted", label: "Posted" },
  { status: "earnings_logged", label: "Earnings logged" },
];

export function KanbanBoard() {
  const [cards, setCards] = useState<ContentCardType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listCards()
      .then(setCards)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="p-4 text-sm text-gray-500">Loading board...</p>;

  return (
    <div className="flex gap-4 overflow-x-auto p-4">
      {COLUMNS.map((column) => (
        <div key={column.status} className="w-64 shrink-0">
          <h2 className="mb-2 text-sm font-medium text-gray-700">{column.label}</h2>
          <div className="flex flex-col gap-2">
            {cards
              .filter((card) => card.status === column.status)
              .map((card) => (
                <ContentCard key={card.id} card={card} />
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
