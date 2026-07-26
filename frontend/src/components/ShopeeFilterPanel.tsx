import type { ShopeeScrapeFilters } from "../types";
import { EMPTY_SHOPEE_FILTERS } from "../types";

interface Props {
  filters: ShopeeScrapeFilters;
  onChange: (filters: ShopeeScrapeFilters) => void;
  onClose: () => void;
}

const RATING_TIERS = [4.0, 4.5, 4.8] as const;

export function ShopeeFilterPanel({ filters, onChange, onClose }: Props) {
  function set<K extends keyof ShopeeScrapeFilters>(key: K, value: ShopeeScrapeFilters[K]) {
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

      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Min commission %">
          <input
            type="number"
            min={0}
            placeholder="e.g. 10"
            value={filters.min_commission_rate ?? ""}
            onChange={(e) => set("min_commission_rate", e.target.value === "" ? null : Number(e.target.value))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
          />
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
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={() => onChange(EMPTY_SHOPEE_FILTERS)}
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