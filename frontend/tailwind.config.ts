import type { Config } from "tailwindcss";

export default {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                cmd: {
                    bg: "var(--cmd-bg)",
                    surface: "var(--cmd-surface)",
                    card: "var(--cmd-card)",
                    border: "var(--cmd-border)",
                    text: "var(--cmd-text)",
                    muted: "var(--cmd-text-muted)",
                    accent: "var(--cmd-blue)", // Legacy mapping
                    green: "var(--cmd-green)",
                    red: "var(--cmd-red)",
                    yellow: "var(--cmd-yellow)",
                    purple: "var(--cmd-purple)", // New
                    cyan: "var(--cmd-blue)",     // New
                },
                // Stitch Mode Palette
                synapse: {
                    bg: "#05040a",      // Deep Void
                    surface: "#0f0a15", // Neural Layer
                    panel: "rgba(13, 17, 23, 0.7)", // Glass Module
                    primary: {
                        DEFAULT: "#8b5cf6", // Violet Neon
                        dark: "#7c3aed",
                        light: "#a78bfa",
                        glow: "rgba(139, 92, 246, 0.5)"
                    },
                    secondary: "#d946ef", // Magenta/Pink
                    cyan: "#06b6d4",      // Cyber Blue
                    emerald: "#10b981",   // System Online
                    amber: "#f59e0b",     // Warning
                    text: "#e9d5ff",      // Light Violet Text
                    border: "rgba(139, 92, 246, 0.2)",
                }
            },
            animation: {
                'radar-scan': 'radarScan 4s linear infinite',
                'pulse-slow': 'pulse 3s ease-in-out infinite',
                'orbit': 'orbit 20s linear infinite',
            },
            keyframes: {
                radarScan: {
                    '0%': { transform: 'rotate(0deg)' },
                    '100%': { transform: 'rotate(360deg)' },
                },
                orbit: {
                    '0%': { transform: 'rotate(0deg) translateX(120px) rotate(0deg)' },
                    '100%': { transform: 'rotate(360deg) translateX(120px) rotate(-360deg)' },
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'Consolas', 'monospace'],
            },
        },
    },
    plugins: [],
} satisfies Config;
