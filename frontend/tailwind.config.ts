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
                    bg: "#0d1117",
                    surface: "#161b22",
                    card: "#1c2128",
                    border: "#30363d",
                    text: "#c9d1d9",
                    muted: "#8b949e",
                    accent: "#58a6ff",
                    green: "#3fb950",
                    red: "#f85149",
                    yellow: "#d29922",
                    purple: "#a371f7",
                    cyan: "#39d353",
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
