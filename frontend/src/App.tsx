import { KanbanBoard } from "./components/KanbanBoard";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-4 py-3">
        <h1 className="text-lg font-medium">TikTok Shop Affiliate AI Engine</h1>
      </header>
      <KanbanBoard />
    </div>
  );
}
