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
        <StitchCard className="p-5 h-[320px] w-full bg-black/20 border-white/5">
            <h3 className="text-sm font-bold text-gray-300 mb-6 uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-synapse-purple shadow-[0_0_8px_#8b5cf6]"></span>
                Curva de Retenção (Segundos)
            </h3>
            <div className="h-[240px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                        <defs>
                            <linearGradient id="colorRetention" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.6} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                        <XAxis
                            dataKey="second"
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => `${val}s`}
                        />
                        <YAxis
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => `${val.toFixed(0)}%`}
                            domain={[0, 100]}
                        />
                        <Tooltip
                            cursor={{ stroke: '#8b5cf6', strokeWidth: 1, strokeDasharray: '4 4' }}
                            contentStyle={{
                                backgroundColor: 'rgba(10,10,10, 0.8)',
                                borderColor: 'rgba(139, 92, 246, 0.2)',
                                backdropFilter: 'blur(12px)',
                                borderRadius: '12px',
                                boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                            }}
                            itemStyle={{ color: '#e9d5ff', fontSize: '12px', fontWeight: 'bold' }}
                            labelStyle={{ color: '#9ca3af', marginBottom: '4px', fontSize: '11px' }}
                            formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Retenção']}
                            labelFormatter={(label) => `Tempo: ${label}s`}
                        />
                        <Area
                            type="monotone"
                            dataKey="retention_rate"
                            stroke="#8b5cf6"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorRetention)"
                            activeDot={{ r: 6, strokeWidth: 0, fill: '#fff', stroke: '#8b5cf6' }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </StitchCard>
    );
}
