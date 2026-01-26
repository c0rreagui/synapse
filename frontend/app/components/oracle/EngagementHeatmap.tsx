'use client';

import { StitchCard } from '../StitchCard';
import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip, Cell, CartesianGrid } from 'recharts';

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
        return '#4b5563'; // Low = Gray
    };

    return (
        <StitchCard className="p-5 h-[320px] w-full bg-black/20 border-white/5">
            <h3 className="text-sm font-bold text-gray-300 mb-6 uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]"></span>
                Mapa de Calor (24 Horas)
            </h3>
            <div className="h-[240px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={heatData} barGap={2}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                        <XAxis
                            dataKey="hour"
                            stroke="#6b7280"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(val) => `${val}h`}
                        />
                        <Tooltip
                            cursor={{ fill: '#ffffff05', radius: 4 }}
                            content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                    const d = payload[0].payload;
                                    return (
                                        <div className="bg-black/90 backdrop-blur-xl border border-white/10 p-3 rounded-xl shadow-2xl text-xs">
                                            <p className="font-bold text-white mb-1 tracking-wide">{d.hour}:00 - {d.hour}:59</p>
                                            <div className="flex items-center gap-2">
                                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getBarColor(d.intensity) }}></div>
                                                <p className="text-gray-300">Intensidade: <span className="text-white font-mono font-bold">{d.intensity.toFixed(0)}%</span></p>
                                            </div>
                                        </div>
                                    );
                                }
                                return null;
                            }}
                        />
                        <Bar dataKey="intensity" radius={[4, 4, 4, 4]} animationDuration={1000}>
                            {heatData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={getBarColor(entry.intensity)} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </StitchCard>
    );
}
