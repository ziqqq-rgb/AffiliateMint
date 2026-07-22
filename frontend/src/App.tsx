// frontend/src/App.tsx
import { useState } from "react";
import { KanbanBoard } from "./components/KanbanBoard";
import { CardDetailView } from "./components/CardDetailView";

export default function App() {
  const [openCardId, setOpenCardId] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
      <header className="border-b border-gray-200 bg-white px-4 py-3">
        <h1 className="text-lg font-semibold tracking-tight">TikTok Shop Affiliate AI Engine</h1>
      </header>

      {openCardId === null ? (
        <KanbanBoard onOpenCard={setOpenCardId} />
      ) : (
        <CardDetailView cardId={openCardId} onBack={() => setOpenCardId(null)} />
      )}
    </div>
  );
}