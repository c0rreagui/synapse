import React from 'react';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    subtitle?: string;
    action?: React.ReactNode;
    glow?: 'magenta' | 'violet' | 'teal' | 'mint';
}

const glowColors = {
    magenta: 'from-aurora-magenta/20 to-aurora-pink/10',
    violet: 'from-aurora-violet/20 to-aurora-magenta/10',
    teal: 'from-aurora-teal/20 to-aurora-violet/10',
    mint: 'from-aurora-mint/20 to-aurora-teal/10',
};

export default function GlassCard({
    children,
    className = "",
    title,
    subtitle,
    action,
    glow = 'violet'
}: GlassCardProps) {
    return (
        <div className={`aurora-card group ${className}`}>
            {/* Inner Glow Effect */}
            <div className={`absolute inset-0 bg-gradient-to-br ${glowColors[glow]} opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none rounded-3xl`} />

            {(title || action) && (
                <div className="relative z-10 px-6 py-5 border-b border-white/5 flex justify-between items-start">
                    <div>
                        {title && (
                            <h3 className="text-lg font-semibold text-white/90 tracking-tight">{title}</h3>
                        )}
                        {subtitle && (
                            <p className="text-xs text-white/40 mt-1 font-mono uppercase tracking-widest">{subtitle}</p>
                        )}
                    </div>
                    {action && <div className="shrink-0">{action}</div>}
                </div>
            )}
            <div className="relative z-10 p-6">
                {children}
            </div>
        </div>
    );
}
