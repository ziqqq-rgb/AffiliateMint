import type { ContentCard as ContentCardType, ScrapedProduct } from "../types";
import { StatusBadge } from "./StatusBadge";
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
      className="w-full rounded-xl border border-gray-200 bg-white p-3 text-left shadow-sm transition hover:border-gray-300 hover:shadow-md"
    >
      <p className="line-clamp-2 text-sm font-semibold text-gray-900">
        {product?.title ?? `Product #${card.product_id}`}
      </p>
      {product && (
        <p className="mt-1 text-xs text-gray-500">
          {formatRM(product.price_rm)} &middot; {product.units_sold.toLocaleString()} sold
        </p>
      )}
      <div className="mt-2">
        <StatusBadge status={card.status} />
      </div>
    </button>
  );
}