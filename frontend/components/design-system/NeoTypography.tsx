import React from 'react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface NeoTypographyProps extends React.HTMLAttributes<HTMLHeadingElement | HTMLParagraphElement> {
    variant?: 'h1' | 'h2' | 'h3' | 'body' | 'caption';
    glow?: 'none' | 'primary' | 'secondary';
    gradient?: boolean;
}

export const NeoTypography = React.forwardRef<HTMLElement, NeoTypographyProps>(
    ({ className, variant = 'body', glow = 'none', gradient = false, children, ...props }, ref) => {

        // Tag Selection
        const Tag = (variant === 'body' || variant === 'caption') ? 'p' : variant;

        const variants = {
            h1: "text-4xl md:text-5xl font-bold tracking-tight",
            h2: "text-3xl font-semibold tracking-tight",
            h3: "text-xl font-medium",
            body: "text-base text-gray-300 leading-relaxed",
            caption: "text-sm text-gray-500 uppercase tracking-wider"
        };

        const glows = {
            none: "",
            primary: "drop-shadow-[0_0_10px_rgba(139,92,246,0.5)]",
            secondary: "drop-shadow-[0_0_10px_rgba(217,70,239,0.5)]"
        };

        const gradientStyle = gradient ? "bg-clip-text text-transparent bg-gradient-to-r from-neo-primary to-neo-secondary" : "text-white";
        // Body shouldn't default to white if gradient is off, it has its own color in variants. 
        // Fix: Only apply text-white if headings and not gradient?
        // Actually, design system specifies off-white text. "text-white" in gradientStyle overrides "text-gray-300".

        // Improved Logic:
        let colorStyle = "";
        if (gradient) {
            colorStyle = "bg-clip-text text-transparent bg-gradient-to-r from-neo-primary to-neo-secondary";
        } else if (variant.startsWith('h')) {
            colorStyle = "text-white";
        }
        // Body keeps its gray default

        return (
            <Tag
                // @ts-ignore - Dynamic tag ref type issue, safe for this use case
                ref={ref}
                className={cn(variants[variant], glows[glow], colorStyle, className)}
                {...props}
            >
                {children}
            </Tag>
        );
    }
);

NeoTypography.displayName = "NeoTypography";
