import React, { ReactNode } from "react";

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    onClick?: () => void;
}

export default function GlassCard({ children, className = "", onClick }: GlassCardProps) {
    return (
        <div
            className={`glass-panel rounded-2xl ${className}`}
            onClick={onClick}
        >
            {children}
        </div>
    );
}
