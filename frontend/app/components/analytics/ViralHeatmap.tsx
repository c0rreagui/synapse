"use client";

import React from "react";

interface HeatmapData {
    day: string;
    day_index: number;
    hour: number;
    value: number;
    count: number;
}

interface ViralHeatmapProps {
    data: HeatmapData[];
}

export default function ViralHeatmap({ data }: ViralHeatmapProps) {
    if (!data || data.length === 0) {
        return <div className="h-full w-full flex items-center justify-center text-white/20">Sem dados de mapa de calor</div>;
    }

    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const hours = Array.from({ length: 24 }, (_, i) => i);

    // Normalize values for opacity (0 to 1)
    const maxVal = Math.max(...data.map(d => d.value), 1);

    const getCellData = (dayIdx: number, hour: number) => {
        // Adjust for Python 0=Sunday, Frontend 0=Monday if we want Monday start? 
        // Python aggregator: 0=Sunday.
        // Let's align with JS getDay(): 0=Sun. 
        // Frontend array above starts Mon? Typically analytics show Mon-Sun.
        // Let's stick to Aggregator output "day_index" which follows Python %w (0=Sun, 6=Sat).
        // If frontend row 0 is Monday (index 0 in new array), we need to map Python 1=Mon to Row 0.
        // Map: (python_idx + 6) % 7 -> Mon=0, Sun=6.

        // Let's just lookup by name first to be safe, or stick to raw index if consistent.
        // Aggregator returns day_index 0=Sun, 1=Mon.
        // We want Mon(0) to Sun(6).

        const targetDayIdx = (dayIdx + 1) % 7; // Convert Mon-start index (0-6) back to Python Sun-start (1-0)
        // Wait. Frontend Row 0 = Mon. 
        // Python 1 = Mon.
        // Frontend Row 6 = Sun.
        // Python 0 = Sun.

        // Let's just find by day name to be robust against index confusion.
        const dayName = days[dayIdx]; // "Mon"
        // Find matching data. Note data uses full names "Monday".

        return data.find(d => d.day.startsWith(dayName) && d.hour === hour);
    };

    return (
        <div className="w-full h-full flex flex-col font-mono text-xs">

            {/* Header: Hours */}
            <div className="flex mb-1 pl-10">
                {hours.map(h => (
                    <div key={h} className="flex-1 text-center text-white/30 text-[9px]">
                        {h}
                    </div>
                ))}
            </div>

            {/* Grid */}
            <div className="flex-1 flex flex-col gap-[2px]">
                {days.map((day, dayIdx) => (
                    <div key={day} className="flex flex-1 items-center gap-[2px]">
                        {/* Day Label */}
                        <div className="w-10 text-white/40 text-[10px] pr-2 text-right">
                            {day}
                        </div>

                        {/* Cells */}
                        {hours.map(h => {
                            const params = getCellData(dayIdx, h);
                            const val = params ? params.value : 0;
                            const opacity = Math.max(0.1, val / maxVal); // Min 0.1 for visibility
                            const hasData = val > 0;

                            return (
                                <div
                                    key={h}
                                    className="flex-1 h-full rounded-sm relative group transition-all duration-300 hover:scale-125 hover:z-10 hover:shadow-[0_0_10px_rgba(255,0,255,0.8)]"
                                    style={{
                                        backgroundColor: hasData ? `rgba(255, 0, 255, ${opacity})` : 'rgba(255, 255, 255, 0.03)',
                                        border: hasData ? 'none' : '1px solid rgba(255,255,255,0.02)'
                                    }}
                                >
                                    {hasData && (
                                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-black/90 border border-white/10 rounded text-[10px] whitespace-nowrap hidden group-hover:block z-20 pointer-events-none">
                                            {day} {h}:00 • {val} views
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ))}
            </div>

            <div className="mt-2 flex items-center justify-end gap-2 text-[10px] text-white/30">
                <span>Less</span>
                <div className="w-2 h-2 bg-aurora-magenta/20 rounded-sm"></div>
                <div className="w-2 h-2 bg-aurora-magenta/60 rounded-sm"></div>
                <div className="w-2 h-2 bg-aurora-magenta/100 rounded-sm"></div>
                <span>More</span>
            </div>
        </div>
    );
}
