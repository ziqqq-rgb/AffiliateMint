import { useEffect, useRef } from "react";
import { api } from "../api";
import type { ContentCard, ResearchDossier } from "../types";
import { Spinner } from "./Spinner";

interface Props {
  card: ContentCard;
  dossier: ResearchDossier | null;
  hasScripts: boolean;
  onChange: () => void;
}

export function PipelinePanel({ card, dossier, hasScripts, onChange }: Props) {
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (card.is_generating && !pollRef.current) {
      pollRef.current = setInterval(onChange, 2000);
    }
    if (!card.is_generating && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [card.is_generating, onChange]);

  async function handleRun() {
    try {
      await api.runPipeline(card.product_id);
    } catch {
      // Already running (409) - ignore, the poll above will reflect the real state.
    } finally {
      onChange();
    }
  }

  if (card.is_generating) {
    return (
      <section className="rounded-xl border border-gray-200 bg-white p-4">
        <Spinner label="Writing research + scripts... this can take a minute" />
      </section>
    );
  }

  if (!hasScripts) {
    return (
      <section className="rounded-xl border border-gray-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-gray-900">Research & scripts</h2>
        <p className="mt-1 text-sm text-gray-500">
          One click writes the research and 3 script angles back-to-back - no approval step, you just pick your
          favorite script below once it's done.
        </p>
        <button
          onClick={handleRun}
          className="mt-3 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
        >
          Run research + scripts
        </button>
      </section>
    );
  }

  if (!dossier) return null;
  const benefits: string[] = JSON.parse(dossier.key_benefits);

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <h2 className="mb-2 text-sm font-semibold text-gray-900">Research</h2>
      <p className="text-sm text-gray-700">{dossier.what_it_does}</p>
      <ul className="mt-2 list-inside list-disc text-sm text-gray-600">
        {benefits.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <p className="mt-2 text-sm">
        <span className="font-medium">USP:</span> {dossier.usp}
      </p>
      <p className="mt-2 text-sm text-emerald-700">
        <span className="font-medium">Reviewers like:</span> {dossier.review_summary_positive}
      </p>
      <p className="mt-1 text-sm text-red-700">
        <span className="font-medium">Reviewers dislike:</span> {dossier.review_summary_negative}
      </p>
    </section>
  );
}