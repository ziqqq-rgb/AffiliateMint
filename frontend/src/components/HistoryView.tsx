import { useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard, EarningsEntry, ScrapedProduct } from "../types";
import { Spinner } from "./Spinner";
import { formatRM } from "../lib/format";

interface HistoryRow {
  card: ContentCard;
  product?: ScrapedProduct;
  latestEarnings?: EarningsEntry;
}

interface Props {
  onOpenCard: (cardId: number) => void;
}

export function HistoryView({ onOpenCard }: Props) {
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [cards, products] = await Promise.all([api.listCards(), api.listProducts()]);
      const productById = Object.fromEntries(products.map((p) => [p.id, p]));
      const completed = cards.filter((c) => c.status === "earnings_logged");

      const withEarnings = await Promise.all(
        completed.map(async (card) => {
          const entries = await api.listEarningsForCard(card.id);
          return { card, product: productById[card.product_id], latestEarnings: entries[0] };
        }),
      );

      withEarnings.sort((a, b) => (b.card.posted_at ?? "").localeCompare(a.card.posted_at ?? ""));
      setRows(withEarnings);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <Spinner label="Loading history..." />
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <p className="p-6 text-sm text-gray-500">
        No completed cards yet - log earnings on a posted card to see it here.
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-2 p-6">
      {rows.map(({ card, product, latestEarnings }) => (
        <button
          key={card.id}
          onClick={() => onOpenCard(card.id)}
          className="flex w-full items-center justify-between rounded-xl border border-gray-200 bg-white p-4 text-left shadow-sm transition hover:border-gray-300 hover:shadow-md"
        >
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-gray-900">
              {product?.title ?? `Product #${card.product_id}`}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              Posted {card.posted_at ? new Date(card.posted_at).toLocaleDateString() : "-"}
            </p>
          </div>
          {latestEarnings && (
            <div className="shrink-0 text-right">
              <p className="text-sm font-semibold text-emerald-700">{formatRM(latestEarnings.commission_earned_rm)}</p>
              <p className="text-xs text-gray-500">
                {latestEarnings.views.toLocaleString()} views &middot; {latestEarnings.units_sold} sold
              </p>
            </div>
          )}
        </button>
      ))}
    </div>
  );
}