import clsx from "clsx";
import { ReactNode } from "react";
// Integrating with Design System Tokens
// Maintaining the same visual fidelity but using configured tokens

interface StitchCardProps {
    children: ReactNode;
    className?: string;
    hoverEffect?: boolean;
    onClick?: () => void;
    noPadding?: boolean;
}

export const StitchCard = ({ children, className, hoverEffect = true, onClick, noPadding = false }: StitchCardProps) => {
    return (
        <div
            onClick={onClick}
            className={clsx(
                // Base: Deep Dark Glass + Rounded Squircle (Using DS tokens)
                "relative group bg-neo-bg/80 backdrop-blur-2xl rounded-neo border border-white/5 overflow-hidden transition-all duration-500",

                // Hover Effects: Neon Border + Shadow Bloom
                hoverEffect && "hover:border-neo-primary/40 hover:shadow-[0_0_60px_-15px_rgba(139,92,246,0.3)] cr-hover-effect",

                // Padding control
                !noPadding && "p-6",

                className
            )}
        >
            {/* 1. GLOBAL HOLOGRAPHIC GRID (Shared DNA) */}
            {/* Kept inline styles for complex gradient steps not easily tokenized yet, but using colors where possible could be next step */}
            <div className="absolute inset-0 z-0 opacity-[0.15] pointer-events-none mix-blend-color-dodge transition-opacity duration-700 group-hover:opacity-30"
                style={{ backgroundImage: 'linear-gradient(rgba(139, 92, 246, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(139, 92, 246, 0.4) 1px, transparent 1px)', backgroundSize: '32px 32px' }}>
            </div>

            {/* 2. SUBTLE SCANLINES */}
            <div className="absolute inset-0 z-0 opacity-10 pointer-events-none bg-[linear-gradient(rgba(0,0,0,0)_50%,rgba(0,0,0,0.4)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%]"></div>

            {/* 3. AMBIENT BLOOM (Top Right) */}
            <div className="absolute -top-[50%] -right-[50%] w-[100%] h-[100%] rounded-full blur-[100px] opacity-10 transition-all duration-1000 group-hover:opacity-20 bg-[conic-gradient(at_top_right,_var(--tw-gradient-stops))] from-neo-primary/50 via-neo-secondary/30 to-transparent pointer-events-none" />

            {/* Content Content */}
            <div className="relative z-10">{children}</div>
        </div>
    );
};
