import React from 'react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Loader2 } from 'lucide-react';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface NeoButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg' | 'icon';
    glow?: boolean;
    isLoading?: boolean;
}

export const NeoButton = React.forwardRef<HTMLButtonElement, NeoButtonProps>(
    ({ className, variant = 'primary', size = 'md', glow = true, isLoading = false, children, ...props }, ref) => {

        const variants = {
            primary: "bg-neo-primary text-white hover:bg-neo-primary/90 border-transparent",
            secondary: "bg-neo-surface border-neo-border text-neo-primary hover:border-neo-primary hover:shadow-[0_0_15px_rgba(139,92,246,0.3)]",
            ghost: "bg-transparent hover:bg-white/5 text-gray-300 hover:text-white border-transparent",
            danger: "bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20 hover:border-red-500/50"
        };

        const sizes = {
            sm: "h-8 px-4 text-xs",
            md: "h-10 px-6 text-sm",
            lg: "h-12 px-8 text-base",
            icon: "h-10 w-10 p-2 flex items-center justify-center"
        };

        const baseStyles = "relative inline-flex items-center justify-center rounded-neo font-medium transition-all duration-300 border backdrop-blur-md active:scale-95 disabled:opacity-50 disabled:pointer-events-none overflow-hidden ripple-container";

        const glowEffects = glow && variant === 'primary'
            ? "shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_30px_rgba(139,92,246,0.6)]"
            : "";

        const createRipple = (event: React.MouseEvent<HTMLButtonElement>) => {
            const button = event.currentTarget;
            const circle = document.createElement("span");
            const diameter = Math.max(button.clientWidth, button.clientHeight);
            const radius = diameter / 2;

            circle.style.width = circle.style.height = `${diameter}px`;
            circle.style.left = `${event.clientX - button.getBoundingClientRect().left - radius}px`;
            circle.style.top = `${event.clientY - button.getBoundingClientRect().top - radius}px`;
            circle.classList.add("ripple");

            const existingRipple = button.getElementsByClassName("ripple")[0];
            if (existingRipple) {
                existingRipple.remove();
            }

            button.appendChild(circle);
        };

        return (
            <button
                ref={ref}
                className={cn(baseStyles, variants[variant], sizes[size], glowEffects, className)}
                onClick={(e) => {
                    if (!isLoading && !props.disabled) createRipple(e);
                    props.onClick?.(e);
                }}
                disabled={isLoading || props.disabled}
                {...props}
            >
                {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                {children}
            </button>
        );
    }
);

NeoButton.displayName = "NeoButton";
