/**
 * Mirrors backend/app/models.py. Kept as one file since the shapes are
 * small and it's the single source of truth the frontend checks
 * against when the backend schema changes.
 */

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
  commission_percentage: number;
  est_commission_rm: number;
  review_score: number;
  stock_volume: number;
  units_sold: number;
  product_url: string;
  scraped_at: string;
}

export interface ResearchDossier {
  id: number;
  product_id: number;
  what_it_does: string;
  key_benefits: string[];
  usp: string;
  review_summary_positive: string;
  review_summary_negative: string;
  status: "pending" | "approved" | "rejected";
  rejection_reason: string | null;
}

export interface ScriptVariation {
  id: number;
  product_id: number;
  angle_type: string;
  hook_ms: string;
  body_ms: string;
  cta_ms: string;
  caption_ms: string;
  hashtags: string[];
  visual_notes: string;
  is_selected: boolean;
}

export interface ContentCard {
  id: number;
  product_id: number;
  selected_script_id: number | null;
  status: CardStatus;
  filmed_at: string | null;
  posted_at: string | null;
  tiktok_video_url: string | null;
}
