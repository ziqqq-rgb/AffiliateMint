import { PipelineStrip } from "./PipelineStrip";

interface Props {
  onGetStarted: () => void;
}

export function Hero({ onGetStarted }: Props) {
  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-6xl px-6 pb-20 pt-24 text-center">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-mint">
          For TikTok Shop &amp; Shopee affiliates in Malaysia
        </p>

        <h1 className="mx-auto mt-5 max-w-3xl font-display text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl">
          One product in. A scheduled post out.
        </h1>

        <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-paper/70">
          AffiliateMint scrapes the product, writes the research and the scripts, and queues the
          post — so running an affiliate shop stays a one-person job.
        </p>

        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <button
            onClick={onGetStarted}
            className="w-full rounded-lg bg-mint px-6 py-3 text-sm font-semibold text-ink transition hover:brightness-95 active:scale-[0.97] sm:w-auto"
          >
            Start your 7-day free trial
          </button>
          <a
            href="#pricing"
            className="w-full rounded-lg border border-paper/25 px-6 py-3 text-sm font-semibold text-paper transition hover:bg-paper/5 active:scale-[0.97] sm:w-auto"
          >
            See pricing
          </a>
        </div>
        <p className="mt-3 text-xs text-paper/40">No card required. Cancel anytime.</p>

        <div id="pipeline" className="mt-16 rounded-2xl border border-paper/10 bg-white/[0.03] p-8">
          <PipelineStrip dark />
        </div>
      </div>
    </section>
  );
}
