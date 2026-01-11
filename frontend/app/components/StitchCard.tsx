import clsx from "clsx";
import { ReactNode } from "react";

interface StitchCardProps {
    children: ReactNode;
    className?: string;
    hoverEffect?: boolean;
}

export const StitchCard = ({ children, className, hoverEffect = true }: StitchCardProps) => {
    return (
        <div
            className={clsx(
                "stitch-card relative overflow-hidden",
                hoverEffect && "hover:border-synapse-primary hover:shadow-[0_0_30px_rgba(139,92,246,0.15)]",
                className
            )}
        >
            {/* Optional: subtle inner glow or noise texture could be added here */}
            <div className="relative z-10">{children}</div>
        </div>
    );
};
