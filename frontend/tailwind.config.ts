import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        card: "hsl(var(--card))",
        raised: "hsl(var(--raised))",
        border: "hsl(var(--border))",
        foreground: "hsl(var(--foreground))",
        muted: "hsl(var(--muted-foreground))",
        accent: "hsl(var(--accent))",
        cause: { DEFAULT: "var(--cause)", wash: "var(--cause-wash)", ink: "var(--cause-ink)" },
        affected: { DEFAULT: "var(--affected)", wash: "var(--affected-wash)", ink: "var(--affected-ink)" },
        steady: { DEFAULT: "var(--steady)", wash: "var(--steady-wash)" },
        trace: { DEFAULT: "var(--trace)", wash: "var(--trace-wash)" },
        unmapped: "var(--unmapped)",
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)", sm: "calc(var(--radius) - 4px)" },
      fontFamily: { sans: ["var(--font-sans)", "system-ui", "sans-serif"], mono: ["var(--font-mono)", "monospace"] },
    },
  },
  plugins: [],
};
export default config;
