import type { ContentCard } from "../types";

export interface DailyPostCount {
  dateKey: string; // yyyy-mm-dd, used only for internal grouping
  label: string; // what's shown on the chart axis
  count: number;
}

const DAY_MS = 24 * 60 * 60 * 1000;

function dateKey(d: Date): string {
  return d.toISOString().slice(0, 10);
}

/**
 * Builds a fixed 7-day trailing window (oldest -> newest, ending today).
 * Days with zero posts still appear as zero-height bars, so the chart
 * shows real gaps in activity rather than silently compressing them.
 */
export function buildLast7DaysSeries(cards: ContentCard[]): DailyPostCount[] {
  const countsByDay = new Map<string, number>();

  for (const card of cards) {
    if (!card.posted_at) continue;
    const key = dateKey(new Date(card.posted_at));
    countsByDay.set(key, (countsByDay.get(key) ?? 0) + 1);
  }

  const today = new Date();
  const series: DailyPostCount[] = [];

  for (let i = 6; i >= 0; i--) {
    const day = new Date(today.getTime() - i * DAY_MS);
    const key = dateKey(day);
    series.push({
      dateKey: key,
      label: i === 0 ? "Today" : day.toLocaleDateString(undefined, { weekday: "short" }),
      count: countsByDay.get(key) ?? 0,
    });
  }

  return series;
}

export function countPostedDaysAgo(cards: ContentCard[], daysAgo: number): number {
  const target = new Date();
  target.setDate(target.getDate() - daysAgo);
  const key = dateKey(target);
  return cards.filter((c) => c.posted_at && dateKey(new Date(c.posted_at)) === key).length;
}

export function countPostedTotal(cards: ContentCard[]): number {
  return cards.filter((c) => c.posted_at !== null).length;
}