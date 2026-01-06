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
                    bg: "#030712",       // Preto profundo
                    surface: "#0f172a",  // Azul escuro fosco
                    border: "#1e293b",   // Borda sutil
                    primary: "#06b6d4",  // Cyan (Ação)
                    secondary: "#8b5cf6",// Roxo (IA)
                    success: "#10b981",  // Verde (Status)
                    text: "#f8fafc",     // Branco Gelo
                    muted: "#94a3b8",    // Cinza Texto
                }
            },
            backgroundImage: {
                'cyber-grid': "linear-gradient(to right, #1e293b 1px, transparent 1px), linear-gradient(to bottom, #1e293b 1px, transparent 1px)",
                'glow-radial': "radial-gradient(circle at center, rgba(6, 182, 212, 0.15) 0%, transparent 70%)",
            },
            backdropBlur: {
                'xs': '2px',
            }
        },
    },
    plugins: [],
} satisfies Config;
