export function LandingFooter() {
  return (
    <footer className="border-t border-line bg-paper">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
          <div>
            <p className="font-display text-base font-bold text-ink">AffiliateMint</p>
            <p className="mt-1 text-sm text-ink/60">
              Built for TikTok Shop Malaysia &amp; Shopee Affiliate Malaysia.
            </p>
          </div>
          <p className="text-xs text-ink/40">
            © {new Date().getFullYear()} AffiliateMint. Not affiliated with TikTok or Shopee.
          </p>
        </div>
      </div>
    </footer>
  );
}
