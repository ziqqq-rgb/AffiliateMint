import { useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard as ContentCardType, ScrapedProduct, ScrapeFilters } from "../types";
import { EMPTY_FILTERS } from "../types";
import { ContentCard } from "./ContentCard";
import { FilterPanel } from "./FilterPanel";
import { Spinner } from "./Spinner";

interface Props {
  onOpenCard: (cardId: number) => void;
}

const SCRAPE_URL = "https://shop.tiktok.com/my";

export function KanbanBoard({ onOpenCard }: Props) {
  const [cards, setCards] = useState<ContentCardType[]>([]);
  const [products, setProducts] = useState<Record<number, ScrapedProduct>>({});
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [scrapeError, setScrapeError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ScrapeFilters>(EMPTY_FILTERS);
  const [showFilters, setShowFilters] = useState(false);

  async function loadBoard() {
    setLoading(true);
    const [cardList, productList] = await Promise.all([api.listCards(), api.listProducts()]);
    setCards(cardList);
    setProducts(Object.fromEntries(productList.map((p) => [p.id, p])));
    setLoading(false);
  }

  useEffect(() => {
    loadBoard();
  }, []);

  async function handleRunScraper() {
    setScraping(true);
    setScrapeError(null);
    try {
      await api.runScraper(SCRAPE_URL, filters);
      await loadBoard();
    } catch (err) {
      setScrapeError(err instanceof Error ? err.message : "Scrape failed");
    } finally {
      setScraping(false);
    }
  }

  async function handleClearScrape() {
    const confirmed = window.confirm(
      "Clear un-reviewed scraped products? Cards already in research, scripting, or history are kept.",
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

  const activeFilterCount = Object.values(filters).filter((v) => v !== null && v !== false).length;

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-500">{cards.length} products scraped</p>
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
            {scraping ? <Spinner label="Scraping..." /> : "Run scraper"}
          </button>
        </div>
      </div>

      {showFilters && (
        <FilterPanel filters={filters} onChange={setFilters} onClose={() => setShowFilters(false)} />
      )}

      {loading ? (
        <Spinner label="Loading products..." />
      ) : cards.length === 0 ? (
        <p className="text-sm text-gray-500">No products yet - run the scraper to pull some in.</p>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {cards.map((card) => (
            <ContentCard key={card.id} card={card} product={products[card.product_id]} onOpen={onOpenCard} />
          ))}
        </div>
      )}
    </div>
  );
}