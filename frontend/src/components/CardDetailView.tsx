import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { ContentCard, ResearchDossier, ScrapedProduct, ScriptVariation } from "../types";
import { Spinner } from "./Spinner";
import { StatusBadge } from "./StatusBadge";
import { ProductSummary } from "./ProductSummary";
import { PipelinePanel } from "./PipelinePanel";
import { ScriptPanel } from "./ScriptPanel";
import { WorkflowControls } from "./WorkflowControls";
import { TeleprompterView } from "./TeleprompterView";
import { EarningsForm } from "./EarningsForm";

interface Props {
  cardId: number;
  onBack: () => void;
}

export function CardDetailView({ cardId, onBack }: Props) {
  const [card, setCard] = useState<ContentCard | null>(null);
  const [product, setProduct] = useState<ScrapedProduct | null>(null);
  const [dossiers, setDossiers] = useState<ResearchDossier[]>([]);
  const [scripts, setScripts] = useState<ScriptVariation[]>([]);
  const [loading, setLoading] = useState(true);
  const [teleprompterScript, setTeleprompterScript] = useState<ScriptVariation | null>(null);

  const load = useCallback(async () => {
    const freshCard = await api.getCard(cardId);
    setCard(freshCard);

    const [freshProduct, freshDossiers, freshScripts] = await Promise.all([
      api.getProduct(freshCard.product_id),
      api.listResearchForProduct(freshCard.product_id),
      api.listScriptsForProduct(freshCard.product_id),
    ]);
    setProduct(freshProduct);
    setDossiers(freshDossiers);
    setScripts(freshScripts);
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

  if (teleprompterScript) {
    return <TeleprompterView script={teleprompterScript} onClose={() => setTeleprompterScript(null)} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <BackButton onBack={onBack} />
        <StatusBadge status={card.status} />
      </div>

      <ProductSummary product={product} />

      <PipelinePanel card={card} dossier={latestDossier} hasScripts={scripts.length > 0} onChange={load} />

      {scripts.length > 0 && (
        <ScriptPanel scripts={scripts} onChange={load} onOpenTeleprompter={setTeleprompterScript} />
      )}

      {card.selected_script_id && <WorkflowControls card={card} onChange={load} />}

      {card.status === "posted" && <EarningsForm cardId={card.id} />}
      {card.status === "earnings_logged" && (
        <p className="rounded-lg bg-violet-50 p-4 text-sm text-violet-800">
          Earnings logged for this card. Nice work.
        </p>
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