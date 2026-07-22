import { useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard as ContentCardType, ScrapedProduct } from "../types";
import { ContentCard } from "./ContentCard";
import { Spinner } from "./Spinner";

interface Props {
  onOpenCard: (cardId: number) => void;
}

export function KanbanBoard({ onOpenCard }: Props) {
  const [cards, setCards] = useState<ContentCardType[]>([]);
  const [products, setProducts] = useState<Record<number, ScrapedProduct>>({});
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [scrapeError, setScrapeError] = useState<string | null>(null);

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
      await api.runScraper();
      await loadBoard();
    } catch (err) {
      setScrapeError(err instanceof Error ? err.message : "Scrape failed");
    } finally {
      setScraping(false);
    }
  }

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-gray-500">{cards.length} products scraped</p>
        <div className="flex items-center gap-3">
          {scrapeError && <p className="text-xs text-red-600">{scrapeError}</p>}
          <button
            disabled
            title="Coming soon"
            className="cursor-not-allowed rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-400"
          >
            Filter
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