import { useRef, useState } from "react";
import { buildHourlySlotsUntilMidnight } from "../lib/timeSlots";

interface Props {
  isReposting: boolean;
  busy: boolean;
  scheduledFor: string | null;
  onPostNow: () => void;
  onSchedule: (isoTime: string) => void;
  onUnschedule: () => void;
}

export function PostActionButton({
  isReposting,
  busy,
  scheduledFor,
  onPostNow,
  onSchedule,
  onUnschedule,
}: Props) {
  const [open, setOpen] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function openMenu() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setOpen(true);
  }

  function scheduleClose() {
    closeTimer.current = setTimeout(() => setOpen(false), 150);
  }

  if (scheduledFor) {
    const when = new Date(scheduledFor).toLocaleString(undefined, {
      weekday: "short",
      hour: "numeric",
      minute: "2-digit",
    });
    return (
      <div className="flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-medium text-violet-700">
        Queued for {when}
        <button onClick={onUnschedule} disabled={busy} className="text-violet-500 hover:text-violet-800 disabled:opacity-50">
          Cancel
        </button>
      </div>
    );
  }

  const slots = buildHourlySlotsUntilMidnight();
  const label = isReposting ? "Repost" : "Post this";

  return (
    <div className="relative inline-block" onMouseEnter={openMenu} onMouseLeave={scheduleClose}>
      <button
        onClick={onPostNow}
        disabled={busy}
        className="flex items-center gap-1 rounded-lg bg-gray-900 px-4 py-2 text-xs font-medium text-white hover:bg-gray-700 disabled:opacity-50"
      >
        {busy ? "Posting..." : label}
        <ChevronIcon />
      </button>

      {open && !busy && (
        <div className="absolute right-0 z-20 mt-1 w-56 rounded-xl border border-gray-200 bg-white p-2 shadow-lg">
          <button
            onClick={onPostNow}
            className="block w-full rounded-lg px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
          >
            Post now
          </button>

          <div className="my-1 h-px bg-gray-100" />
          <p className="px-3 py-1 text-xs font-medium uppercase tracking-wide text-gray-400">Post later</p>

          <div className="max-h-56 overflow-y-auto">
            {slots.length === 0 ? (
              <p className="px-3 py-2 text-xs text-gray-400">No slots left today</p>
            ) : (
              slots.map((slot) => (
                <button
                  key={slot.value}
                  onClick={() => onSchedule(slot.value)}
                  className="block w-full rounded-lg px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                >
                  {slot.label}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ChevronIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}