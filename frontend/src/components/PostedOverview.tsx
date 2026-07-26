import { useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard, ScrapedProduct, ScriptVariation, ThreadsPost } from "../types";
import { groupByDate } from "../lib/dateGroups";
import { truncate } from "../lib/textUtils";

interface Row {
  card: ContentCard;
  product?: ScrapedProduct;
}

interface Props {
  rows: Row[];
  onOpenCard: (cardId: number) => void;
}

/**
 * Shows what actually got published, and when - grouped by posted_at,
 * not added_to_progress_at, since a card can sit in progress for days
 * before it's posted. "Today" here means "posted today".
 */
export function PostedOverview({ rows, onOpenCard }: Props) {
  const postedRows = rows.filter((r) => r.card.posted_at !== null && r.product);
  const [labels, setLabels] = useState<Record<number, string>>({});

  useEffect(() => {
    let cancelled = false;
    buildPostedLabels(postedRows).then((result) => {
      if (!cancelled) setLabels(result);
    });
    return () => {
      cancelled = true;
    };
    // Only re-run when the set of posted cards actually changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postedRows.map((r) => r.card.id).join(",")]);

  if (postedRows.length === 0) return null;

  const groups = groupByDate(postedRows, (row) => row.card.posted_at);

  return (
    <section className="rounded-2xl border border-sky-100 bg-sky-50/40 p-5">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-sky-900">Posted</h2>
        <span className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-medium text-sky-800">
          {postedRows.length} total
        </span>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map((group) => (
          <PostedDateCard key={group.label} label={group.label} rows={group.items} labels={labels} onOpenCard={onOpenCard} />
        ))}
      </div>
    </section>
  );
}

function PostedDateCard({
  label,
  rows,
  labels,
  onOpenCard,
}: {
  label: string;
  rows: Row[];
  labels: Record<number, string>;
  onOpenCard: (cardId: number) => void;
}) {
  return (
    <div className="rounded-xl border border-sky-100 bg-white p-4">
      <div className="flex items-baseline justify-between">
        <p className="text-sm font-semibold text-gray-900">{label}</p>
        <span className="text-xs font-medium text-sky-700">{rows.length} posted</span>
      </div>
      <ul className="mt-3 space-y-2.5">
        {rows.map(({ card, product }) => (
          <li key={card.id}>
            <button
              onClick={() => onOpenCard(card.id)}
              className="block w-full text-left text-xs leading-snug hover:text-sky-700"
            >
              <span className="line-clamp-1 font-medium text-gray-800">
                {product?.title ?? `Product #${card.product_id}`}
              </span>
              {labels[card.id] && <span className="mt-0.5 block text-gray-500">{labels[card.id]}</span>}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Looks up which script (TikTok) or post text (Shopee) was actually
 * published for each posted card. Fetches once per product, not once
 * per card, since one product can have multiple posted rows. */
async function buildPostedLabels(postedRows: Row[]): Promise<Record<number, string>> {
  const scriptsByProduct = new Map<number, Promise<ScriptVariation[]>>();
  const threadsByProduct = new Map<number, Promise<ThreadsPost[]>>();
  const labels: Record<number, string> = {};

  await Promise.all(
    postedRows.map(async ({ card, product }) => {
      if (!product) return;

      if (product.platform === "shopee") {
        if (!threadsByProduct.has(product.id)) {
          threadsByProduct.set(product.id, api.listThreadsForProduct(product.id));
        }
        const posts = await threadsByProduct.get(product.id)!;
        const published = posts.find((p) => p.posted_at !== null);
        if (published) labels[card.id] = truncate(published.post_text, 60);
      } else {
        if (!scriptsByProduct.has(product.id)) {
          scriptsByProduct.set(product.id, api.listScriptsForProduct(product.id));
        }
        const scripts = await scriptsByProduct.get(product.id)!;
        const selected = scripts.find((s) => s.id === card.selected_script_id);
        if (selected) labels[card.id] = selected.angle_type.replace(/_/g, " ");
      }
    }),
  );

  return labels;
}