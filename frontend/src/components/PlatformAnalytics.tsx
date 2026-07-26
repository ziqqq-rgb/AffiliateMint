import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import type { ContentCard, Platform } from "../types";
import { buildLast7DaysSeries, countPostedDaysAgo, countPostedTotal } from "../lib/postedStats";

interface Props {
  platform: Platform;
  cards: ContentCard[]; 
}

const PLATFORM_THEME: Record<Platform, { accent: string; soft: string; ring: string; name: string }> = {
  tiktok: { accent: "#fe2c55", soft: "bg-rose-50/60", ring: "ring-rose-100", name: "TikTok Shop" },
  shopee: { accent: "#ee4d2d", soft: "bg-orange-50/60", ring: "ring-orange-100", name: "Shopee" },
};

export function PlatformAnalytics({ platform, cards }: Props) {
  const theme = PLATFORM_THEME[platform];
  const series = buildLast7DaysSeries(cards);
  const today = countPostedDaysAgo(cards, 0);
  const yesterday = countPostedDaysAgo(cards, 1);
  const total = countPostedTotal(cards);
  const delta = today - yesterday;

  return (
    <section className={`rounded-2xl border border-gray-100 ${theme.soft} p-6`}>
      <div className="flex flex-col gap-6 sm:flex-row sm:items-stretch">
        <div className="flex shrink-0 flex-col justify-between gap-4 sm:w-48">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
              {theme.name} · Posted today
            </p>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-4xl font-bold tracking-tight text-gray-900">{today}</span>
              <DeltaBadge delta={delta} />
            </div>
          </div>

          <div className={`rounded-xl bg-white/70 px-3 py-2 ring-1 ${theme.ring}`}>
            <p className="text-xs text-gray-500">All-time posted</p>
            <p className="text-lg font-semibold text-gray-900">{total}</p>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">Last 7 days</p>
          <div className="h-32 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={series} barCategoryGap="28%">
                <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#6b7280" }} />
                <Tooltip
                  cursor={{ fill: "rgba(0,0,0,0.04)" }}
                  contentStyle={{ borderRadius: 10, borderColor: "#e5e7eb", fontSize: 12 }}
                  formatter={(value: number) => [`${value} posted`, ""]}
                />
                <Bar dataKey="count" fill={theme.accent} radius={[6, 6, 0, 0]} maxBarSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  );
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) {
    return <span className="text-xs font-medium text-gray-400">flat vs yesterday</span>;
  }
  const positive = delta > 0;
  return (
    <span className={`text-xs font-medium ${positive ? "text-emerald-600" : "text-red-500"}`}>
      {positive ? "▲" : "▼"} {Math.abs(delta)} vs yesterday
    </span>
  );
}