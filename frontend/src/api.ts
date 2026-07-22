// frontend/src/api.ts
import type { CardStatus, ContentCard, DashboardSummary, EarningsEntry, ResearchDossier, ScrapedProduct, ScriptVariation } from "./types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${options?.method ?? "GET"} ${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  listCards: () => request<ContentCard[]>("/cards/"),
  getCard: (cardId: number) => request<ContentCard>(`/cards/${cardId}`),
  setCardStatus: (cardId: number, status: CardStatus) =>
    request<ContentCard>(`/cards/${cardId}/status?new_status=${status}`, { method: "POST" }),

  listProducts: () => request<ScrapedProduct[]>("/products/"),
  getProduct: (productId: number) => request<ScrapedProduct>(`/products/${productId}`),
  runScraper: (url?: string) =>
    request<ScrapedProduct[]>("/scraper/scrape", { method: "POST", body: JSON.stringify(url ? { url } : {}) }),
  runPipeline: (productId: number) =>
    request<ContentCard>(`/products/${productId}/run-pipeline`, { method: "POST" }),

  listResearchForProduct: (productId: number) => request<ResearchDossier[]>(`/research/product/${productId}`),

  listScriptsForProduct: (productId: number) => request<ScriptVariation[]>(`/scripts/product/${productId}`),
  updateScript: (
    scriptId: number,
    body: Partial<Pick<ScriptVariation, "hook_ms" | "body_ms" | "cta_ms" | "caption_ms" | "visual_notes">>,
  ) => request<ScriptVariation>(`/scripts/${scriptId}`, { method: "PUT", body: JSON.stringify(body) }),
  selectScript: (scriptId: number) => request<ContentCard>(`/scripts/${scriptId}/select`, { method: "POST" }),

  logEarnings: (cardId: number, body: Record<string, unknown>) =>
    request(`/earnings/${cardId}`, { method: "POST", body: JSON.stringify(body) }),
  listEarningsForCard: (cardId: number) => request<EarningsEntry[]>(`/earnings/card/${cardId}`),

  getDashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),
};