import {
  ContentCard,
  EarningsEntry,
  ResearchDossier,
  ScrapedProduct,
  ScrapeFilters,
  ScriptVariation,
  ThreadsPost,
  ShopeeScrapeFilters,
  EMPTY_SHOPEE_FILTERS,
  QueuedPost,
} from "./types";

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
  listCards: (inProgress?: boolean) =>
  request<ContentCard[]>(inProgress === undefined ? "/cards/" : `/cards/?in_progress=${inProgress}`),

  addCardToProgress: (cardId: number) =>
  request<ContentCard>(`/cards/${cardId}/add-to-progress`, { method: "POST" }),
  getCard: (cardId: number) => request<ContentCard>(`/cards/${cardId}`),

  listProducts: () => request<ScrapedProduct[]>("/products/"),
  getProduct: (productId: number) => request<ScrapedProduct>(`/products/${productId}`),
  runScraper: (url: string, filters: ScrapeFilters) =>
    request<ScrapedProduct[]>("/scraper/scrape", {
      method: "POST",
      body: JSON.stringify({ url, ...filters }),
    }),
  runPipeline: (productId: number) =>
    request<ContentCard>(`/products/${productId}/run-pipeline`, { method: "POST" }),

  listResearchForProduct: (productId: number) => request<ResearchDossier[]>(`/research/product/${productId}`),
  clearScrapedProducts: () =>
    request<{ deleted: number }>("/scraper/clear", { method: "DELETE" }),

  listScriptsForProduct: (productId: number) => request<ScriptVariation[]>(`/scripts/product/${productId}`),
  updateScript: (
    scriptId: number,
    body: Partial<Pick<ScriptVariation, "hook_ms" | "body_ms" | "cta_ms" | "caption_ms" | "visual_notes">>,
  ) => request<ScriptVariation>(`/scripts/${scriptId}`, { method: "PUT", body: JSON.stringify(body) }),

  runShopeeScraper: (filters: ShopeeScrapeFilters = EMPTY_SHOPEE_FILTERS) =>
    request<ScrapedProduct[]>("/shopee/scrape", {
      method: "POST",
      body: JSON.stringify(filters),
    }),

  listThreadsForProduct: (productId: number) => request<ThreadsPost[]>(`/threads/product/${productId}`),
  updateThreadsPost: (postId: number, postText: string) =>
  request<ThreadsPost>(`/threads/posts/${postId}`, {
    method: "PUT",
    body: JSON.stringify({ post_text: postText }),
  }),

  postThreadsPostNow: (postId: number) =>
  request<ContentCard>(`/threads/posts/${postId}/post-now`, { method: "POST" }),

  // History tab - was missing, which broke the History page too
  listEarningsForCard: (cardId: number) => request<EarningsEntry[]>(`/earnings/card/${cardId}`),

  scheduleThreadsPost: (postId: number, scheduledFor: string) =>
  request<ContentCard>(`/threads/posts/${postId}/schedule`, {
    method: "POST",
    body: JSON.stringify({ scheduled_for: scheduledFor }),
  }),

  unscheduleThreadsPost: (postId: number) =>
    request<ContentCard>(`/threads/posts/${postId}/unschedule`, { method: "POST" }),

  listQueue: () => request<QueuedPost[]>("/threads/queue"),
};