
import { clsx } from 'clsx';
import { ArrowUp, ArrowDown } from 'lucide-react';

interface StatCardProps {
    label: string;
    value: string | number;
    subValue?: string;
    trend?: 'up' | 'down' | 'neutral';
    trendValue?: string;
    icon?: React.ReactNode;
    color?: 'purple' | 'green' | 'pink' | 'blue';
}

export function StatCard({ label, value, subValue, trend, trendValue, icon, color = 'purple' }: StatCardProps) {
    const colorStyles = {
        purple: 'bg-synapse-purple/10 border-synapse-purple/30 text-synapse-purple',
        green: 'bg-green-500/10 border-green-500/30 text-green-400',
        pink: 'bg-pink-500/10 border-pink-500/30 text-pink-400',
        blue: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
    };

    return (
        <div className="relative p-6 rounded-2xl bg-[#0f0a15] border border-white/5 overflow-hidden group hover:border-white/20 transition-all">
            {/* Ambient Glow */}
            <div className={clsx("absolute -right-6 -top-6 w-24 h-24 rounded-full blur-3xl opacity-20 group-hover:opacity-40 transition-opacity", colorStyles[color].split(' ')[0])} />

            <div className="relative flex justify-between items-start">
                <div>
                    <p className="text-xs font-mono uppercase tracking-wider text-gray-500 mb-1">{label}</p>
                    <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
                    {subValue && <p className="text-xs text-gray-400 mt-1">{subValue}</p>}
                </div>
                {icon && (
                    <div className={clsx("p-2 rounded-lg", colorStyles[color])}>
                        {icon}
                    </div>
                )}
            </div>

            {(trend && trendValue) && (
                <div className="mt-4 flex items-center gap-1 text-xs font-medium">
                    {trend === 'up' ? (
                        <ArrowUp className="w-3 h-3 text-green-400" />
                    ) : (
                        <ArrowDown className="w-3 h-3 text-red-400" />
                    )}
                    <span className={trend === 'up' ? 'text-green-400' : 'text-red-400'}>
                        {trendValue}
                    </span>
                    <span className="text-gray-600 ml-1">vs last month</span>
                </div>
            )}
        </div>
    );
}
