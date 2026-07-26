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
    <div className="min-h-screen bg-gray-50"> 
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2.5">
          <img src="/logo.svg" alt="AffiliateMint logo" className="h-15 w-18 rounded-lg" />
          <h1
            className="text-xl font-bold tracking-tight text-gray-900 -ml-8"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            AffiliateMint
          </h1>
        </div>
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
