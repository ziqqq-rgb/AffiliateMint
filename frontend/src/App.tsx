import { useState } from "react";
import { KanbanBoard } from "./components/KanbanBoard";
import { CardDetailView } from "./components/CardDetailView";
import { Dashboard } from "./components/Dashboard";
import { ProgressView } from "./components/ProgressView";

type Tab = "board" | "dashboard" | "progress";

const TABS: { id: Tab; label: string }[] = [
  { id: "board", label: "Board" },
  { id: "dashboard", label: "Dashboard" },
  { id: "progress", label: "Progress" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("board");
  const [openCardId, setOpenCardId] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
        <h1 className="text-lg font-semibold tracking-tight">TikTok Shop Affiliate AI Engine</h1>
        {openCardId === null && (
          <nav className="flex gap-1 rounded-lg bg-gray-100 p-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                  tab === t.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-900"
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        )}
      </header>

      {openCardId !== null ? (
        <CardDetailView cardId={openCardId} onBack={() => setOpenCardId(null)} />
      ) : tab === "board" ? (
        <KanbanBoard />
      ) : tab === "dashboard" ? (
        <Dashboard />
      ) : (
        <ProgressView onOpenCard={setOpenCardId} />
      )}
    </div>
  );
}