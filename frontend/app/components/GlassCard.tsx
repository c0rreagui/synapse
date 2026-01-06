import React from 'react';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    action?: React.ReactNode;
}

export default function GlassCard({ children, className = "", title, action }: GlassCardProps) {
    return (
        <div className={`glass-panel rounded-xl overflow-hidden transition-all duration-300 hover:border-white/10 ${className}`}>
            {(title || action) && (
                <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                    {title && <h3 className="text-sm font-semibold text-synapse-text uppercase tracking-wider">{title}</h3>}
                    {action && <div>{action}</div>}
                </div>
            )}
            <div className="p-6">
                {children}
            </div>
        </div>
    );
}
