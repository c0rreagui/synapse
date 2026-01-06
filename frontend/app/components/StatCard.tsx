import React from 'react';

interface StatCardProps {
    label: string;
    value: string | number;
    icon: any; // Aceita ícones do Heroicons
    trend?: string;
    color?: 'cyan' | 'purple' | 'emerald' | 'red';
}

export default function StatCard({ label, value, icon: Icon, trend, color = 'cyan' }: StatCardProps) {
    const colors = {
        cyan: 'text-synapse-primary bg-synapse-primary/10 border-synapse-primary/20',
        purple: 'text-synapse-secondary bg-synapse-secondary/10 border-synapse-secondary/20',
        emerald: 'text-synapse-success bg-synapse-success/10 border-synapse-success/20',
        red: 'text-red-500 bg-red-500/10 border-red-500/20',
    };

    return (
        <div className="glass-panel p-5 rounded-xl flex items-center gap-4 relative overflow-hidden group">
            {/* Background Glow */}
            <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl opacity-10 transition-opacity group-hover:opacity-20 ${colors[color].split(' ')[0].replace('text-', 'bg-')}`}></div>

            <div className={`p-3 rounded-lg border ${colors[color]}`}>
                <Icon className="w-6 h-6" />
            </div>
            <div>
                <p className="text-xs text-synapse-muted font-medium uppercase tracking-wide">{label}</p>
                <h4 className="text-2xl font-bold text-white mt-1">{value}</h4>
                {trend && <span className="text-xs text-white/50">{trend}</span>}
            </div>
        </div>
    );
}
