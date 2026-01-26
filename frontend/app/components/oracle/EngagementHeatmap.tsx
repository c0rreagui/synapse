'use client';

import { StitchCard } from '../StitchCard';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

interface HeatmapProps {
    data?: {
        hour: number;
        intensity: number; // 0-100
    }[];
}

export function EngagementHeatmap({ data }: HeatmapProps) {
    // Generate mock 24h data if missing
    const heatData = data || Array.from({ length: 24 }, (_, i) => ({
        hour: i,
        intensity: Math.random() * 100
    }));

    const getBarColor = (intensity: number) => {
        if (intensity > 80) return '#10b981'; // High = Emerald
        if (intensity > 50) return '#3b82f6'; // Med = Blue
        return '#6b7280'; // Low = Gray
    };

    return (
        <StitchCard className="p-4 h-[300px] w-full bg-black/20 border-white/5">
            <h3 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                Heatmap de Engajamento (24h)
            </h3>
            <div className="h-[220px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={heatData}>
                        <XAxis
                            dataKey="hour"
                            stroke="#6b7280"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => `${val}h`}
                        />
                        <Tooltip
                            cursor={{ fill: 'transparent' }}
                            content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                    const d = payload[0].payload;
                                    return (
                                        <div className="bg-black/90 border border-white/10 p-2 rounded shadow-xl text-xs">
                                            <p className="font-bold text-white mb-1">{d.hour}:00 - {d.hour}:59</p>
                                            <p className="text-gray-400">Intensidade: <span className="text-white font-mono">{d.intensity.toFixed(0)}/100</span></p>
                                        </div>
                                    );
                                }
                                return null;
                            }}
                        />
                        <Bar dataKey="intensity" radius={[4, 4, 0, 0]}>
                            {heatData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={getBarColor(entry.intensity)} fillOpacity={0.8} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </StitchCard>
    );
}
