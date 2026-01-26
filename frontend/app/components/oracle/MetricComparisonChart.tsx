'use client';

import { StitchCard } from '../StitchCard';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from 'recharts';

interface ComparisonProps {
    data?: {
        period: string; // e.g. "7d", "30d"
        current: number;
        previous: number;
    }[];
}

export function MetricComparisonChart({ data }: ComparisonProps) {
    const chartData = data || [
        { period: '7 Dias', current: 15400, previous: 12000 },
        { period: '30 Dias', current: 85000, previous: 92000 },
        { period: '90 Dias', current: 240000, previous: 180000 },
    ];

    return (
        <StitchCard className="p-5 h-[320px] w-full bg-black/20 border-white/5">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-synapse-cyan shadow-[0_0_8px_#06b6d4]"></span>
                    Performance Comparada
                </h3>
            </div>

            <div className="h-[240px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} barSize={32}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                        <XAxis
                            dataKey="period"
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val}
                        />
                        <Tooltip
                            cursor={{ fill: '#ffffff05' }}
                            contentStyle={{
                                backgroundColor: 'rgba(10,10,10, 0.9)',
                                borderColor: 'rgba(255,255,255,0.1)',
                                backdropFilter: 'blur(12px)',
                                borderRadius: '12px'
                            }}
                            itemStyle={{ fontSize: '12px' }}
                            labelStyle={{ color: '#9ca3af', marginBottom: '8px' }}
                        />
                        <Legend iconType="circle" wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                        <Bar name="Período Atual" dataKey="current" fill="url(#gradCurrent)" radius={[6, 6, 0, 0]} />
                        <Bar name="Período Anterior" dataKey="previous" fill="#333" radius={[6, 6, 0, 0]} />
                        <defs>
                            <linearGradient id="gradCurrent" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#06b6d4" stopOpacity={1} />
                                <stop offset="100%" stopColor="#3b82f6" stopOpacity={1} />
                            </linearGradient>
                        </defs>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </StitchCard>
    );
}
