import type { Plan } from "../../lib/plans";
import { formatRMWhole } from "../../lib/format";

interface Props {
  plan: Plan;
  onSelect: (planId: Plan["id"]) => void;
}

/**
 * A pricing card styled like a printed receipt - the torn top edge is a
 * repeating triangle gradient colored to match the page background, so
 * it reads as paper torn away rather than a decorative border.
 */
export function ReceiptCard({ plan, onSelect }: Props) {
  return (
    <div
      className={`flex flex-col ${
        plan.popular ? "ring-2 ring-teal" : "ring-1 ring-line"
      } rounded-b-xl bg-white shadow-card`}
    >
      {plan.popular && (
        <p className="rounded-t-xl bg-teal px-4 py-1.5 text-center font-mono text-[11px] font-medium uppercase tracking-wider text-white">
          Most popular
        </p>
      )}

      <div
        aria-hidden="true"
        className="h-2.5 w-full"
        style={{
          backgroundImage:
            "linear-gradient(-45deg, transparent 6px, #F7F5EF 6px), linear-gradient(45deg, transparent 6px, #F7F5EF 6px)",
          backgroundSize: "12px 12px",
          backgroundPosition: "left top",
          backgroundRepeat: "repeat-x",
        }}
      />

      <div className="flex flex-1 flex-col px-7 pb-7 pt-1">
        <h3 className="font-display text-lg font-bold text-ink">{plan.name}</h3>
        <p className="mt-1 text-sm text-ink/55">{plan.tagline}</p>

        <p className="mt-5 font-mono text-3xl font-semibold text-ink">
          {formatRMWhole(plan.priceRM)}
          <span className="text-sm font-normal text-ink/45"> / month</span>
        </p>

        <div className="my-6 border-t border-dashed border-line" />

        <ul className="flex-1 space-y-2.5 font-mono text-sm text-ink/75">
          {plan.features.map((feature) => (
            <li key={feature} className="flex gap-2.5">
              <span className="text-mint">+</span>
              <span>{feature}</span>
            </li>
          ))}
        </ul>

        <button
          onClick={() => onSelect(plan.id)}
          className={`mt-7 rounded-lg px-4 py-2.5 text-sm font-semibold transition active:scale-[0.97] ${
            plan.popular
              ? "bg-teal text-white hover:bg-teal-dark"
              : "border border-ink/15 text-ink hover:bg-ink/[0.03]"
          }`}
        >
          Choose {plan.name}
        </button>
      </div>
    </div>
  );
}
