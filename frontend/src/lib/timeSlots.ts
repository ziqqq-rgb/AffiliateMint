export interface TimeSlot {
  label: string;
  value: string; 
  disabled: boolean; 
}

const END_OF_DAY_HOUR = 23;
const END_OF_DAY_MINUTE = 59;

/**
 * Hourly slots from the next full hour after `from` until 11:59 PM the
 * same day. Always appends an explicit "end of day" slot so the last
 * partial hour of the day is reachable even when it isn't a round hour
 * away. Returns [] once it's already past 11:59 PM - callers never
 * need to special-case "no slots left today".
 *
 * takenSlots are ISO strings (from GET /threads/queue/slots) - compared
 * by timestamp, not string equality, since backend/frontend ISO
 * formatting can differ in precision.
 */
export function buildHourlySlotsUntilMidnight(takenSlots: string[] = [], from: Date = new Date()): TimeSlot[] {
  const endOfDay = new Date(from);
  endOfDay.setHours(END_OF_DAY_HOUR, END_OF_DAY_MINUTE, 0, 0);

  if (from >= endOfDay) return [];

  const takenTimestamps = new Set(takenSlots.map((iso) => new Date(iso).getTime()));

  const slots: TimeSlot[] = [];
  const cursor = new Date(from);
  cursor.setMinutes(0, 0, 0);
  cursor.setHours(cursor.getHours() + 1);

  while (cursor < endOfDay) {
    slots.push({
      label: formatClock(cursor),
      value: cursor.toISOString(),
      disabled: takenTimestamps.has(cursor.getTime()),
    });
    cursor.setHours(cursor.getHours() + 1);
  }

  slots.push({
    label: `${formatClock(endOfDay)} (end of day)`,
    value: endOfDay.toISOString(),
    disabled: takenTimestamps.has(endOfDay.getTime()),
  });

  return slots;
}

function formatClock(date: Date): string {
  return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

/** "in 45m" / "in 2h 10m" - used by the queue sidebar countdown. */
export function formatRelativeTime(target: Date, now: Date = new Date()): string {
  const diffMs = target.getTime() - now.getTime();
  if (diffMs <= 0) return "due now";

  const totalMinutes = Math.round(diffMs / 60000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0) return `in ${minutes}m`;
  if (minutes === 0) return `in ${hours}h`;
  return `in ${hours}h ${minutes}m`;
}