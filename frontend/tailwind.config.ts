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
                background: "var(--background)",
                foreground: "var(--foreground)",
                synapse: {
                    dark: "#030712", // Rich Black
                    surface: "#0f172a", // Slate 900
                    border: "#1e293b", // Slate 800
                    primary: "#06b6d4", // Cyan 500
                    primaryGlow: "rgba(6, 182, 212, 0.5)",
                    secondary: "#8b5cf6", // Violet 500
                    success: "#10b981", // Emerald 500
                    danger: "#ef4444", // Red 500
                    text: "#f8fafc", // Slate 50
                    muted: "#94a3b8", // Slate 400
                }
            },
            backgroundImage: {
                'grid-pattern': "linear-gradient(to right, #1e293b 1px, transparent 1px), linear-gradient(to bottom, #1e293b 1px, transparent 1px)",
                'radial-glow': "radial-gradient(circle at center, var(--tw-gradient-stops))",
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float': 'float 6s ease-in-out infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                }
            }
        },
    },
    plugins: [],
} satisfies Config;
