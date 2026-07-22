import type { CardStatus } from "../types";

interface StatusMeta {
  label: string;
  color: string; 
}

export const STATUS_META: Record<CardStatus, StatusMeta> = {
  scraped: { label: "Scraped", color: "bg-slate-100 text-slate-700" },
  researched_pending: { label: "Research pending", color: "bg-amber-100 text-amber-800" },
  research_approved: { label: "Research approved", color: "bg-emerald-100 text-emerald-800" },
  scripted_pending: { label: "Scripts pending", color: "bg-amber-100 text-amber-800" },
  script_approved: { label: "Ready to film", color: "bg-emerald-100 text-emerald-800" },
  filming: { label: "Filming", color: "bg-indigo-100 text-indigo-800" },
  ready_to_post: { label: "Ready to post", color: "bg-indigo-100 text-indigo-800" },
  posted: { label: "Posted", color: "bg-sky-100 text-sky-800" },
  earnings_logged: { label: "Earnings logged", color: "bg-violet-100 text-violet-800" },
};

export const STATUS_ORDER: CardStatus[] = [
  "scraped",
  "researched_pending",
  "research_approved",
  "scripted_pending",
  "script_approved",
  "filming",
  "ready_to_post",
  "posted",
  "earnings_logged",
];