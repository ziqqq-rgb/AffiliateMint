export interface Plan {
  id: "starter" | "growth" | "scale";
  name: string;
  priceRM: number;
  tagline: string;
  popular: boolean;
  features: string[];
}

// Static marketing content for the pricing section - edit values here
// directly when pricing changes, no backend call involved.
export const PLANS: Plan[] = [
  {
    id: "starter",
    name: "Starter",
    priceRM: 89,
    tagline: "For testing the waters",
    popular: false,
    features: [
      "TikTok Shop scraping",
      "30 product scrapes / month",
      "AI research dossier + 3 script angles",
      "Manual publishing reminders",
    ],
  },
  {
    id: "growth",
    name: "Growth",
    priceRM: 199,
    tagline: "For your daily grind",
    popular: true,
    features: [
      "Everything in Starter",
      "Shopee scraping + Threads auto-publishing",
      "Unlimited product scrapes",
      "Self-healing scheduling queue",
      "Deep research (ingredient & compound science)",
    ],
  },
  {
    id: "scale",
    name: "Scale",
    priceRM: 399,
    tagline: "For running it like a business",
    popular: false,
    features: [
      "Everything in Growth",
      "Multiple affiliate accounts",
      "Priority queue slots",
      "Priority support",
    ],
  },
];
