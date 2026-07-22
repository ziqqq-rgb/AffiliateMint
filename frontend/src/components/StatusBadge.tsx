import type { CardStatus } from "../types";
import { STATUS_META } from "../lib/statusMeta";

export function StatusBadge({ status }: { status: CardStatus }) {
  const meta = STATUS_META[status];
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  );
}