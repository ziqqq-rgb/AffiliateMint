import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type {
  ContentCard as ContentCardType,
  Platform,
  ScrapedProduct,
  ScrapeFilters,
  ShopeeScrapeFilters,
} from "../types";
import { EMPTY_FILTERS, EMPTY_SHOPEE_FILTERS } from "../types";
import { BoardProductCard } from "./BoardProductCard";
import { FilterPanel } from "./FilterPanel";
import { ShopeeFilterPanel } from "./ShopeeFilterPanel";
import { PlatformTabs } from "./PlatformTabs";
import { Spinner } from "./Spinner";

const SCRAPE_URL = "https://shop.tiktok.com/my";

export function KanbanBoard() {
  const [platform, setPlatform] = useState<Platform>("tiktok");
  const [cards, setCards] = useState<ContentCardType[]>([]);
  const [products, setProducts] = useState<Record<number, ScrapedProduct>>({});
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [addingId, setAddingId] = useState<number | null>(null);
  const [scrapeError, setScrapeError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ScrapeFilters>(EMPTY_FILTERS);
  const [shopeeFilters, setShopeeFilters] = useState<ShopeeScrapeFilters>(EMPTY_SHOPEE_FILTERS);
  const [showFilters, setShowFilters] = useState(false);

  async function loadBoard() {
    setLoading(true);
    const [cardList, productList] = await Promise.all([api.listCards(false), api.listProducts()]);
    setCards(cardList);
    setProducts(Object.fromEntries(productList.map((p) => [p.id, p])));
    setLoading(false);
  }

  useEffect(() => {
    loadBoard();
  }, []);

  const visibleCards = useMemo(
    () => cards.filter((c) => products[c.product_id]?.platform === platform),
    [cards, products, platform],
  );

  const counts = useMemo(
    () => ({
      tiktok: cards.filter((c) => products[c.product_id]?.platform === "tiktok").length,
      shopee: cards.filter((c) => products[c.product_id]?.platform === "shopee").length,
    }),
    [cards, products],
  );

  async function handleRunScraper() {
    setScraping(true);
    setScrapeError(null);
    try {
      if (platform === "shopee") {
        await api.runShopeeScraper(shopeeFilters);
      } else {
        await api.runScraper(SCRAPE_URL, filters);
      }
      await loadBoard();
    } catch (err) {
      setScrapeError(err instanceof Error ? err.message : "Scrape failed");
    } finally {
      setScraping(false);
    }
  }

  async function handleClearScrape() {
    const confirmed = window.confirm(
      "Clear un-reviewed scraped products? Anything already added to Progress is kept.",
    );
    if (!confirmed) return;
    setClearing(true);
    setScrapeError(null);
    try {
      await api.clearScrapedProducts();
      await loadBoard();
    } catch (err) {
      setScrapeError(err instanceof Error ? err.message : "Clear failed");
    } finally {
      setClearing(false);
    }
  }

  async function handleAddToProgress(cardId: number) {
    setAddingId(cardId);
    try {
      await api.addCardToProgress(cardId);
      setCards((prev) => prev.filter((c) => c.id !== cardId));
    } finally {
      setAddingId(null);
    }
  }

  const activeFilterCount =
    platform === "shopee"
      ? Object.values(shopeeFilters).filter((v) => v !== null).length
      : Object.values(filters).filter((v) => v !== null && v !== false).length;

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <PlatformTabs active={platform} onChange={setPlatform} counts={counts} />
        <div className="flex items-center gap-3">
          {scrapeError && <p className="text-xs text-red-600">{scrapeError}</p>}
          <button
            onClick={() => setShowFilters((v) => !v)}
            className={`rounded-lg border px-4 py-2 text-sm font-medium transition ${
              showFilters ? "border-gray-900 text-gray-900" : "border-gray-300 text-gray-700 hover:bg-gray-50"
            }`}
          >
            Filter{activeFilterCount > 0 ? ` (${activeFilterCount})` : ""}
          </button>
          <button
            onClick={handleClearScrape}
            disabled={clearing}
            className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50 disabled:opacity-50"
          >
            {clearing ? <Spinner label="Clearing..." /> : "Clear scrape"}
          </button>
          <button
            onClick={handleRunScraper}
            disabled={scraping}
            className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
          >
            {scraping ? <Spinner label="Scraping..." /> : `Run ${platform === "shopee" ? "Shopee" : "TikTok"} scraper`}
          </button>
        </div>
      </div>

      <p className="mb-3 text-sm text-gray-500">
        {visibleCards.length} product{visibleCards.length === 1 ? "" : "s"} awaiting review
      </p>

      {showFilters && platform === "tiktok" && (
        <FilterPanel filters={filters} onChange={setFilters} onClose={() => setShowFilters(false)} />
      )}
      {showFilters && platform === "shopee" && (
        <ShopeeFilterPanel filters={shopeeFilters} onChange={setShopeeFilters} onClose={() => setShowFilters(false)} />
      )}

      {loading ? (
        <Spinner label="Loading products..." />
      ) : visibleCards.length === 0 ? (
        <p className="text-sm text-gray-500">No new products to review - run the scraper to pull some in.</p>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {visibleCards.map((card) => (
            <BoardProductCard
              key={card.id}
              card={card}
              product={products[card.product_id]}
              busy={addingId === card.id}
              onAddToProgress={handleAddToProgress}
            />
          ))}
        </div>
      )}
    </div>
  );
}