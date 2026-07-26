export interface DateGroup<T> {
  label: string;
  items: T[];
}

export function groupByDate<T>(items: T[], getDateString: (item: T) => string | null): DateGroup<T>[] {
  const groups: DateGroup<T>[] = [];

  for (const item of items) {
    const label = formatGroupLabel(getDateString(item));
    const lastGroup = groups[groups.length - 1];

    if (lastGroup && lastGroup.label === label) {
      lastGroup.items.push(item);
    } else {
      groups.push({ label, items: [item] });
    }
  }

  return groups;
}

function formatGroupLabel(dateString: string | null): string {
  if (!dateString) return "Unknown date";

  const date = new Date(dateString);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (isSameDay(date, today)) return "Today";
  if (isSameDay(date, yesterday)) return "Yesterday";

  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function isSameDay(a: Date, b: Date): boolean {
  return a.toDateString() === b.toDateString();
}