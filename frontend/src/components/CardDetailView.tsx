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
}

export function CardDetailView({ cardId, onBack }: Props) {
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

  useEffect(() => {
    setLoading(true);
    load();
  }, [load]);

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
        threadsPosts.length > 0 && <ThreadsPanel card={card} posts={threadsPosts} onChange={load} />
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