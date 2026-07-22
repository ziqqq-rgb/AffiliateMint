import type { ContentCard as ContentCardType, ScrapedProduct } from "../types";
import { formatRM } from "../lib/format";

interface Props {
  card: ContentCardType;
  product?: ScrapedProduct;
  onOpen: (cardId: number) => void;
}

export function ContentCard({ card, product, onOpen }: Props) {
  return (
    <button
      onClick={() => onOpen(card.id)}
      className="flex w-full items-center gap-4 rounded-xl border border-gray-200 bg-white p-3 text-left shadow-sm transition hover:border-gray-300 hover:shadow-md"
    >
      {product?.image_url && (
        <img src={product.image_url} alt={product.title} className="h-20 w-20 shrink-0 rounded-lg object-cover" />
      )}
      <div className="min-w-0">
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
    </button>
  );
}