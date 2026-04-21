import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0B0D10",
        surface: "#14181D",
        raised: "#1B2027",
        subtle: "#222831",
        up: "#2ED3A7",
        down: "#F06868",
        neutral: "#6B7280",
        warn: "#F5B14C",
        brand: "#6D8CFF",
        text_primary: "#E6EAF0",
        text_secondary: "#8A93A0",
        text_muted: "#5A6270",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
