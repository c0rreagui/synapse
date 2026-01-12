"use client";

import React, { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

interface GrowthChartProps {
    data: any[];
}

export default function GrowthChart({ data }: GrowthChartProps) {
    if (!data || data.length === 0) {
        return <div className="h-full w-full flex items-center justify-center text-white/20">Sem dados de histórico</div>;
    }

    // Format data for chart
    const chartData = data.map(item => ({
        date: item.date,
        views: item.views,
        likes: item.likes
    }));

    return (
        <div className="w-full h-[300px] font-mono">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#00F0FF" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#00F0FF" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ffffff10" />
                    <XAxis
                        dataKey="date"
                        stroke="#ffffff40"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        minTickGap={30}
                    />
                    <YAxis
                        stroke="#ffffff40"
                        fontSize={10}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #333', borderRadius: '8px' }}
                        itemStyle={{ color: '#00F0FF' }}
                        labelStyle={{ color: '#888' }}
                    />
                    <Area
                        type="monotone"
                        dataKey="views"
                        stroke="#00F0FF"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorViews)"
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
