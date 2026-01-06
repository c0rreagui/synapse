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
        <GlassCard className="relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity transform scale-150">
                {icon}
            </div>
            <div className="relative z-10">
                <div className={`p-2 rounded-lg bg-white/5 w-fit mb-3 ${colorMap[color]}`}>
                    {icon}
                </div>
                <p className="text-sm font-medium text-slate-400 uppercase tracking-wider">{label}</p>
                <h4 className="text-3xl font-bold text-white mt-1">{value}</h4>
                {trend && (
                    <p className="text-xs mt-2 text-white/60">
                        {trend}
                    </p>
                )}
            </div>
        </GlassCard>
    );
}
