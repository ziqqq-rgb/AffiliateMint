import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { ContentCard, Platform, ScrapedProduct } from "../types";
import { PlatformTabs } from "./PlatformTabs";
import { PlatformAnalytics } from "./PlatformAnalytics";
import { Spinner } from "./Spinner";
import { productSummaryLine } from "../lib/productSummaryLine";
import { groupByDate } from "../lib/dateGroups";
import { isResearched, isPosted } from "../lib/cardProgress";

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

  const dateGroups = useMemo(
    () => groupByDate(visibleRows, (row) => row.card.added_to_progress_at),
    [visibleRows],
  );

   if (loading) {
    return (
      <div className="p-6">
        <Spinner label="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <PlatformTabs active={platform} onChange={setPlatform} counts={counts} />

      <PlatformAnalytics platform={platform} cards={visibleRows.map((r) => r.card)} />

      {visibleRows.length === 0 ? (
        <p className="text-sm text-gray-500">
          Nothing here yet - pick a product on the Board to start working on it.
        </p>
      ) : (
        <div className="space-y-10">
          {dateGroups.map((group) => (
            <DateSection key={group.label} label={group.label} rows={group.items} onOpenCard={onOpenCard} />
          ))}
        </div>
      )}
    </div>
  );
}

function DateSection({
  label,
  rows,
  onOpenCard,
}: {
  label: string;
  rows: ProgressRow[];
  onOpenCard: (cardId: number) => void;
}) {
  const researchedRows = rows.filter((r) => isResearched(r.card.status));
  const pendingRows = rows.filter((r) => !isResearched(r.card.status));

  return (
    <section>
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-base font-semibold text-gray-900">{label}</h2>
        <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
          {rows.length} total
        </span>
        <div className="h-px flex-1 bg-gray-200" />
      </div>

      <div className="mt-4 space-y-6">
        <CardGroup title="Researched & scripted" tone="emerald" rows={researchedRows} onOpenCard={onOpenCard} />
        <CardGroup title="Awaiting research" tone="amber" rows={pendingRows} onOpenCard={onOpenCard} />
      </div>
    </section>
  );
}

const GROUP_PILL_STYLES = {
  emerald: "bg-emerald-50 text-emerald-800 border-emerald-200",
  amber: "bg-amber-50 text-amber-800 border-amber-200",
} as const;

function CardGroup({
  title,
  tone,
  rows,
  onOpenCard,
}: {
  title: string;
  tone: keyof typeof GROUP_PILL_STYLES;
  rows: ProgressRow[];
  onOpenCard: (cardId: number) => void;
}) {
  if (rows.length === 0) return null;

  return (
    <div>
      <span
        className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${GROUP_PILL_STYLES[tone]}`}
      >
        {title}
        <span className="opacity-70">· {rows.length}</span>
      </span>

      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {rows.map(({ card, product }) => (
          <ProgressCard key={card.id} card={card} product={product} onOpen={onOpenCard} />
        ))}
      </div>
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
      className="flex w-full items-center gap-5 rounded-2xl border border-gray-200 bg-white p-5 text-left shadow-sm transition hover:border-gray-300 hover:shadow-md"
    >
      {product?.image_url && (
        <img src={product.image_url} alt={product.title} className="h-28 w-28 shrink-0 rounded-xl object-cover" />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="line-clamp-2 text-base font-semibold text-gray-900">
            {product?.title ?? `Product #${card.product_id}`}
          </p>
          {isPosted(card) && (
            <span className="shrink-0 rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-800">
              Posted
            </span>
          )}
        </div>
        {product && <p className="mt-2 text-sm text-gray-600">{productSummaryLine(product)}</p>}
        {product?.shop_name && <p className="mt-1.5 text-xs text-gray-400">{product.shop_name}</p>}
      </div>
    </button>
  );
}