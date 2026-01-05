import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: "class",
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        screens: {
            sm: "640px",
            md: "768px",
            lg: "1024px",
            xl: "1280px",
            "2xl": "1536px",
        },
        extend: {
            colors: {
                // Core colors
                background: "#050507",
                foreground: "#ffffff",
                surface: "#0f0f13",
                "surface-dark": "#0a0a0e",

                // Primary palette - CORRECTED TO MATCH STITCH
                primary: "#8b5cf6",
                "primary-dark": "#6d42c3",
                "primary-glow": "#a78bfa",

                // Accent colors
                secondary: "#10b981",
                success: "#00ff9d",
                warning: "#fa6c38",
                idle: "#fbbf24",

                // Neon variants
                "neon-purple": "#8b5cf6",
                "neon-green": "#00ff9d",
                "neon-cyan": "#06b6d4",
                "neon-blue": "#00f0ff",

                // Surface variants
                "deep-space": "#050507",
                "card-surface": "#0e0c15",
                "card-dark": "#0E0C15",
                "card-darker": "#09080F",

                // Border variants
                "border-dark": "rgba(255, 255, 255, 0.08)",
                "border-glow": "#352F4F",
                "glass-border": "rgba(255, 255, 255, 0.08)",
                "glass-bg": "rgba(20, 20, 25, 0.6)",

                // Text
                "text-muted": "#6b7280",
            },
            fontFamily: {
                display: ["Space Grotesk", "sans-serif"],
                body: ["Inter", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
                heading: ["Space Grotesk", "sans-serif"],
            },
            animation: {
                "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                "float": "float 6s ease-in-out infinite",
                "float-delayed": "float 6s ease-in-out 3s infinite",
                "stream-down": "stream 2.5s linear infinite",
                "shimmer": "shimmer 2s linear infinite",
                "shimmer-fast": "shimmer 1s linear infinite",
                "spin-slow": "spin 12s linear infinite",
                "reverse-spin": "spin 15s linear infinite reverse",
                "scan-rotate": "spin 8s linear infinite",
                "data-flow": "dataFlow 2s linear infinite",
                "glow-pulse": "glowPulse 3s ease-in-out infinite",
                "flow-h": "flowHorizontal 3s linear infinite",
                "grid-move": "gridMove 20s linear infinite",
                "scan-line": "scanLine 3s ease-in-out infinite",
                "hex-pulse": "hexPulse 4s ease-in-out infinite",
                "radar-ping": "ping 2s cubic-bezier(0, 0, 0.2, 1) infinite",
            },
            keyframes: {
                float: {
                    "0%, 100%": { transform: "translateY(0)" },
                    "50%": { transform: "translateY(-10px)" },
                },
                stream: {
                    "0%": { transform: "translateY(-100%)", opacity: "0" },
                    "50%": { opacity: "1" },
                    "100%": { transform: "translateY(100%)", opacity: "0" },
                },
                dataFlow: {
                    "0%": { transform: "translateX(-100%)" },
                    "100%": { transform: "translateX(200%)" },
                },
                glowPulse: {
                    "0%, 100%": { boxShadow: "0 0 10px rgba(139, 85, 247, 0.2)" },
                    "50%": { boxShadow: "0 0 25px rgba(139, 85, 247, 0.6)" },
                },
                shimmer: {
                    "0%": { backgroundPosition: "-200% 0" },
                    "100%": { backgroundPosition: "200% 0" },
                },
                flowHorizontal: {
                    "0%": { backgroundPosition: "100% 0" },
                    "100%": { backgroundPosition: "-100% 0" },
                },
                gridMove: {
                    "0%": { backgroundPosition: "0 0" },
                    "100%": { backgroundPosition: "40px 40px" },
                },
                scanLine: {
                    "0%": { top: "0%", opacity: "0" },
                    "10%": { opacity: "1" },
                    "90%": { opacity: "1" },
                    "100%": { top: "100%", opacity: "0" },
                },
                hexPulse: {
                    "0%, 100%": { opacity: "0.1" },
                    "50%": { opacity: "0.3" },
                },
            },
            backgroundImage: {
                "neural-gradient": "radial-gradient(circle at center, rgba(139, 85, 247, 0.15) 0%, transparent 70%)",
                "bio-glow": "radial-gradient(ellipse at top, rgba(16, 185, 129, 0.08) 0%, transparent 60%)",
                "data-stream": "linear-gradient(180deg, rgba(139, 85, 247, 0) 0%, rgba(139, 85, 247, 0.4) 50%, rgba(139, 85, 247, 0) 100%)",
                "synapse-gradient": "radial-gradient(circle at 50% -20%, rgba(139, 85, 247, 0.25), transparent 70%)",
                "grid-pattern": "linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)",
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
            },
            boxShadow: {
                glow: "0 0 20px rgba(139, 85, 247, 0.15)",
                "glow-purple": "0 0 20px rgba(168, 85, 247, 0.3)",
                "glow-blue": "0 0 20px rgba(59, 130, 246, 0.3)",
                "glow-success": "0 0 15px rgba(16, 185, 129, 0.2)",
            },
        },
    },
    plugins: [],
};

export default config;
