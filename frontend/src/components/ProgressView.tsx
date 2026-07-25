import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { ContentCard, Platform, ScrapedProduct } from "../types";
import { PlatformTabs } from "./PlatformTabs";
import { Spinner } from "./Spinner";
import { StatusBadge } from "./StatusBadge";
import { productSummaryLine } from "../lib/productSummaryLine";

interface ProgressRow {
  card: ContentCard;
  product?: ScrapedProduct;
}

interface Props {
  onOpenCard: (cardId: number) => void;
}

export function ProgressView({ onOpenCard }: Props) {
  const [platform, setPlatform] = useState<Platform>("tiktok");
  const [rows, setRows] = useState<ProgressRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const [cards, products] = await Promise.all([api.listCards(true), api.listProducts()]);
      const productById = Object.fromEntries(products.map((p) => [p.id, p]));
      const sorted = [...cards].sort((a, b) =>
        (b.added_to_progress_at ?? "").localeCompare(a.added_to_progress_at ?? ""),
      );
      setRows(sorted.map((card) => ({ card, product: productById[card.product_id] })));
      setLoading(false);
    }
    load();
  }, []);

  const visibleRows = useMemo(() => rows.filter((r) => r.product?.platform === platform), [rows, platform]);

  const counts = useMemo(
    () => ({
      tiktok: rows.filter((r) => r.product?.platform === "tiktok").length,
      shopee: rows.filter((r) => r.product?.platform === "shopee").length,
    }),
    [rows],
  );

  if (loading) {
    return (
      <div className="p-6">
        <Spinner label="Loading progress..." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-6">
      <PlatformTabs active={platform} onChange={setPlatform} counts={counts} />

      {visibleRows.length === 0 ? (
        <p className="text-sm text-gray-500">
          Nothing here yet - pick a product on the Board to start working on it.
        </p>
      ) : (
        visibleRows.map(({ card, product }) => (
          <ProgressCard key={card.id} card={card} product={product} onOpen={onOpenCard} />
        ))
      )}
    </div>
  );
}

function ProgressCard({
  card,
  product,
  onOpen,
}: {
  card: ContentCard;
  product?: ScrapedProduct;
  onOpen: (cardId: number) => void;
}) {
  return (
    <div>
      <p className="mb-1 px-1 text-xs text-gray-500">
        Added {card.added_to_progress_at ? new Date(card.added_to_progress_at).toLocaleDateString() : "-"}
      </p>
      <button
        onClick={() => onOpen(card.id)}
        className="flex w-full items-center gap-4 rounded-xl border border-gray-200 bg-white p-3 text-left shadow-sm transition hover:border-gray-300 hover:shadow-md"
      >
        {product?.image_url && (
          <img src={product.image_url} alt={product.title} className="h-20 w-20 shrink-0 rounded-lg object-cover" />
        )}
        <div className="min-w-0 flex-1">
          <p className="line-clamp-2 text-sm font-semibold text-gray-900">
            {product?.title ?? `Product #${card.product_id}`}
          </p>
          {product && <p className="mt-1 text-sm text-gray-600">{productSummaryLine(product)}</p>}
          {product?.shop_name && <p className="mt-1 text-xs text-gray-400">{product.shop_name}</p>}
        </div>
        <StatusBadge status={card.status} />
      </button>
    </div>
  );
}