import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f8f9fa",
        surface: "#f8f9fa",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f3f4f5",
        "surface-container": "#edeeef",
        "surface-container-high": "#e7e8e9",
        "surface-container-highest": "#e1e3e4",
        "surface-variant": "#e1e3e4",
        "on-background": "#191c1d",
        "on-surface": "#191c1d",
        "on-surface-variant": "#45464d",
        primary: "#0f172a",
        "on-primary": "#ffffff",
        "primary-container": "#131b2e",
        "on-primary-container": "#aeb6cf",
        secondary: "#64748b",
        "secondary-container": "#d0e1fb",
        "on-secondary-container": "#54647a",
        "tertiary-fixed": "#89f5e7",
        "on-tertiary-container": "#0c9488",
        outline: "#76777d",
        "outline-variant": "#c6c6cd",
        error: "#ba1a1a",
      },
      borderRadius: {
        DEFAULT: "1rem",
        lg: "2rem",
        xl: "3rem",
      },
      spacing: {
        "container-max": "1280px",
        "margin-desktop": "64px",
        "margin-mobile": "20px",
        gutter: "24px",
        "stack-sm": "8px",
        "stack-md": "16px",
        "stack-lg": "32px",
        "section-gap": "80px",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        fintech: "0 4px 6px -1px rgba(15, 23, 42, 0.05)",
        "fintech-lg": "0 10px 15px -3px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
