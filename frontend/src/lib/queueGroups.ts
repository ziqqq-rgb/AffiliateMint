import type { QueuedPost } from "../types";

export interface QueueGroup {
  label: string;
  items: QueuedPost[];
}

export function groupQueueByDay(posts: QueuedPost[]): QueueGroup[] {
  const groups: QueueGroup[] = [];

  for (const post of posts) {
    const label = dayLabel(new Date(post.scheduled_for));
    const last = groups[groups.length - 1];
    if (last && last.label === label) {
      last.items.push(post);
    } else {
      groups.push({ label, items: [post] });
    }
  }

  return groups;
}

function dayLabel(date: Date): string {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  if (isSameDay(date, today)) return "Today";
  if (isSameDay(date, tomorrow)) return "Tomorrow";
  return date.toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
}

function isSameDay(a: Date, b: Date): boolean {
  return a.toDateString() === b.toDateString();
}