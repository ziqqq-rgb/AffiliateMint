import type { ContentCard as ContentCardType, ScrapedProduct } from "../types";
import { formatRM } from "../lib/format";

interface Props {
  card: ContentCardType;
  product?: ScrapedProduct;
  busy: boolean;
  onAddToProgress: (cardId: number) => void;
}

export function BoardProductCard({ card, product, busy, onAddToProgress }: Props) {
  return (
    <div className="flex w-full items-center gap-4 rounded-xl border border-gray-200 bg-white p-3 shadow-sm">
      {product?.image_url && (
        <img src={product.image_url} alt={product.title} className="h-20 w-20 shrink-0 rounded-lg object-cover" />
      )}
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-sm font-semibold text-gray-900">
          {product?.title ?? `Product #${card.product_id}`}
        </p>
        {product && (
          <p className="mt-1 text-sm text-gray-600">
            {formatRM(product.price_rm)} &middot; {product.review_score.toFixed(1)}&#9733; ({product.review_count})
            &middot; {product.units_sold.toLocaleString()} sold
          </p>
        )}
        {product?.shop_name && <p className="mt-1 text-xs text-gray-400">{product.shop_name}</p>}
      </div>
      <button
        onClick={() => onAddToProgress(card.id)}
        disabled={busy}
        className="shrink-0 rounded-lg bg-gray-900 px-3 py-2 text-xs font-medium text-white hover:bg-gray-700 disabled:opacity-50"
      >
        {busy ? "Adding..." : "Work on this"}
      </button>
    </div>
  );
}