import type { Config } from "tailwindcss";

export default {
    content: [
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./stories/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                // Legacy / Command Palette Mapping
                cmd: {
                    bg: "#030305", // OLED Black Base
                    surface: "#08080C", // Deep Space Grey
                    card: "#0C0C14", // Elevated Panel
                    border: "rgba(255, 255, 255, 0.05)", // Starlight Border
                    text: "#f8fafc",
                    muted: "#94a3b8",
                    accent: "#3b82f6",
                    green: "#10b981",
                    red: "#ef4444",
                    yellow: "#f59e0b",
                    purple: "#8b5cf6",
                    cyan: "#06b6d4",
                },
                // Cosmic Industrial Palette (Fase 13 Redesign)
                cosmic: {
                    void: "#030305",     // Deepest Space
                    hull: "#08080C",      // Outer Space Station Hull
                    glass: "rgba(12, 12, 20, 0.6)", // Frosted Viewport
                    border: "rgba(255, 255, 255, 0.06)", // Subtle Grid
                    glowBorder: "rgba(6, 182, 212, 0.3)", // Cyan Highlight
                    primary: "#06b6d4",   // Cyan Neon
                    secondary: "#8b5cf6", // Indigo Deep
                    accent: "#c084fc",    // Radiant Purple
                    stardust: "#f8fafc",  // Bright Text
                    nebula: "#94a3b8",    // Muted Text
                },
                // Stitch Prototype Overrides
                cyan: {
                    400: '#00f0ff',
                    500: '#00d0e0',
                    900: '#003a40',
                },
                indigo: {
                    500: '#6366f1',
                    600: '#4f46e5',
                    900: '#312e81',
                },
                magenta: {
                    500: '#ff0055',
                    600: '#d60046',
                },
                deep: "#010103",
                space: "#050508",
                // Synapse System Modes
                synapse: {
                    bg: "#030305",
                    surface: "#08080C",
                    panel: "rgba(12, 12, 20, 0.7)",
                    primary: {
                        DEFAULT: "#06b6d4",
                        dark: "#0891b2",
                        light: "#67e8f9",
                        glow: "rgba(6, 182, 212, 0.4)"
                    },
                    secondary: "#8b5cf6",
                    cyan: "#06b6d4",
                    emerald: "#10b981",
                    amber: "#f59e0b",
                    text: "#f8fafc",
                    border: "rgba(255, 255, 255, 0.05)",
                }
            },
            backgroundImage: {
                'celestial-gradient': 'radial-gradient(circle at 50% 50%, #0c0e16 0%, #010103 100%)',
                'grid-perspective': "linear-gradient(to bottom, transparent 0%, rgba(0, 240, 255, 0.03) 100%)",
                'scanline': "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))",
            },
            boxShadow: {
                'glow-cyan': '0 0 20px rgba(0, 240, 255, 0.3), 0 0 10px rgba(0, 240, 255, 0.1)',
                'glow-indigo': '0 0 20px rgba(99, 102, 241, 0.4)',
                'glow-magenta': '0 0 20px rgba(255, 0, 85, 0.3)',
                'hologram': 'inset 0 0 30px rgba(0, 240, 255, 0.05)',
                'bloom': '0 0 15px 2px rgba(0, 240, 255, 0.15)',
            },
            borderRadius: {
                neo: "24px", // Sleeker curve
            },
            backdropBlur: {
                '2xl': '40px', // Deep Blur override
            },
            animation: {
                'radar-scan': 'radarScan 4s linear infinite',
                'pulse-slow': 'pulse 3s ease-in-out infinite',
                'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'orbit': 'orbit 20s linear infinite',
                'pulse-transmission': 'pulseTransmission 3s ease-out infinite',
                'data-stream': 'dataStream 2s linear infinite',
                'chromatic-pulse': 'chromaticPulse 4s ease-in-out infinite',
                'spin-slow': 'spin 20s linear infinite',
                'spin-reverse-slow': 'spin 25s linear infinite reverse',
                'float-slow': 'float 6s ease-in-out infinite',
                'shimmer': 'shimmer 2s linear infinite',
                'heartbeat': 'heartbeat 1.5s ease-in-out infinite',
                'laser-flow': 'laserFlow 2s linear infinite',
                'packet-drop': 'packetDrop 4s cubic-bezier(0.4, 0, 1, 1) infinite',
                'radar-sweep': 'radar-spin 4s linear infinite',
                'scan-laser': 'scan-laser 2s linear infinite',
                'glitch-anim': 'glitch 2s infinite',
                'scroll-text': 'scroll-up 20s linear infinite',
                'drift': 'drift 60s linear infinite',
                'shake': 'shake 0.5s cubic-bezier(.36,.07,.19,.97) both',
                'text-scan': 'textScan 3s linear infinite',
                'scan': 'scan 4s linear infinite',
                'scan-fast': 'scan 2s linear infinite',
                'ripple': 'ripple 1.5s linear infinite',
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
                pulseTransmission: {
                    '0%': { opacity: '0', transform: 'translateX(-50%) scaleX(0)' },
                    '50%': { opacity: '1', transform: 'translateX(0) scaleX(1)' },
                    '100%': { opacity: '0', transform: 'translateX(50%) scaleX(0)' },
                },
                dataStream: {
                    '0%': { backgroundPosition: '0% 0%' },
                    '100%': { backgroundPosition: '0% 100%' },
                },
                chromaticPulse: {
                    '0%, 100%': { textShadow: '2px 0 #ff0055, -2px 0 #00f0ff' },
                    '50%': { textShadow: '1px 0 #ff0055, -1px 0 #00f0ff' },
                },
                shimmer: {
                    '0%': { backgroundPosition: '-1000px 0' },
                    '100%': { backgroundPosition: '1000px 0' },
                },
                heartbeat: {
                    '0%, 100%': { transform: 'scale(1)', opacity: '0.5' },
                    '50%': { transform: 'scale(1.1)', opacity: '1' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                laserFlow: {
                    '0%': { backgroundPosition: '0% 0%' },
                    '100%': { backgroundPosition: '0% 200%' },
                },
                packetDrop: {
                    '0%': { top: '0%', opacity: '0' },
                    '10%': { opacity: '1' },
                    '90%': { opacity: '1' },
                    '100%': { top: '100%', opacity: '0' },
                },
                'radar-spin': {
                    '0%': { transform: 'rotate(0deg)' },
                    '100%': { transform: 'rotate(360deg)' },
                },
                'scan-laser': {
                    '0%': { left: '-10%', opacity: '0' },
                    '50%': { opacity: '1' },
                    '100%': { left: '110%', opacity: '0' },
                },
                'glitch': {
                    '0%': { clipPath: 'inset(40% 0 61% 0)' },
                    '20%': { clipPath: 'inset(92% 0 1% 0)' },
                    '40%': { clipPath: 'inset(43% 0 1% 0)' },
                    '60%': { clipPath: 'inset(25% 0 58% 0)' },
                    '80%': { clipPath: 'inset(54% 0 7% 0)' },
                    '100%': { clipPath: 'inset(58% 0 43% 0)' },
                },
                'scroll-up': {
                    '0%': { transform: 'translateY(0)' },
                    '100%': { transform: 'translateY(-50%)' },
                },
                drift: {
                    '0%': { backgroundPosition: '0 0' },
                    '100%': { backgroundPosition: '100% 100%' }
                },
                shake: {
                    '10%, 90%': { transform: 'translate3d(-1px, 0, 0)' },
                    '20%, 80%': { transform: 'translate3d(2px, 0, 0)' },
                    '30%, 50%, 70%': { transform: 'translate3d(-4px, 0, 0)' },
                    '40%, 60%': { transform: 'translate3d(4px, 0, 0)' }
                },
                textScan: {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' }
                },
                scan: {
                    '0%': { backgroundPosition: '0 -100vh' },
                    '100%': { backgroundPosition: '0 100vh' }
                },
                'pulse-connection': {
                    '0%': { opacity: '0', transform: 'scaleX(0)' },
                    '50%': { opacity: '0.6', transform: 'scaleX(1)' },
                    '100%': { opacity: '0', transform: 'translateX(50%) scaleX(0)' }
                },
                'pulse-beam': {
                    '0%, 100%': { opacity: '0.5', height: '180px', boxShadow: '0 0 20px #0bf' },
                    '50%': { opacity: '1', height: '220px', boxShadow: '0 0 60px #0bf, 0 0 100px #0bf' }
                },
                'mech-grab': {
                    '0%, 100%': { transform: 'rotate(0deg)' },
                    '50%': { transform: 'rotate(-15deg)' }
                },
                ripple: {
                    '0%': { boxShadow: '0 0 0 0 rgba(14, 165, 233, 0.4)' },
                    '70%': { boxShadow: '0 0 0 10px rgba(14, 165, 233, 0)' },
                    '100%': { boxShadow: '0 0 0 0 rgba(14, 165, 233, 0)' },
                },
                'rotate-orbit': {
                    '0%': { transform: 'rotateY(0deg) rotateX(20deg)' },
                    '100%': { transform: 'rotateY(360deg) rotateX(20deg)' }
                },
                'counter-rotate': {
                    '0%': { transform: 'rotateX(-20deg) rotateY(360deg)' },
                    '100%': { transform: 'rotateX(-20deg) rotateY(0deg)' }
                },
                rain: {
                    '0%': { backgroundPosition: '0 -150px' },
                    '100%': { backgroundPosition: '0 100%' }
                },
                'energy-pulse': {
                    '0%': { opacity: '0.3', transform: 'scale(0.95)' },
                    '100%': { opacity: '0.6', transform: 'scale(1.05)' }
                },
                'pulse-soft': {
                    '0%, 100%': { opacity: '1' },
                    '50%': { opacity: '0.5' }
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                display: ["Space Grotesk", "sans-serif"],
                mono: ['JetBrains Mono', 'Consolas', 'monospace'],
            },
        },
    },
    plugins: [],
} satisfies Config;
