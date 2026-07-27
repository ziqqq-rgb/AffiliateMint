export interface TimeSlot {
  label: string;
  value: string; // ISO datetime string
}

const END_OF_DAY_HOUR = 23;
const END_OF_DAY_MINUTE = 59;

export function buildHourlySlotsUntilMidnight(from: Date = new Date()): TimeSlot[] {
  const endOfDay = new Date(from);
  endOfDay.setHours(END_OF_DAY_HOUR, END_OF_DAY_MINUTE, 0, 0);

  if (from >= endOfDay) return [];

  const slots: TimeSlot[] = [];
  const cursor = new Date(from);
  cursor.setMinutes(0, 0, 0);
  cursor.setHours(cursor.getHours() + 1);

  while (cursor < endOfDay) {
    slots.push({ label: formatClock(cursor), value: cursor.toISOString() });
    cursor.setHours(cursor.getHours() + 1);
  }

  slots.push({ label: `${formatClock(endOfDay)} (end of day)`, value: endOfDay.toISOString() });
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