import { useEffect, useState } from "react";
import { api } from "../api";
import type { DashboardSummary } from "../types";
import { Spinner } from "./Spinner";
import { STATUS_META, STATUS_ORDER } from "../lib/statusMeta";
import { formatRM } from "../lib/format";

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardSummary().then((data) => {
      setSummary(data);
      setLoading(false);
    });
  }, []);

  if (loading || !summary) {
    return (
      <div className="p-6">
        <Spinner label="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total cards" value={summary.total_cards.toString()} />
        <StatCard label="Total commission" value={formatRM(summary.total_commission_rm)} highlight />
        <StatCard label="Total views" value={summary.total_views.toLocaleString()} />
        <StatCard label="Units sold" value={summary.total_units_sold.toLocaleString()} />
      </div>

      {summary.cards_missing_earnings > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {summary.cards_missing_earnings} posted card{summary.cards_missing_earnings === 1 ? "" : "s"} still
          waiting on an earnings entry.
        </div>
      )}

      <section className="rounded-xl border border-gray-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-900">Cards by stage</h2>
        <div className="space-y-2">
          {STATUS_ORDER.map((status) => {
            const count = summary.cards_by_status[status] ?? 0;
            const pct = summary.total_cards === 0 ? 0 : Math.round((count / summary.total_cards) * 100);
            return (
              <div key={status} className="flex items-center gap-3">
                <span className="w-40 shrink-0 text-xs text-gray-600">{STATUS_META[status].label}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-100">
                  <div className="h-full rounded-full bg-gray-900" style={{ width: `${pct}%` }} />
                </div>
                <span className="w-8 shrink-0 text-right text-xs text-gray-500">{count}</span>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${highlight ? "text-emerald-700" : "text-gray-900"}`}>{value}</p>
    </div>
  );
}