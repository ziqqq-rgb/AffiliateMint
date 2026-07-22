import { useState } from "react";
import { api } from "../api";
import type { CardStatus, ContentCard } from "../types";

const NEXT_STEP: Partial<Record<CardStatus, { next: CardStatus; label: string }>> = {
  script_approved: { next: "filming", label: "Start filming" },
  filming: { next: "ready_to_post", label: "Mark ready to post" },
  ready_to_post: { next: "posted", label: "Mark posted" },
};

interface Props {
  card: ContentCard;
  onChange: () => void;
}

export function WorkflowControls({ card, onChange }: Props) {
  const [busy, setBusy] = useState(false);
  const step = NEXT_STEP[card.status];

  if (!step) return null;

  async function advance(next: CardStatus) {
    setBusy(true);
    try {
      await api.setCardStatus(card.id, next);
      onChange();
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <button
        onClick={() => advance(step.next)}
        disabled={busy}
        className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
      >
        {busy ? "Saving..." : step.label}
      </button>
    </section>
  );
}