import { PLANS } from "../../lib/plans";
import { ReceiptCard } from "./ReceiptCard";

interface Props {
  onGetStarted: () => void;
}

export function PricingSection({ onGetStarted }: Props) {
  return (
    <section id="pricing" className="bg-mint-soft/40 py-20">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto max-w-xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight text-ink">Simple, monthly pricing</h2>
          <p className="mt-3 text-ink/60">No lock-in contracts. Change or cancel your plan anytime.</p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {PLANS.map((plan) => (
            // No checkout wired up yet - picking any plan just gets
            // them into the app for now, like every other CTA here.
            <ReceiptCard key={plan.id} plan={plan} onSelect={onGetStarted} />
          ))}
        </div>
      </div>
    </section>
  );
}
