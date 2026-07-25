import type { ScrapedProduct } from "../types";
import { formatRM } from "../lib/format";
import { CopyLinkButton } from "./CopyLinkButton";

export function ProductSummary({ product }: { product: ScrapedProduct }) {
  return (
    <div className="flex gap-4 rounded-xl border border-gray-200 bg-white p-4">
      {product.image_url && (
        <img src={product.image_url} alt={product.title} className="h-20 w-20 shrink-0 rounded-lg object-cover" />
      )}
      <div className="min-w-0 flex-1">
        <a
          href={product.product_url}
          target="_blank"
          rel="noreferrer"
          className="block text-sm font-semibold text-gray-900 hover:underline truncate"
        >
          {product.title}
        </a>

        <p className="mt-1 text-sm text-gray-600">
          {formatRM(product.price_rm)} &middot; {product.review_score.toFixed(1)}★ ({product.review_count})
          &middot; {product.units_sold.toLocaleString()} sold
        </p>
        <p className="mt-1 text-xs text-gray-400">{product.shop_name}</p>

        {product.platform === "shopee" && (
          <div className="mt-2 flex items-center gap-2">
            {product.affiliate_link ? (
              <>
                <span className="truncate text-xs text-gray-500">{product.affiliate_link}</span>
                <CopyLinkButton url={product.affiliate_link} />
              </>
            ) : (
              <span className="text-xs text-red-500">No affiliate link captured for this product</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}