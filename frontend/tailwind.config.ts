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
                synapse: {
                    bg: "#02040a",
                    surface: "#0b101b",
                    border: "#1e293b",
                    primary: "#06b6d4",
                    secondary: "#8b5cf6",
                    success: "#10b981",
                    text: "#e2e8f0",
                    muted: "#64748b",
                }
            },
            backgroundImage: {
                'glow-radial': "radial-gradient(circle at center, rgba(6, 182, 212, 0.15) 0%, transparent 70%)",
            },
            animation: {
                'spin-slow': 'spin 8s linear infinite',
                'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
} satisfies Config;
