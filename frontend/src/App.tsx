import { useEffect, useState } from "react";
import { KanbanBoard } from "./components/KanbanBoard";
import { CardDetailView } from "./components/CardDetailView";
import { ProgressView } from "./components/ProgressView";
import { QueueSidebar } from "./components/QueueSidebar";
import { api } from "./api";

type Tab = "board" | "progress";

const TABS: { id: Tab; label: string }[] = [
  { id: "board", label: "Board" },
  { id: "progress", label: "Dashboard" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("board");
  const [openCardId, setOpenCardId] = useState<number | null>(null);
  const [queueOpen, setQueueOpen] = useState(false);
  const [queueCount, setQueueCount] = useState(0);

  useEffect(() => {
    api.listQueue().then((posts) => setQueueCount(posts.length));
  }, []);

  async function handleCloseQueue() {
    setQueueOpen(false);
    setQueueCount((await api.listQueue()).length);
  }

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

        <div className="flex items-center gap-3">
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

          <button
            onClick={() => setQueueOpen(true)}
            className="relative flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
          >
            <ClockIcon />
            Queue
            {queueCount > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-violet-600 px-1 text-[10px] font-bold leading-none text-white">
                {queueCount}
              </span>
            )}
          </button>
        </div>
      </header>

      {openCardId !== null ? (
        <CardDetailView cardId={openCardId} onBack={() => setOpenCardId(null)} />
      ) : tab === "board" ? (
        <KanbanBoard />
      ) : (
        <ProgressView onOpenCard={setOpenCardId} />
      )}

      <QueueSidebar open={queueOpen} onClose={handleCloseQueue} />
    </div>
  );
}

function ClockIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.4" />
      <path d="M8 4.5V8L10.5 9.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}