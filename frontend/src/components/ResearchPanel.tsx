import { useState } from "react";
import { api } from "../api";
import type { ResearchDossier } from "../types";
import { Spinner } from "./Spinner";

interface Props {
  productId: number;
  dossier: ResearchDossier | null;
  onChange: () => void;
}

export function ResearchPanel({ productId, dossier, onChange }: Props) {
  const [busy, setBusy] = useState(false);
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    try {
      await action();
      onChange();
    } finally {
      setBusy(false);
    }
  }

  // No dossier yet, or the last attempt was rejected - offer to (re)run it.
  if (!dossier || dossier.status === "rejected") {
    return (
      <section className="rounded-xl border border-gray-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-gray-900">Research</h2>
        {dossier?.status === "rejected" && (
          <p className="mt-1 text-xs text-red-600">
            Previous dossier rejected{dossier.rejection_reason ? `: ${dossier.rejection_reason}` : ""}
          </p>
        )}
        <button
          onClick={() => run(() => api.runResearch(productId))}
          disabled={busy}
          className="mt-3 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
        >
          {busy ? <Spinner label="Researching..." /> : dossier ? "Retry research" : "Run research"}
        </button>
      </section>
    );
  }

  const benefits: string[] = JSON.parse(dossier.key_benefits);

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">Research</h2>
        {dossier.status === "approved" && <span className="text-xs font-medium text-emerald-700">Approved</span>}
      </div>

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

      {dossier.status === "pending" && (
        <div className="mt-4 space-y-2">
          <div className="flex gap-2">
            <button
              onClick={() => run(() => api.reviewResearch(dossier.id, true))}
              disabled={busy}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Approve
            </button>
            <button
              onClick={() => setShowRejectInput((v) => !v)}
              disabled={busy}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Reject
            </button>
          </div>
          {showRejectInput && (
            <div className="flex gap-2">
              <input
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Reason (optional)"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
              <button
                onClick={() => run(() => api.reviewResearch(dossier.id, false, rejectReason || undefined))}
                disabled={busy}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                Confirm reject
              </button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}