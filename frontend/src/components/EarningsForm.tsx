import { useState } from "react";
import { api } from "../api";

export function EarningsForm({ cardId }: { cardId: number }) {
  const [views, setViews] = useState(0);
  const [unitsSold, setUnitsSold] = useState(0);
  const [commission, setCommission] = useState(0);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.logEarnings(cardId, {
        views,
        units_sold: unitsSold,
        commission_earned_rm: commission,
      });
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-gray-900">Log earnings</h2>
      <label className="block text-sm">
        Views
        <input
          type="number"
          value={views}
          onChange={(e) => setViews(Number(e.target.value))}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
        />
      </label>
      <label className="block text-sm">
        Units sold
        <input
          type="number"
          value={unitsSold}
          onChange={(e) => setUnitsSold(Number(e.target.value))}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
        />
      </label>
      <label className="block text-sm">
        Commission earned (RM)
        <input
          type="number"
          value={commission}
          onChange={(e) => setCommission(Number(e.target.value))}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2"
        />
      </label>
      <button
        type="submit"
        disabled={saving}
        className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save"}
      </button>
      {saved && <p className="text-sm text-emerald-600">Saved.</p>}
    </form>
  );
}