import { useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard as ContentCardType, ScrapedProduct } from "../types";
import { ContentCard } from "./ContentCard";
import { Spinner } from "./Spinner";
import { STATUS_META, STATUS_ORDER } from "../lib/statusMeta";

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
        <p className="text-sm text-gray-500">{cards.length} cards on the board</p>
        <div className="flex items-center gap-3">
          {scrapeError && <p className="text-xs text-red-600">{scrapeError}</p>}
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
        <Spinner label="Loading board..." />
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STATUS_ORDER.map((status) => (
            <div key={status} className="w-64 shrink-0">
              <h2 className="mb-2 text-sm font-medium text-gray-700">{STATUS_META[status].label}</h2>
              <div className="flex flex-col gap-2">
                {cards
                  .filter((card) => card.status === status)
                  .map((card) => (
                    <ContentCard key={card.id} card={card} product={products[card.product_id]} onOpen={onOpenCard} />
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}