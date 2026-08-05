import { LandingNavbar } from "../components/landing/LandingNavbar";
import { Hero } from "../components/landing/Hero";
import { FeatureGrid } from "../components/landing/FeatureGrid";
import { PricingSection } from "../components/landing/PricingSection";
import { FAQSection } from "../components/landing/FAQSection";
import { CTASection } from "../components/landing/CTASection";
import { LandingFooter } from "../components/landing/LandingFooter";

interface Props {
  /** Called by every "Start free trial" / "Choose plan" button. For now
   * this just enters the app - there's no signup/auth flow yet. */
  onGetStarted: () => void;
}

export function LandingPage({ onGetStarted }: Props) {
  return (
    // Self-contained bg/text colors so this looks right regardless of
    // whatever background the parent (App.tsx) happens to use.
    <div className="bg-paper text-ink">
      <LandingNavbar onGetStarted={onGetStarted} />
      <main>
        <Hero onGetStarted={onGetStarted} />
        <FeatureGrid />
        <PricingSection onGetStarted={onGetStarted} />
        <FAQSection />
        <CTASection onGetStarted={onGetStarted} />
      </main>
      <LandingFooter />
    </div>
  );
}
