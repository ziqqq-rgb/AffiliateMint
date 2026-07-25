import type { ScrapedProduct } from "../types";

/** TikTok cards link straight to the product page (no tracked-link
 * concept on the public storefront). Shopee cards must use
 * affiliate_link - product_url there is just the plain page, which
 * doesn't count as a tracked click for commission. */
export function getCardLinkUrl(product: ScrapedProduct): string {
  if (product.platform === "shopee") {
    return product.affiliate_link || product.product_url;
  }
  return product.product_url;
}