import type { Config } from "tailwindcss";

const config: Config = {
    darkMode: "class",
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#050507", // The Bible's Background
                primary: "#8b55f7",
                "primary-dark": "#6d42c3",
                secondary: "#3b82f6",
                "background-dark": "#050507",
                "surface-dark": "#0a0a0e",
                "border-dark": "rgba(255, 255, 255, 0.08)",
                success: "#00ff9d",
                warning: "#fa6c38",
                idle: "#fbbf24",
            },
            fontFamily: {
                display: ["Inter", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"],
            },
            backgroundImage: {
                'synapse-gradient': 'radial-gradient(circle at 50% -20%, rgba(139, 85, 247, 0.25), transparent 70%)',
                'grid-pattern': 'linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)',
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'radar-ping': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
                'scan-rotate': 'spin 8s linear infinite',
                'data-flow': 'dataFlow 2s linear infinite',
                'float': 'float 6s ease-in-out infinite',
                'float-delayed': 'float 6s ease-in-out 3s infinite',
                'glow-pulse': 'glowPulse 3s ease-in-out infinite',
                'spin-slow': 'spin 12s linear infinite',
                'reverse-spin': 'spin 15s linear infinite reverse',
            },
            keyframes: {
                dataFlow: {
                    '0%': { transform: 'translateX(-100%)' },
                    '100%': { transform: 'translateX(200%)' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                glowPulse: {
                    '0%, 100%': { boxShadow: '0 0 10px rgba(139, 85, 247, 0.2)' },
                    '50%': { boxShadow: '0 0 25px rgba(139, 85, 247, 0.6)' },
                }
            }
        },
    },
    plugins: [],
};
export default config;
