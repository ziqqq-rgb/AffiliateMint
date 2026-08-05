/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Landing page brand tokens - pulled from the product's own logo
        // (teal + mint). Only used by the landing page components; the
        // rest of the app keeps using plain Tailwind grays.
        ink: "#0E1613",
        paper: "#F7F5EF",
        teal: { DEFAULT: "#038D7D", dark: "#026B5E" },
        mint: { DEFAULT: "#07C260", soft: "#E4F7EC" },
        coral: { DEFAULT: "#FF5B45", soft: "#FFE9E4" },
        line: "#DCD7C9",
      },
      fontFamily: {
        sans: ["Manrope", "system-ui", "sans-serif"],
        serif: ["Newsreader", "Georgia", "serif"],
        display: ["'Space Grotesk'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(14,22,19,0.04), 0 8px 24px rgba(14,22,19,0.06)",
      },
    },
  },
  plugins: [],
};
