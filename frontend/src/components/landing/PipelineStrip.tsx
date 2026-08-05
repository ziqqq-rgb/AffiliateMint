export interface PipelineStage {
  label: string;
  detail: string;
}

export const PIPELINE_STAGES: PipelineStage[] = [
  { label: "Scrape", detail: "Pull winning products from TikTok Shop & Shopee" },
  { label: "Research", detail: "AI dossier: benefits, USPs, reviewer sentiment" },
  { label: "Script", detail: "Three ready-to-film angles, captions included" },
  { label: "Schedule", detail: "Queue it to post at the right slot" },
  { label: "Learn", detail: "Your edits become next time's default" },
];

const NODE_COUNT = PIPELINE_STAGES.length;
const TRACK_WIDTH = 760;
const NODE_Y = 24;

function nodeX(index: number): number {
  const margin = 40;
  const usable = TRACK_WIDTH - margin * 2;
  return margin + (usable / (NODE_COUNT - 1)) * index;
}

/**
 * The one signature element on the page: a literal render of the real
 * product pipeline (scrape -> research -> script -> schedule -> learn),
 * with a single dot traveling the line to suggest "this runs on its own".
 * `dark` controls whether it sits on the ink hero or the paper page body.
 */
export function PipelineStrip({ dark = false, compact = false }: { dark?: boolean; compact?: boolean }) {
  const pathD = `M ${nodeX(0)} ${NODE_Y} L ${nodeX(NODE_COUNT - 1)} ${NODE_Y}`;
  const lineColor = dark ? "rgba(247,245,239,0.18)" : "#DCD7C9";
  const labelColor = dark ? "text-paper" : "text-ink";
  const detailColor = dark ? "text-paper/55" : "text-ink/55";

  return (
    <div className="w-full overflow-x-auto">
      <div className="relative mx-auto" style={{ width: TRACK_WIDTH, minWidth: TRACK_WIDTH }}>
        <svg viewBox={`0 0 ${TRACK_WIDTH} 48`} className="block w-full" aria-hidden="true">
          <path d={pathD} stroke={lineColor} strokeWidth={2} fill="none" />
          {PIPELINE_STAGES.map((_, i) => (
            <circle key={i} cx={nodeX(i)} cy={NODE_Y} r={5} fill={dark ? "#F7F5EF" : "#0E1613"} />
          ))}
        </svg>

        {/* Traveling dot - purely decorative, disabled under reduced-motion (see styles.css) */}
        <div
          className="pipeline-dot pointer-events-none absolute left-0 top-0 h-2.5 w-2.5 rounded-full bg-mint shadow-[0_0_0_4px_rgba(7,194,96,0.25)]"
          style={{ "--pipeline-path": `path("${pathD}")` } as React.CSSProperties}
        />

        {!compact && (
          <div className="mt-3 grid" style={{ gridTemplateColumns: `repeat(${NODE_COUNT}, 1fr)` }}>
            {PIPELINE_STAGES.map((stage) => (
              <div key={stage.label} className="px-2 text-center">
                <p className={`font-display text-sm font-semibold ${labelColor}`}>{stage.label}</p>
                <p className={`mt-1 text-xs leading-snug ${detailColor}`}>{stage.detail}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
