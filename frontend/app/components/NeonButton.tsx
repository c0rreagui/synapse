import clsx from 'clsx';
import { ButtonHTMLAttributes, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

interface NeonButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'ghost' | 'danger';
    isLoading?: boolean;
    glow?: boolean;
}

export const NeonButton = forwardRef<HTMLButtonElement, NeonButtonProps>(
    ({ className, children, variant = 'primary', isLoading, glow = true, ...props }, ref) => {

        const baseStyles = "relative inline-flex items-center justify-center rounded-lg font-bold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed";

        const variants = {
            primary: "bg-gradient-to-r from-synapse-primary to-synapse-secondary text-white border border-transparent hover:brightness-110",
            ghost: "bg-transparent border border-synapse-primary/30 text-synapse-primary hover:border-synapse-primary hover:bg-synapse-primary/10",
            danger: "bg-red-500/10 border border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white"
        };

        const glowStyles = glow ? "hover:shadow-[0_0_20px_rgba(139,92,246,0.4)]" : "";
        const dangerGlow = (glow && variant === 'danger') ? "hover:shadow-[0_0_20px_rgba(239,68,68,0.4)]" : "";

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
                className={clsx(
                    baseStyles,
                    variants[variant],
                    variant !== 'danger' ? glowStyles : dangerGlow,
                    "px-4 py-2 text-sm ripple-container",
                    className
                )}
                disabled={isLoading || props.disabled}
                onClick={(e) => {
                    if (!isLoading && !props.disabled) createRipple(e);
                    props.onClick?.(e);
                }}
                {...props}
            >
                {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                <span className={clsx(glow && variant !== 'primary' && "text-glow")}>
                    {children}
                </span>
            </button>
        );
    }
);

NeonButton.displayName = "NeonButton";
