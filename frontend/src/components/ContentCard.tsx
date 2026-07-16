/** One Kanban card - FR-4.2. Shows a summary; the full-detail click-through
 * view (product + research + script) is intentionally left for a later pass. */
import type { ContentCard as ContentCardType } from "../types";

export function ContentCard({ card }: { card: ContentCardType }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
      <p className="text-sm font-medium">Product #{card.product_id}</p>
      <p className="text-xs text-gray-500">Card #{card.id}</p>
    </div>
  );
}
