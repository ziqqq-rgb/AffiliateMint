import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard, ResearchDossier, ScrapedProduct, ScriptVariation, ThreadsPost } from "../types";
import { Spinner } from "./Spinner";
import { ProductSummary } from "./ProductSummary";
import { PipelinePanel } from "./PipelinePanel";
import { ScriptPanel } from "./ScriptPanel";
import { ThreadsPanel } from "./ThreadsPanel";
import { TeleprompterView } from "./TeleprompterView";

interface Props {
  cardId: number;
  onBack: () => void;

  refreshSignal?: number;
}

export function CardDetailView({ cardId, onBack, refreshSignal }: Props) {
  const [card, setCard] = useState<ContentCard | null>(null);
  const [product, setProduct] = useState<ScrapedProduct | null>(null);
  const [dossiers, setDossiers] = useState<ResearchDossier[]>([]);
  const [scripts, setScripts] = useState<ScriptVariation[]>([]);
  const [threadsPosts, setThreadsPosts] = useState<ThreadsPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [teleprompterScript, setTeleprompterScript] = useState<ScriptVariation | null>(null);

  const load = useCallback(async () => {
    const freshCard = await api.getCard(cardId);
    const freshProduct = await api.getProduct(freshCard.product_id);
    const freshDossiers = await api.listResearchForProduct(freshCard.product_id);

    setCard(freshCard);
    setProduct(freshProduct);
    setDossiers(freshDossiers);

    if (freshProduct.platform === "shopee") {
      setThreadsPosts(await api.listThreadsForProduct(freshCard.product_id));
    } else {
      setScripts(await api.listScriptsForProduct(freshCard.product_id));
    }
    setLoading(false);
  }, [cardId]);

  // Full load (with spinner) whenever we're pointed at a different card.
  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

  // Silent background refresh triggered from outside this view (e.g.
  // cancelling a queued post from the Queue sidebar) - no spinner, so
  // the panel doesn't flicker while it's already on screen.
  useEffect(() => {
    if (refreshSignal === undefined) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshSignal]);

  if (loading || !card || !product) {
    return (
      <div className="p-6">
        <BackButton onBack={onBack} />
        <div className="mt-4">
          <Spinner label="Loading card..." />
        </div>
      </div>
    );
  }

  const latestDossier = dossiers[0] ?? null;
  const isShopee = product.platform === "shopee";
  const hasContent = isShopee ? threadsPosts.length > 0 : scripts.length > 0;

  if (teleprompterScript) {
    return <TeleprompterView script={teleprompterScript} onClose={() => setTeleprompterScript(null)} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <BackButton onBack={onBack} />

      <ProductSummary product={product} />

      <PipelinePanel card={card} dossier={latestDossier} hasScripts={hasContent} onChange={load} />

      {isShopee ? (
        threadsPosts.length > 0 && <ThreadsPanel posts={threadsPosts} onChange={load} />
      ) : (
        scripts.length > 0 && (
          <ScriptPanel scripts={scripts} onChange={load} onOpenTeleprompter={setTeleprompterScript} />
        )
      )}
    </div>
  );
}

function BackButton({ onBack }: { onBack: () => void }) {
  return (
    <button onClick={onBack} className="text-sm font-medium text-gray-500 hover:text-gray-900">
      &larr; Back to board
    </button>
  );
}