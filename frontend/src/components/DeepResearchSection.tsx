import type { IngredientResearch, ResearchDossier } from "../types";

/** Best-effort hostname for a source link label - falls back to the raw
 * URL if it's malformed rather than crashing the render. */
function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

interface Props {
  dossier: ResearchDossier;
}

/** Renders nothing when the product had no ingredient/compound topics
 * worth researching (backend stores "[]" in that case) - deep research
 * is additive, not every product gets this section. */
export function DeepResearchSection({ dossier }: Props) {
  const topics: IngredientResearch[] = JSON.parse(dossier.ingredients_research || "[]");

  if (topics.length === 0) return null;

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-gray-900">Deep research</h2>
      <p className="mt-1 text-xs text-gray-500">
        Ingredient/compound science pulled from the open web - use for credibility in scripts, not as medical advice.
      </p>

      <div className="mt-4 space-y-4">
        {topics.map((topic) => (
          <TopicCard key={topic.topic} topic={topic} />
        ))}
      </div>
    </section>
  );
}

function TopicCard({ topic }: { topic: IngredientResearch }) {
  const sources = topic.sources.filter(Boolean);

  return (
    <div className="rounded-lg border border-sky-100 bg-sky-50/50 p-4">
      <h3 className="text-sm font-semibold capitalize text-sky-900">{topic.topic}</h3>
      <p className="mt-1 text-sm text-gray-700">{topic.what_it_is}</p>

      <Field label="How it works">{topic.how_it_works}</Field>
      <Field label="Who benefits">{topic.who_benefits}</Field>
      {topic.things_to_know && (
        <Field label="Things to know" labelClassName="text-amber-700" textClassName="text-amber-700">
          {topic.things_to_know}
        </Field>
      )}

      {sources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {sources.map((url) => (
            <a
              key={url}
              href={url}
              target="_blank"
              rel="noreferrer"
              className="max-w-[200px] truncate rounded-md border border-sky-200 bg-white px-2 py-1 text-xs text-sky-700 hover:bg-sky-100"
            >
              {hostnameOf(url)}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  children,
  labelClassName = "text-gray-800",
  textClassName = "text-gray-600",
}: {
  label: string;
  children: string;
  labelClassName?: string;
  textClassName?: string;
}) {
  return (
    <p className="mt-2 text-sm">
      <span className={`font-medium ${labelClassName}`}>{label}:</span>{" "}
      <span className={textClassName}>{children}</span>
    </p>
  );
}