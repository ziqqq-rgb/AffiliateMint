import type { ContentCard as ContentCardType, ScrapedProduct } from "../types";
import { productSummaryLine } from "../lib/productSummaryLine";

interface Props {
  card: ContentCardType;
  product?: ScrapedProduct;
  busy: boolean;
  isRemoving: boolean;
  onAddToProgress: (cardId: number) => void;
}

export function BoardProductCard({ card, product, busy, isRemoving, onAddToProgress }: Props) {
  return (
    <div
      className={`flex w-full items-center gap-4 rounded-xl border border-gray-200 bg-white p-3 shadow-sm transition-all duration-300 ease-in ${
        isRemoving ? "pointer-events-none -translate-x-3 scale-95 opacity-0" : "translate-x-0 scale-100 opacity-100"
      }`}
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
        {product?.platform === "shopee" && product.commission_rate_pct > 0 && (
          <span className="inline-block rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
            {product.commission_rate_pct.toFixed(0)}% comm
          </span>
        )}
      </div>
      <button
        onClick={() => onAddToProgress(card.id)}
        disabled={busy || isRemoving}
        className="shrink-0 rounded-lg border-2 border-gray-900 bg-transparent px-3 py-2 text-xs font-medium text-gray-900 transition hover:bg-gray-900 hover:text-white disabled:opacity-50"
      >
        {isRemoving ? "Added ✓" : busy ? "Adding..." : "Work on this"}
      </button>
    </div>
  );
}