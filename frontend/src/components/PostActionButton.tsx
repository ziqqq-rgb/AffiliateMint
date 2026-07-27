import { useRef, useState } from "react";
import { api } from "../api";
import { buildHourlySlotsUntilMidnight } from "../lib/timeSlots";

interface Props {
  isReposting: boolean;
  busy: boolean;
  scheduledFor: string | null;
  onPostNow: () => void;
  onSchedule: (isoTime: string) => Promise<void>;
  onUnschedule: () => void;
}

/**
 * Split button: click/tap posts immediately, hover reveals "Post later"
 * with hourly slots until midnight. Once a post has scheduled_for set,
 * this collapses into a "Queued for ..." pill with a cancel action.
 */
export function PostActionButton({
  isReposting,
  busy,
  scheduledFor,
  onPostNow,
  onSchedule,
  onUnschedule,
}: Props) {
  const [open, setOpen] = useState(false);
  const [takenSlots, setTakenSlots] = useState<string[]>([]);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function openMenu() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setOpen(true);
    setTakenSlots(await api.listQueueSlots());
  }

  function scheduleClose() {
    closeTimer.current = setTimeout(() => setOpen(false), 150);
  }

  async function handlePickSlot(isoTime: string) {
    try {
      await onSchedule(isoTime);
    } catch (err) {
      // Most likely someone else grabbed this exact slot between our
      // last fetch and this click - refresh so the picker reflects reality.
      window.alert(err instanceof Error ? err.message : "That time slot is no longer available");
      setTakenSlots(await api.listQueueSlots());
    }
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

  const slots = buildHourlySlotsUntilMidnight(takenSlots);
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
                  onClick={() => handlePickSlot(slot.value)}
                  disabled={slot.disabled}
                  className={`block w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                    slot.disabled
                      ? "cursor-not-allowed text-gray-300"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {slot.label}
                  {slot.disabled && <span className="ml-1.5 text-[10px] text-gray-300">taken</span>}
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