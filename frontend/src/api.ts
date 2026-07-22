import type { CardStatus, ContentCard, ResearchDossier, ScrapedProduct, ScriptVariation } from "./types";

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
    request<ScrapedProduct[]>("/scraper/scrape", {
      method: "POST",
      body: JSON.stringify(url ? { url } : {}),
    }),

  runResearch: (productId: number) =>
    request<ResearchDossier>(`/research/${productId}/generate`, { method: "POST" }),
  listResearchForProduct: (productId: number) =>
    request<ResearchDossier[]>(`/research/product/${productId}`),
  reviewResearch: (dossierId: number, approved: boolean, rejectionReason?: string) =>
    request<ResearchDossier>(`/research/${dossierId}/review`, {
      method: "POST",
      body: JSON.stringify({ approved, rejection_reason: rejectionReason }),
    }),

  generateScripts: (dossierId: number) =>
    request<ScriptVariation[]>(`/scripts/${dossierId}/generate`, { method: "POST" }),
  listScriptsForProduct: (productId: number) =>
    request<ScriptVariation[]>(`/scripts/product/${productId}`),
  selectScript: (scriptId: number) =>
    request<ContentCard>(`/scripts/${scriptId}/select`, { method: "POST" }),

  logEarnings: (cardId: number, body: Record<string, unknown>) =>
    request(`/earnings/${cardId}`, { method: "POST", body: JSON.stringify(body) }),
};