import React from 'react';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    icon?: React.ReactNode;
}

export default function GlassCard({ children, className = "", title, icon }: GlassCardProps) {
    return (
        <div className={`glass-panel rounded-xl p-6 transition-all duration-300 group ${className}`}>
            {(title || icon) && (
                <div className="flex items-center gap-3 mb-4 border-b border-white/10 pb-3 group-hover:border-cyan-500/30 transition-colors duration-300">
                    {icon && <span className="text-synapse-primary group-hover:text-cyan-400 transition-colors duration-300 drop-shadow-[0_0_8px_rgba(6,182,212,0.5)]">{icon}</span>}
                    {title && <h3 className="text-lg font-bold text-white tracking-wide">{title}</h3>}
                </div>
            )}
            <div className="text-synapse-muted">
                {children}
            </div>
        </div>
    );
}
