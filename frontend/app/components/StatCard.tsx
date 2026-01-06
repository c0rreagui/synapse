import React from 'react';
import GlassCard from './GlassCard';

interface StatCardProps {
    label: string;
    value: string | number;
    icon: React.ReactNode;
    trend?: string;
    color?: 'primary' | 'success' | 'danger' | 'secondary';
}

export default function StatCard({ label, value, icon, trend, color = 'primary' }: StatCardProps) {
    const colorMap = {
        primary: 'text-synapse-primary',
        success: 'text-synapse-success',
        danger: 'text-synapse-danger',
        secondary: 'text-synapse-secondary'
    };

    return (
        <GlassCard className="relative overflow-hidden group h-full flex flex-col justify-between">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity transform scale-150">
                {icon}
            </div>
            <div className="relative z-10 flex flex-col h-full justify-between">
                <div>
                    <div className={`p-2 rounded-lg bg-white/5 w-fit mb-3 ${colorMap[color]} ring-1 ring-white/10`}>
                        {icon}
                    </div>
                    <p className="text-sm font-medium text-slate-400 uppercase tracking-widest">{label}</p>
                </div>
                <div>
                    <h4 className="text-4xl font-bold text-white mt-2 tracking-tight drop-shadow-lg">{value}</h4>
                    {trend && (
                        <p className="text-xs mt-2 text-white/60 font-mono">
                            {trend}
                        </p>
                    )}
                </div>
            </div>
        </GlassCard>
    );
}
