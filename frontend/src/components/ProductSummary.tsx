import type { ScrapedProduct } from "../types";
import { formatRM } from "../lib/format";

export function ProductSummary({ product }: { product: ScrapedProduct }) {
  return (
    <div className="flex gap-4 rounded-xl border border-gray-200 bg-white p-4">
      {product.image_url && (
        <img src={product.image_url} alt={product.title} className="h-20 w-20 shrink-0 rounded-lg object-cover" />
      )}
      <div className="min-w-0">
        
          href={product.product_url}
          target="_blank"
          rel="noreferrer"
          className="text-sm font-semibold text-gray-900 hover:underline"
        >
          {product.title}
        </>
        <p className="mt-1 text-sm text-gray-600">
          {formatRM(product.price_rm)} &middot; {product.review_score.toFixed(1)}&#9733; ({product.review_count})
          &middot; {product.units_sold.toLocaleString()} sold
        </p>
        <p className="mt-1 text-xs text-gray-400">{product.shop_name}</p>
      </div>
    </div>
  );
}