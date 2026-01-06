import React from 'react';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    icon?: React.ReactNode;
}

export default function GlassCard({ children, className = "", title, icon }: GlassCardProps) {
    return (
        <div className={`glass-panel rounded-xl p-6 transition-all duration-300 ${className}`}>
            {(title || icon) && (
                <div className="flex items-center gap-3 mb-4 border-b border-white/5 pb-3">
                    {icon && <span className="text-synapse-primary">{icon}</span>}
                    {title && <h3 className="text-lg font-semibold text-white tracking-wide">{title}</h3>}
                </div>
            )}
            <div className="text-synapse-muted">
                {children}
            </div>
        </div>
    );
}
