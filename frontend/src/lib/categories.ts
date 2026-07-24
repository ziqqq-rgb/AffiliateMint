/**
 * Fixed category list matching TikTok Shop's homepage "Categories" row
 * (see backend/scraper/navigation.py's open_category, which clicks the
 * tile by this exact label text). Kept as a flat list rather than an
 * API-driven one - TikTok Shop doesn't expose a categories endpoint we
 * scrape, and category names change rarely enough that a small edit
 * here is simpler than adding a fetch just for this dropdown.
 */
export const TIKTOK_CATEGORIES = [
  "Womenswear & Underwear",
  "Phones & Electronics",
  "Fashion Accessories",
  "Menswear & Underwear",
  "Home Supplies",
  "Beauty & Personal Care",
  "Shoes",
  "Sports & Outdoor",
  "Luggage & Bags",
] as const;

// Matches scraper/config.py's available_rating_tiers - keep these two
// lists in sync if the backend tiers ever change.
export const RATING_TIERS = [4.0, 4.5, 4.8] as const;