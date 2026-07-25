import type { Platform } from "../types";

interface Props {
  active: Platform;
  onChange: (platform: Platform) => void;
  counts?: Partial<Record<Platform, number>>;
}

const PLATFORMS: { id: Platform; label: string }[] = [
  { id: "tiktok", label: "TikTok Shop" },
  { id: "shopee", label: "Shopee" },
];

export function PlatformTabs({ active, onChange, counts }: Props) {
  return (
    <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
      {PLATFORMS.map((p) => (
        <button
          key={p.id}
          onClick={() => onChange(p.id)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
            active === p.id ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-900"
          }`}
        >
          {p.label}
          {counts?.[p.id] !== undefined && (
            <span className="ml-1.5 text-xs text-gray-400">{counts[p.id]}</span>
          )}
        </button>
      ))}
    </div>
  );
}