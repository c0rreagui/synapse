import React from 'react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
    intensity?: 'low' | 'medium' | 'high';
    border?: boolean;
}

export const GlassPanel = React.forwardRef<HTMLDivElement, GlassPanelProps>(
    ({ className, intensity = 'medium', border = true, children, ...props }, ref) => {

        // Intensity controls opacity/blur mix
        const intensities = {
            low: "bg-neo-bg/40 backdrop-blur-md",
            medium: "bg-neo-glass backdrop-blur-xl", // Standard Neo-Glass
            high: "bg-neo-surface/90 backdrop-blur-2xl"
        };

        const baseStyles = "rounded-neo transition-all duration-300";
        const borderStyles = border ? "border border-neo-border shadow-lg shadow-black/20" : "";

        return (
            <div
                ref={ref}
                className={cn(baseStyles, intensities[intensity], borderStyles, className)}
                {...props}
            >
                {children}
            </div>
        );
    }
);

GlassPanel.displayName = "GlassPanel";
