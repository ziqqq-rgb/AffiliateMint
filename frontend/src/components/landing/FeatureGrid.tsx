interface Feature {
  title: string;
  description: string;
}

const FEATURES: Feature[] = [
  {
    title: "Dual-platform scraping",
    description: "TikTok Shop and Shopee product boards, filtered by category, rating, and price, in one place.",
  },
  {
    title: "AI research dossiers",
    description: "What it does, key benefits, USPs, and what reviewers actually like and dislike — written for you.",
  },
  {
    title: "Three script angles, every time",
    description: "Hook, body, CTA, caption, and shot notes — pick your favorite and edit inline.",
  },
  {
    title: "Teleprompter mode",
    description: "Film straight off the app with a clean, large-type reading view.",
  },
  {
    title: "Self-healing queue",
    description: "One post per time slot, scheduled ahead — it keeps working even after a restart.",
  },
  {
    title: "Memory that improves",
    description: "Every edit you make is remembered, so future scripts start closer to what you'd actually post.",
  },
];

export function FeatureGrid() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-6 py-20">
      <div className="max-w-xl">
        <h2 className="font-display text-3xl font-bold tracking-tight text-ink">
          Everything between "found a product" and "it's posted"
        </h2>
        <p className="mt-3 text-ink/60">
          Six pieces, built to run as one pipeline instead of six separate tools.
        </p>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className="rounded-xl border border-line bg-white p-6 shadow-card transition hover:-translate-y-0.5"
          >
            <h3 className="font-display text-base font-semibold text-ink">{feature.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink/60">{feature.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
