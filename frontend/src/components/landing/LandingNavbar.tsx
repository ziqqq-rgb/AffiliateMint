interface Props {
  onGetStarted: () => void;
}

const NAV_LINKS = [
  { href: "#pipeline", label: "How it works" },
  { href: "#features", label: "Features" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export function LandingNavbar({ onGetStarted }: Props) {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <span className="font-display text-lg font-bold tracking-tight text-ink">AffiliateMint</span>

        <nav className="hidden items-center gap-7 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-ink/70 transition-colors hover:text-ink"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <button
          onClick={onGetStarted}
          className="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-dark active:scale-[0.97]"
        >
          Start free trial
        </button>
      </div>
    </header>
  );
}
