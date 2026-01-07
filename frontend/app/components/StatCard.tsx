import React from 'react';

interface StatCardProps {
    label: string;
    value: string | number;
    icon: React.ElementType;
    trend?: string;
    color?: 'magenta' | 'violet' | 'teal' | 'mint';
}

const colorConfig = {
    magenta: {
        text: 'text-aurora-magenta',
        glow: 'shadow-aurora-magenta/30',
        bg: 'bg-aurora-magenta/10',
        border: 'border-aurora-magenta/30',
    },
    violet: {
        text: 'text-aurora-violet',
        glow: 'shadow-aurora-violet/30',
        bg: 'bg-aurora-violet/10',
        border: 'border-aurora-violet/30',
    },
    teal: {
        text: 'text-aurora-teal',
        glow: 'shadow-aurora-teal/30',
        bg: 'bg-aurora-teal/10',
        border: 'border-aurora-teal/30',
    },
    mint: {
        text: 'text-aurora-mint',
        glow: 'shadow-aurora-mint/30',
        bg: 'bg-aurora-mint/10',
        border: 'border-aurora-mint/30',
    },
};

export default function StatCard({ label, value, icon: Icon, trend, color = 'violet' }: StatCardProps) {
    const config = colorConfig[color];

    return (
        <div className="aurora-card group p-6 cursor-default">
            {/* Ambient Glow */}
            <div className={`absolute -inset-1 rounded-3xl blur-2xl ${config.bg} opacity-0 group-hover:opacity-60 transition-opacity duration-700`} />

            <div className="relative z-10 flex items-start justify-between">
                <div className="space-y-3">
                    <p className="text-[11px] uppercase tracking-[0.2em] text-white/40 font-mono">
                        {label}
                    </p>
                    <p className={`text-4xl font-bold stat-value ${config.text} transition-all duration-500`}>
                        {value}
                    </p>
                    {trend && (
                        <p className="text-xs text-white/50 flex items-center gap-1.5">
                            <span className="text-aurora-mint">↗</span>
                            <span className="font-mono">{trend}</span>
                        </p>
                    )}
                </div>

                <div className={`p-3 rounded-2xl ${config.bg} border ${config.border} group-hover:scale-110 transition-transform duration-500`}>
                    <Icon className={`w-6 h-6 ${config.text}`} />
                </div>
            </div>
        </div>
    );
}
