"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import { StitchCard } from "../components/StitchCard";
import StatCard from "../components/StatCard";
import { ChartBarIcon, EyeIcon, HeartIcon, FireIcon } from "@heroicons/react/24/outline";
import { TikTokProfile } from "../types";
import GrowthChart from "../components/analytics/GrowthChart";
import ViralHeatmap from "../components/analytics/ViralHeatmap";

// Mock types for analytics (should match Backend endpoint)
interface AnalyticsData {
    profile_id: string;
    summary: {
        total_views: number;
        avg_views: number;
        avg_likes: number;
        viral_ratio: number;
        engagement_rate: number;
    };
    history: { date: string; views: number; likes: number }[];
    heatmap: { day: string; day_index: number; hour: number; value: number; count: number }[];
    is_simulated?: boolean;
}

export default function AnalyticsPage() {
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
    const [selectedProfile, setSelectedProfile] = useState<string>("");
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(false);

    // Load Profiles
    useEffect(() => {
        fetch('http://localhost:8000/api/v1/profiles')
            .then(res => res.json())
            .then(data => {
                setProfiles(data);
                if (data.length > 0) setSelectedProfile(data[0].id);
            })
            .catch(err => console.error("Error fetching profiles:", err));
    }, []);

    // Load Analytics when profile changes
    useEffect(() => {
        if (!selectedProfile) return;

        setLoading(true);
        fetch(`http://localhost:8000/api/v1/analytics/${selectedProfile}`)
            .then(res => res.json())
            .then(setData)
            .catch(err => console.error("Error fetching analytics:", err))
            .finally(() => setLoading(false));
    }, [selectedProfile]);

    return (
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans selection:bg-synapse-primary selection:text-white">
            <Sidebar />

            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern flex flex-col gap-6">

                {/* Header */}
                <header className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-3 m-0">
                            <ChartBarIcon className="w-8 h-8 text-synapse-purple" />
                            Deep Analytics
                        </h2>
                        <div className="flex items-center gap-2 mt-1">
                            <p className="text-sm text-gray-500 font-mono m-0">// DEEP_DIVE_METRICS</p>
                            {data?.is_simulated && (
                                <span className="px-2 py-0.5 rounded text-[10px] bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 font-mono uppercase">
                                    Simulado
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-4">
                        {/* Profile Selector */}
                        <div className="relative">
                            <select
                                value={selectedProfile}
                                onChange={(e) => setSelectedProfile(e.target.value)}
                                className="appearance-none bg-[#1c2128] border border-white/10 text-white rounded-xl px-4 py-2 pr-10 focus:outline-none focus:border-synapse-purple transition-colors min-w-[200px]"
                            >
                                {profiles.map(p => (
                                    <option key={p.id} value={p.id}>{p.label || p.username || p.id}</option>
                                ))}
                            </select>
                            <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                                ▼
                            </div>
                        </div>
                    </div>
                </header>

                {loading ? (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-synapse-purple"></div>
                    </div>
                ) : data ? (
                    <>
                        {/* Top Row: Key Metrics */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <StatCard
                                label="Total Views"
                                value={data.summary.total_views.toLocaleString()}
                                icon={EyeIcon}
                                color="violet"
                            />
                            <StatCard
                                label="Avg Views"
                                value={data.summary.avg_views.toLocaleString()}
                                icon={ChartBarIcon}
                                color="teal"
                            />
                            <StatCard
                                label="Engagement Rate"
                                value={`${data.summary.engagement_rate}%`}
                                icon={HeartIcon}
                                color="magenta"
                            />
                            <StatCard
                                label="Viral Efficiency"
                                value={`${(data.summary.viral_ratio * 100).toFixed(0)}%`}
                                icon={FireIcon}
                                color="mint"
                                trend="High Potential"
                            />
                        </div>

                        {/* Middle Row: Growth Chart & Heatmap */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
                            {/* Growth Chart (2/3 width) */}
                            <StitchCard className="lg:col-span-2 p-6 flex flex-col">
                                <h3 className="text-sm font-bold text-white/70 mb-6 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-aurora-teal"></span>
                                    GROWTH TRAJECTORY
                                </h3>
                                <div className="flex-1 min-h-[300px]">
                                    <GrowthChart data={data.history} />
                                </div>
                            </StitchCard>

                            {/* Viral Heatmap (1/3 width) */}
                            <StitchCard className="p-6 flex flex-col">
                                <h3 className="text-sm font-bold text-white/70 mb-6 flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-aurora-magenta"></span>
                                    VIRAL HEATMAP
                                </h3>
                                <div className="flex-1 min-h-[300px]">
                                    <ViralHeatmap data={data.heatmap} />
                                </div>
                            </StitchCard>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-white/30 gap-4">
                        <ChartBarIcon className="w-16 h-16 opacity-20" />
                        <p>Selecione um perfil para analisar</p>
                    </div>
                )}
            </main>
        </div>
    );
}
