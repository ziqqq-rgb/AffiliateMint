import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { ContentCard, Platform, ScrapedProduct } from "../types";
import { PlatformTabs } from "./PlatformTabs";
import { Spinner } from "./Spinner";
import { productSummaryLine } from "../lib/productSummaryLine";
import { groupByDate } from "../lib/dateGroups";

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

  // One date header per day instead of repeating "Added 7/26/2026" on
  // every card - rows are already sorted newest-first above, so this
  // just clusters consecutive same-day rows together.
  const dateGroups = useMemo(
    () => groupByDate(visibleRows, (row) => row.card.added_to_progress_at),
    [visibleRows],
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
        <div className="space-y-8">
          {dateGroups.map((group) => (
            <section key={group.label}>
              <DateHeader label={group.label} count={group.items.length} />
              <div className="mt-3 space-y-3">
                {group.items.map(({ card, product }) => (
                  <ProgressCard key={card.id} card={card} product={product} onOpen={onOpenCard} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

function DateHeader({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center gap-3">
      <h2 className="shrink-0 text-sm font-semibold text-gray-900">{label}</h2>
      <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
        {count}
      </span>
      <div className="h-px flex-1 bg-gray-200" />
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
    </button>
  );
}