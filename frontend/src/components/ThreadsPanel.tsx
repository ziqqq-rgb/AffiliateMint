import { useState } from "react";
import { api } from "../api";
import type { ThreadsPost } from "../types";
import { PostActionButton } from "./PostActionButton";

interface Props {
  posts: ThreadsPost[];
  onChange: () => void;
}

export function ThreadsPanel({ posts, onChange }: Props) {
  const [busyId, setBusyId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftText, setDraftText] = useState("");

  function startEdit(post: ThreadsPost) {
    setEditingId(post.id);
    setDraftText(post.post_text);
  }

  function cancelEdit() {
    setEditingId(null);
    setDraftText("");
  }

  async function handleSaveEdit(postId: number) {
    setBusyId(postId);
    try {
      await api.updateThreadsPost(postId, draftText);
      cancelEdit();
      onChange();
    } finally {
      setBusyId(null);
    }
  }

  async function handlePostNow(post: ThreadsPost) {
    const confirmMessage = post.posted_at
      ? "Re-post this to Threads? This publishes it again as a new post."
      : "Post this to Threads now?";
    if (!window.confirm(confirmMessage)) return;

    setBusyId(post.id);
    try {
      await api.postThreadsPostNow(post.id);
      onChange();
    } finally {
      setBusyId(null);
    }
  }

  async function handleSchedule(post: ThreadsPost, isoTime: string) {
  setBusyId(post.id);
  try {
    await api.scheduleThreadsPost(post.id, isoTime);
    onChange();
  } finally {
    setBusyId(null);
  }
}

  async function handleUnschedule(post: ThreadsPost) {
    setBusyId(post.id);
    try {
      await api.unscheduleThreadsPost(post.id);
      onChange();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <h2 className="mb-4 text-sm font-semibold text-gray-900">Threads posts</h2>
      <div className="space-y-4">
        {posts.map((post) => {
          const isEditing = editingId === post.id;
          const borderClass = post.posted_at
            ? "border-gray-900"
            : post.scheduled_for
              ? "border-violet-300 bg-violet-50/30"
              : "border-gray-200";

          return (
            <div key={post.id} className={`rounded-lg border p-4 text-sm ${borderClass}`}>
              {isEditing ? (
                <div className="space-y-3">
                  <textarea
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    rows={6}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveEdit(post.id)}
                      disabled={busyId === post.id}
                      className="rounded-lg bg-gray-900 px-4 py-2 text-xs font-medium text-white hover:bg-gray-700 disabled:opacity-50"
                    >
                      {busyId === post.id ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="rounded-lg border border-gray-300 px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <p className="whitespace-pre-wrap text-gray-800">{post.post_text}</p>

                  {post.posted_at && (
                    <p className="mt-3 text-xs font-medium text-emerald-700">Posted to Threads.</p>
                  )}

                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <button
                      onClick={() => startEdit(post)}
                      className="rounded-lg border border-gray-300 px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Edit
                    </button>
                    <PostActionButton
                      isReposting={!!post.posted_at}
                      busy={busyId === post.id}
                      scheduledFor={post.scheduled_for}
                      onPostNow={() => handlePostNow(post)}
                      onSchedule={(iso) => handleSchedule(post, iso)}
                      onUnschedule={() => handleUnschedule(post)}
                    />
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}