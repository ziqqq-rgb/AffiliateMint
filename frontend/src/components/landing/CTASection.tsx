interface Props {
  onGetStarted: () => void;
}

export function CTASection({ onGetStarted }: Props) {
  return (
    <section className="bg-ink py-16 text-center text-paper">
      <div className="mx-auto max-w-xl px-6">
        <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">
          Your next product post is one scrape away.
        </h2>
        <button
          onClick={onGetStarted}
          className="mt-6 inline-block rounded-lg bg-mint px-6 py-3 text-sm font-semibold text-ink transition hover:brightness-95 active:scale-[0.97]"
        >
          Start your 7-day free trial
        </button>
      </div>
    </section>
  );
}
