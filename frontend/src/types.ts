export type CardStatus =
  | "scraped"
  | "researched_pending"
  | "research_approved"
  | "scripted_pending"
  | "script_approved"
  | "filming"
  | "ready_to_post"
  | "posted"
  | "earnings_logged";

export interface ScrapedProduct {
  id: number;
  title: string;
  price_rm: number;
  original_price_rm: number;
  review_score: number;
  review_count: number;
  units_sold: number;
  shop_name: string;
  image_url: string;
  product_url: string;
  scraped_at: string;
}

export interface ResearchDossier {
  id: number;
  product_id: number;
  what_it_does: string;
  key_benefits: string; // JSON-encoded list - JSON.parse before rendering
  usp: string;
  review_summary_positive: string;
  review_summary_negative: string;
  status: "pending" | "approved" | "rejected";
  rejection_reason: string | null;
  created_at: string;
}

export interface ScriptVariation {
  id: number;
  product_id: number;
  angle_type: string;
  hook_ms: string;
  body_ms: string;
  cta_ms: string;
  caption_ms: string;
  hashtags: string; // JSON-encoded list - JSON.parse before rendering
  visual_notes: string;
  is_selected: boolean;
}

export interface EarningsEntry {
  id: number;
  card_id: number;
  date_checked: string;
  views: number;
  likes: number;
  units_sold: number;
  commission_earned_rm: number;
  notes: string | null;
}

export interface DashboardSummary {
  total_cards: number;
  cards_by_status: Record<CardStatus, number>;
  total_commission_rm: number;
  total_views: number;
  total_units_sold: number;
  cards_missing_earnings: number;
}

export interface ContentCard {
  id: number;
  product_id: number;
  selected_script_id: number | null;
  status: CardStatus;
  filmed_at: string | null;
  posted_at: string | null;
  tiktok_video_url: string | null;
  is_generating: boolean;
  used_auto_pipeline: boolean;
  added_to_progress_at: string | null;
}

export interface ScrapeFilters {
  category: string | null;
  min_rating: number | null;
  sort_by_sold: boolean;
  min_price: number | null;
  max_price: number | null;
}

export const EMPTY_FILTERS: ScrapeFilters = {
  category: null,
  min_rating: null,
  sort_by_sold: false,
  min_price: null,
  max_price: null,
};