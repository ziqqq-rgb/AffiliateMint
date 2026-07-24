import { useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard, ScrapedProduct } from "../types";
import { Spinner } from "./Spinner";
import { StatusBadge } from "./StatusBadge";

interface ProgressRow {
  card: ContentCard;
  product?: ScrapedProduct;
}

interface Props {
  onOpenCard: (cardId: number) => void;
}

export function ProgressView({ onOpenCard }: Props) {
  const [rows, setRows] = useState<ProgressRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [cards, products] = await Promise.all([api.listCards(true), api.listProducts()]);
      const productById = Object.fromEntries(products.map((p) => [p.id, p]));

      // Latest added first
      const sorted = [...cards].sort((a, b) =>
        (b.added_to_progress_at ?? "").localeCompare(a.added_to_progress_at ?? ""),
      );
      setRows(sorted.map((card) => ({ card, product: productById[card.product_id] })));
      setLoading(false);
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <Spinner label="Loading progress..." />
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <p className="p-6 text-sm text-gray-500">
        Nothing here yet - pick a product on the Board to start working on it.
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-2 p-6">
      {rows.map(({ card, product }) => (
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
              Added {card.added_to_progress_at ? new Date(card.added_to_progress_at).toLocaleDateString() : "-"}
            </p>
          </div>
          <StatusBadge status={card.status} />
        </button>
      ))}
    </div>
  );
}
