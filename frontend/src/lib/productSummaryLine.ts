import type { ScrapedProduct } from "../types";
import { formatRM } from "./format";

/** TikTok cards show rating+sold (no commission data on the public
 * storefront). Shopee cards show commission% instead (no public rating
 * feed from the affiliate dashboard) - see backend/README for why each
 * platform exposes different fields. */
export function productSummaryLine(product: ScrapedProduct): string {
  const price = formatRM(product.price_rm);
  if (product.platform === "shopee") {
    return `${price} · ${product.commission_rate_pct.toFixed(0)}% commission · ${product.units_sold.toLocaleString()} sold`;
  }
  return `${price} · ${product.review_score.toFixed(1)}★ (${product.review_count}) · ${product.units_sold.toLocaleString()} sold`;
}