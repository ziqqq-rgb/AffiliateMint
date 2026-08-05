interface FaqItem {
  question: string;
  answer: string;
}

const FAQS: FaqItem[] = [
  {
    question: "Which platforms does AffiliateMint support?",
    answer:
      "TikTok Shop Malaysia and Shopee Affiliate Malaysia today, on a single affiliate account per platform on the Starter and Growth plans.",
  },
  {
    question: "Do I need my own affiliate accounts?",
    answer:
      "Yes. AffiliateMint automates your existing TikTok Shop and Shopee affiliate accounts — it doesn't create or approve accounts for you.",
  },
  {
    question: "How does the AI research work?",
    answer:
      "For each product, it builds a short dossier covering what it does, its key benefits and USPs, and a summary of what reviewers like and dislike — used as the basis for your scripts.",
  },
  {
    question: "Can I edit what it generates?",
    answer:
      "Every script and caption is editable inline. Your edits are remembered, so future scripts for similar products lean toward what you've actually kept.",
  },
  {
    question: "Can I cancel anytime?",
    answer: "Yes. Billing is monthly with no lock-in contract — cancel from your account page and you won't be charged again.",
  },
];

export function FAQSection() {
  return (
    <section id="faq" className="mx-auto max-w-3xl px-6 py-20">
      <h2 className="text-center font-display text-3xl font-bold tracking-tight text-ink">
        Questions, answered
      </h2>

      <div className="mt-10 divide-y divide-line rounded-xl border border-line bg-white shadow-card">
        {FAQS.map((faq) => (
          <details key={faq.question} className="group px-6 py-4">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-sm font-semibold text-ink">
              {faq.question}
              <span className="shrink-0 text-ink/40 transition-transform group-open:rotate-45">+</span>
            </summary>
            <p className="mt-3 text-sm leading-relaxed text-ink/60">{faq.answer}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
