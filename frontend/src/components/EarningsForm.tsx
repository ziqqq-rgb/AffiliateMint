/** FR-4.4: manual earnings entry per posted card. */
import { useState } from "react";
import { api } from "../api";

export function EarningsForm({ cardId }: { cardId: number }) {
  const [views, setViews] = useState(0);
  const [unitsSold, setUnitsSold] = useState(0);
  const [commission, setCommission] = useState(0);
  const [saved, setSaved] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await api.logEarnings(cardId, {
      views,
      units_sold: unitsSold,
      commission_earned_rm: commission,
    });
    setSaved(true);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 p-4">
      <label className="block text-sm">
        Views
        <input
          type="number"
          value={views}
          onChange={(e) => setViews(Number(e.target.value))}
          className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
        />
      </label>
      <label className="block text-sm">
        Units sold
        <input
          type="number"
          value={unitsSold}
          onChange={(e) => setUnitsSold(Number(e.target.value))}
          className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
        />
      </label>
      <label className="block text-sm">
        Commission earned (RM)
        <input
          type="number"
          value={commission}
          onChange={(e) => setCommission(Number(e.target.value))}
          className="mt-1 w-full rounded border border-gray-300 px-2 py-1"
        />
      </label>
      <button type="submit" className="rounded bg-black px-4 py-2 text-sm text-white">
        Save
      </button>
      {saved && <p className="text-sm text-green-600">Saved.</p>}
    </form>
  );
}
