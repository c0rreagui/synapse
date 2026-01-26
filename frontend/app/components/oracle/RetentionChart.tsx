'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { StitchCard } from '../StitchCard';

interface RetentionChartProps {
    data?: {
        second: number;
        retention_rate: number;
    }[];
}

export function RetentionChart({ data }: RetentionChartProps) {
    // Mock data if empty
    const chartData = data && data.length > 0 ? data : Array.from({ length: 60 }, (_, i) => ({
        second: i,
        retention_rate: 100 * Math.exp(-0.05 * i) + (Math.random() * 5)
    }));

    return (
        <StitchCard className="p-4 h-[300px] w-full bg-black/20 border-white/5">
            <h3 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-synapse-purple"></span>
                Curva de Retenção
            </h3>
            <div className="h-[220px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                        <defs>
                            <linearGradient id="colorRetention" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                        <XAxis
                            dataKey="second"
                            stroke="#6b7280"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => `${val}s`}
                        />
                        <YAxis
                            stroke="#6b7280"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => `${val.toFixed(0)}%`}
                            domain={[0, 100]}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#000000cc', borderColor: '#ffffff20', borderRadius: '8px' }}
                            itemStyle={{ color: '#fff', fontSize: '12px' }}
                            labelStyle={{ color: '#9ca3af', marginBottom: '4px' }}
                            formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Retenção']}
                            labelFormatter={(label) => `Segundo ${label}`}
                        />
                        <Area
                            type="monotone"
                            dataKey="retention_rate"
                            stroke="#8b5cf6"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorRetention)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </StitchCard>
    );
}
