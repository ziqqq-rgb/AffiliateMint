import { TIKTOK_CATEGORIES, RATING_TIERS } from "../lib/categories";
import type { ScrapeFilters } from "../types";
import { EMPTY_FILTERS } from "../types";

interface Props {
  filters: ScrapeFilters;
  onChange: (filters: ScrapeFilters) => void;
  onClose: () => void;
}

/**
 * Inline filter form shown below the board's toolbar. Fully controlled -
 * KanbanBoard owns the ScrapeFilters state, this component only renders
 * inputs and calls onChange. Keeps this file free of any fetch/API logic.
 */
export function FilterPanel({ filters, onChange, onClose }: Props) {
  function set<K extends keyof ScrapeFilters>(key: K, value: ScrapeFilters[K]) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <div className="mb-4 rounded-xl border border-gray-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
        <button onClick={onClose} className="text-xs font-medium text-gray-500 hover:text-gray-900">
          Close
        </button>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Field label="Category">
          <select
            value={filters.category ?? ""}
            onChange={(e) => set("category", e.target.value || null)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
          >
            <option value="">Any category</option>
            {TIKTOK_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Minimum rating">
          <div className="flex gap-1">
            {RATING_TIERS.map((tier) => (
              <button
                key={tier}
                onClick={() => set("min_rating", filters.min_rating === tier ? null : tier)}
                className={`flex-1 rounded-lg border px-2 py-2 text-sm font-medium transition ${
                  filters.min_rating === tier
                    ? "border-gray-900 bg-gray-900 text-white"
                    : "border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                {tier}★+
              </button>
            ))}
          </div>
        </Field>

        <Field label="Price range (RM)">
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={0}
              placeholder="Min"
              value={filters.min_price ?? ""}
              onChange={(e) => set("min_price", e.target.value === "" ? null : Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
            />
            <span className="text-gray-400">–</span>
            <input
              type="number"
              min={0}
              placeholder="Max"
              value={filters.max_price ?? ""}
              onChange={(e) => set("max_price", e.target.value === "" ? null : Number(e.target.value))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
            />
          </div>
        </Field>

        <Field label="Sort">
          <label className="flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={filters.sort_by_sold}
              onChange={(e) => set("sort_by_sold", e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
            Best sellers (sort by units sold)
          </label>
        </Field>
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={() => onChange(EMPTY_FILTERS)}
          className="text-xs font-medium text-gray-500 hover:text-gray-900"
        >
          Reset all
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-xs font-medium text-gray-600">
      {label}
      <div className="mt-1">{children}</div>
    </label>
  );
}