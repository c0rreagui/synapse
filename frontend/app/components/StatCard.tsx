import React from 'react';

interface StatCardProps {
    label: string;
    value: string | number;
    icon: React.ElementType;
    trend?: string;
    color?: 'cyan' | 'purple' | 'emerald' | 'amber';
}

export default function StatCard({ label, value, icon: Icon, trend, color = 'cyan' }: StatCardProps) {
    const colors = {
        cyan: 'text-cyan-400',
        purple: 'text-purple-400',
        emerald: 'text-emerald-400',
        amber: 'text-amber-400',
    };

    return (
        <div className="stitch-card p-5 rounded-lg flex items-center justify-between group hover:-translate-y-1 transition-transform">
            <div>
                <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 font-mono">{label}</p>
                <p className="text-3xl font-bold text-white group-hover:text-glow transition-all">{value}</p>
                {trend && <p className="text-xs text-slate-600 mt-1">{trend}</p>}
            </div>
            <div className={`p-3 rounded-full bg-white/5 border border-white/5 group-hover:border-white/20 transition-colors ${colors[color]}`}>
                <Icon className="w-6 h-6 opacity-80" />
            </div>
        </div>
    );
}
