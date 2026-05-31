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
        gold: {
          DEFAULT: "#D4AF37",
          bright: "#FFD700",
          dim: "#A08C28",
          glow: "rgba(212,175,55,0.15)",
        },
        cyan: {
          oms: "#00E5FF",
          dim: "#0099AA",
        },
        green: {
          oms: "#00FFA3",
          dim: "#00AA6E",
        },
        red: {
          oms: "#FF5A5A",
          dim: "#AA3333",
        },
        orange: {
          oms: "#FF8C00",
        },
        surface: {
          DEFAULT: "rgba(18,18,18,0.65)",
          dark: "rgba(10,10,10,0.80)",
          light: "rgba(30,30,30,0.50)",
        },
        border: {
          oms: "rgba(255,255,255,0.06)",
          gold: "rgba(212,175,55,0.20)",
        },
      },
      fontFamily: {
        orbitron: ["Orbitron", "sans-serif"],
        inter: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      backgroundImage: {
        "gold-gradient": "linear-gradient(135deg, #D4AF37 0%, #A08C28 100%)",
        "surface-gradient": "linear-gradient(135deg, rgba(30,25,15,0.8) 0%, rgba(12,12,12,0.9) 100%)",
      },
      backdropBlur: {
        "4xl": "40px",
      },
      boxShadow: {
        "gold-glow": "0 0 20px rgba(212,175,55,0.25), 0 0 40px rgba(212,175,55,0.08)",
        "cyan-glow": "0 0 20px rgba(0,229,255,0.20), 0 0 40px rgba(0,229,255,0.06)",
        "green-glow": "0 0 20px rgba(0,255,163,0.25), 0 0 40px rgba(0,255,163,0.08)",
        "red-glow": "0 0 20px rgba(255,90,90,0.30), 0 0 40px rgba(255,90,90,0.10)",
        "glass": "0 8px 32px rgba(0,0,0,0.40), 0 0 0 1px rgba(255,255,255,0.06), inset 0 1px 0 rgba(255,255,255,0.08)",
        "glass-gold": "0 8px 32px rgba(0,0,0,0.50), 0 0 0 1px rgba(212,175,55,0.15), inset 0 1px 0 rgba(212,175,55,0.08)",
        "depth": "0 24px 64px rgba(0,0,0,0.60), 0 8px 24px rgba(0,0,0,0.40)",
      },
      animation: {
        "pulse-gold": "pulseGold 2s ease-in-out infinite",
        "scan": "scan 3s linear infinite",
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "glow-pulse": "glowPulse 3s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
      },
      keyframes: {
        pulseGold: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 15px rgba(212,175,55,0.15)" },
          "50%": { boxShadow: "0 0 30px rgba(212,175,55,0.35), 0 0 60px rgba(212,175,55,0.10)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
