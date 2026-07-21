import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Paleta Territorial Kwesx AI ─────────────────────────────────────
        // Verde esmeralda colombiano — naturaleza, territorio, confianza
        terra: {
          DEFAULT: "#1A6B42",
          dark:    "#0F4828",
          mid:     "#2D8A57",
          light:   "#3FAD6E",
          pale:    "#E4F5EC",
          faint:   "#F1FAF5",
        },
        // Ámbar cálido — sol colombiano, agricultura, calidez
        amber: {
          DEFAULT: "#F59E0B",
          dark:    "#B45309",
          light:   "#FCD34D",
          pale:    "#FEF9EC",
          faint:   "#FFFBF0",
        },
        // Azul cielo — innovación, datos, tecnología
        sky: {
          DEFAULT: "#0EA5E9",
          dark:    "#0369A1",
          light:   "#38BDF8",
          pale:    "#E0F2FE",
        },
        // Rojo alerta
        danger: {
          DEFAULT: "#EF4444",
          dark:    "#B91C1C",
          pale:    "#FEE2E2",
        },
        // Neutrales con tono cálido
        warm: {
          50:  "#F8FAF9",
          100: "#EFF5F2",
          200: "#D9E8E1",
          300: "#B8CFC5",
          400: "#89AE9E",
          500: "#638E7D",
          600: "#4A7062",
          700: "#345449",
          800: "#223830",
          900: "#111E18",
        },
        // Backwards compat — keep old names working
        navy:        "#1A6B42",
        "teal-dark": "#0F4828",
        teal:        "#2D8A57",
        "teal-mid":  "#3FAD6E",
        green:       "#22C55E",
        "green-light":"#86EFAC",
        sand:        "#F59E0B",
        primary:     "#1A6B42",
        secondary:   "#3FAD6E",
        accent:      "#F59E0B",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
        "4xl": "2rem",
      },
      boxShadow: {
        "card":   "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        "card-md":"0 4px 12px 0 rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
        "card-lg":"0 10px 30px 0 rgb(0 0 0 / 0.10), 0 4px 8px -4px rgb(0 0 0 / 0.06)",
        "glow":   "0 0 24px 0 rgb(26 107 66 / 0.25)",
        "glow-amber":"0 0 24px 0 rgb(245 158 11 / 0.30)",
      },
      animation: {
        "fade-in":    "fadeIn 0.4s ease-out forwards",
        "slide-up":   "slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-in-r": "slideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pop":        "pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) forwards",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
        "bounce-soft":"bounceSoft 1s ease-in-out infinite",
        "shimmer":    "shimmer 1.5s infinite",
        "spin-slow":  "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn:      { from: { opacity: "0" },                          to: { opacity: "1" } },
        slideUp:     { from: { opacity: "0", transform: "translateY(16px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        slideInRight:{ from: { opacity: "0", transform: "translateX(24px)" }, to: { opacity: "1", transform: "translateX(0)" } },
        pop:         { from: { opacity: "0", transform: "scale(0.85)" },to: { opacity: "1", transform: "scale(1)" } },
        pulseSoft:   { "0%,100%": { opacity: "1" },                     "50%": { opacity: "0.6" } },
        bounceSoft:  { "0%,100%": { transform: "translateY(0)" },       "50%": { transform: "translateY(-4px)" } },
        shimmer:     {
          "0%":   { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      transitionTimingFunction: {
        "spring": "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
