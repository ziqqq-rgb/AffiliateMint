import { useEffect, useState } from "react";
import { api } from "../api";
import type { QueuedPost } from "../types";
import { groupQueueByDay } from "../lib/queueGroups";
import { formatRelativeTime } from "../lib/timeSlots";
import { Spinner } from "./Spinner";

interface Props {
  open: boolean;
  onClose: () => void;
}

const PLATFORM_BADGE: Record<string, string> = {
  shopee: "bg-orange-100 text-orange-700",
  tiktok: "bg-rose-100 text-rose-700",
};

export function QueueSidebar({ open, onClose }: Props) {
  const [posts, setPosts] = useState<QueuedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setPosts(await api.listQueue());
    setLoading(false);
  }

  useEffect(() => {
    if (open) load();
  }, [open]);

  async function handleCancel(postId: number) {
    setBusyId(postId);
    try {
      await api.unscheduleThreadsPost(postId);
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function handlePostNow(postId: number) {
    setBusyId(postId);
    try {
      await api.postThreadsPostNow(postId);
      await load();
    } finally {
      setBusyId(null);
    }
  }

  const groups = groupQueueByDay(posts);

  return (
    <>
      <div
        onClick={onClose}
        className={`fixed inset-0 z-30 bg-gray-900/20 backdrop-blur-[2px] transition-opacity duration-300 ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />

      <aside
        className={`fixed right-0 top-0 z-40 flex h-full w-full max-w-md flex-col border-l border-gray-200 bg-white shadow-2xl transition-transform duration-300 ease-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <header className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
          <div>
            <h2 className="text-base font-bold text-gray-900">Post queue</h2>
            <p className="text-xs text-gray-500">{posts.length} scheduled</p>
          </div>
          <button onClick={onClose} className="rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700">
            <CloseIcon />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading ? (
            <Spinner label="Loading queue..." />
          ) : posts.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="space-y-6">
              {groups.map((group) => (
                <div key={group.label}>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">{group.label}</p>
                  <div className="space-y-3">
                    {group.items.map((post) => (
                      <QueueItem
                        key={post.post_id}
                        post={post}
                        busy={busyId === post.post_id}
                        onCancel={() => handleCancel(post.post_id)}
                        onPostNow={() => handlePostNow(post.post_id)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

function QueueItem({
  post,
  busy,
  onCancel,
  onPostNow,
}: {
  post: QueuedPost;
  busy: boolean;
  onCancel: () => void;
  onPostNow: () => void;
}) {
  const scheduledDate = new Date(post.scheduled_for);
  const badgeClass = PLATFORM_BADGE[post.platform] ?? "bg-gray-100 text-gray-600";

  return (
    <div className="group rounded-2xl border border-gray-100 bg-gray-50/60 p-3 transition hover:border-gray-200 hover:bg-white hover:shadow-sm">
      <div className="flex gap-3">
        {post.product_image_url && (
          <img
            src={post.product_image_url}
            alt={post.product_title}
            className="h-14 w-14 shrink-0 rounded-xl object-cover"
          />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase ${badgeClass}`}>
              {post.platform}
            </span>
            <p className="truncate text-xs font-medium text-gray-500">{post.product_title}</p>
          </div>
          <p className="mt-1 line-clamp-2 text-sm text-gray-800">{post.post_text}</p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-2">
        <div className="flex items-baseline gap-1.5">
          <span className="text-sm font-semibold text-gray-900">
            {scheduledDate.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}
          </span>
          <span className="text-xs text-gray-400">{formatRelativeTime(scheduledDate)}</span>
        </div>
        <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            onClick={onPostNow}
            disabled={busy}
            className="rounded-lg px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
          >
            Post now
          </button>
          <button
            onClick={onCancel}
            disabled={busy}
            className="rounded-lg px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center py-16 text-center">
      <div className="mb-3 rounded-full bg-gray-100 p-4">
        <ClockIcon />
      </div>
      <p className="text-sm font-medium text-gray-700">No posts queued</p>
      <p className="mt-1 max-w-[220px] text-xs text-gray-400">
        Hover "Post this" on any Threads post and choose "Post later" to schedule it.
      </p>
    </div>
  );
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="7.5" stroke="#9CA3AF" strokeWidth="1.5" />
      <path d="M10 5.5V10L13 12" stroke="#9CA3AF" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}