import { useState } from "react";
import { api } from "../api";
import type { ContentCard, ThreadsPost } from "../types";

interface Props {
  card: ContentCard;
  posts: ThreadsPost[];
  onChange: () => void;
}

export function ThreadsPanel({ card, posts, onChange }: Props) {
  const [busyId, setBusyId] = useState<number | null>(null);
  const [publishing, setPublishing] = useState(false);

  async function handleSelect(postId: number) {
    setBusyId(postId);
    try {
      await api.selectThreadsPost(postId);
      onChange();
    } finally {
      setBusyId(null);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    try {
      await api.publishThreadsPost(card.id);
      onChange();
    } finally {
      setPublishing(false);
    }
  }

  const selected = posts.find((p) => p.is_selected);

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <h2 className="mb-4 text-sm font-semibold text-gray-900">Threads posts</h2>
      <div className="space-y-4">
        {posts.map((post) => (
          <div
            key={post.id}
            className={`rounded-lg border p-4 text-sm whitespace-pre-wrap ${
              post.is_selected ? "border-gray-900" : "border-gray-200"
            }`}
          >
            <p className="text-gray-800">{post.post_text}</p>
            {!post.is_selected && (
              <button
                onClick={() => handleSelect(post.id)}
                disabled={busyId === post.id}
                className="mt-3 rounded-lg border border-gray-300 px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                {busyId === post.id ? "Selecting..." : "Use this one"}
              </button>
            )}
          </div>
        ))}
      </div>

      {selected && !selected.posted_at && (
        <button
          onClick={handlePublish}
          disabled={publishing}
          className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
        >
          {publishing ? "Publishing..." : "Publish to Threads"}
        </button>
      )}

      {selected?.posted_at && <p className="mt-4 text-sm text-emerald-700">Posted to Threads.</p>}
    </section>
  );
}