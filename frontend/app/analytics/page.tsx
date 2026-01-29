
'use client';

import { useState, useEffect } from 'react';
import { getSavedProfiles, SavedProfile } from '../../services/profileService';
import { StatCard } from '../components/analytics/StatCard';
import Sidebar from '../components/Sidebar';
import { PerformanceChart } from '../components/analytics/PerformanceChart';
import axios from 'axios';
import { Sparkles, BarChart3, Eye, Heart, MessageSquare } from 'lucide-react';

// Define Data Type based on backend response
interface AnalyticsData {
    profile_id: string;
    username: string;
    summary: {
        followers: number;
        total_likes: number;
        total_views: number;
        posts_analyzed: number;
        avg_engagement: number;
    };
    history: {
        date: string;
        views: number;
        likes: number;
        engagement: number;
    }[];
    best_times: any[];
}

export default function AnalyticsPage() {
    const [profiles, setProfiles] = useState<SavedProfile[]>([]);
    const [selectedProfileId, setSelectedProfileId] = useState<string>('');
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(false);

    // Initial Load: Fetch Profiles
    useEffect(() => {
        const loadProfiles = async () => {
            const list = await getSavedProfiles();
            setProfiles(list);
            if (list.length > 0) {
                // Select first by default
                setSelectedProfileId(list[0].id);
            }
        };
        loadProfiles();
    }, []);

    // Fetch Analytics when selection changes
    useEffect(() => {
        if (!selectedProfileId) return;

        const fetchData = async () => {
            setLoading(true);
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const response = await axios.get(`${API_URL}/api/v1/analytics/${selectedProfileId}`);
                setData(response.data);
            } catch (error) {
                console.error("Error loading analytics:", error);
                setData(null);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selectedProfileId]);

    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
    };

    return (
        <div className="flex bg-[#050505] h-screen overflow-hidden font-sans text-gray-100">
            <Sidebar />
            <main className="flex-1 overflow-y-auto relative h-full scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {/* Ambient Background (simplified) */}
                <div className="fixed inset-0 pointer-events-none z-0">
                    <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-synapse-purple/5 blur-[120px] rounded-full" />
                    <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-blue-500/5 blur-[120px] rounded-full" />
                </div>

                <div className="relative z-10 p-8 max-w-7xl mx-auto space-y-8 pb-20">

                    {/* Header & Selector */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                            <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3">
                                <BarChart3 className="w-8 h-8 text-synapse-purple" />
                                <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
                                    Deep Analytics
                                </span>
                            </h1>
                            <p className="text-gray-500 mt-1">Visualize growth, engagement, and viral patterns.</p>
                        </div>

                        <div className="flex items-center gap-3 bg-[#0f0a15] border border-white/10 rounded-full px-4 py-2">
                            <span className="text-sm text-gray-400">Profile:</span>
                            <select
                                value={selectedProfileId}
                                onChange={(e) => setSelectedProfileId(e.target.value)}
                                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
                            >
                                {profiles.length === 0 && <option>No profiles found</option>}
                                {profiles.map(p => (
                                    <option key={p.id} value={p.id} className="bg-[#0f0a15]">
                                        {p.label || p.username || p.id}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {loading ? (
                        <div className="h-96 flex flex-col items-center justify-center text-synapse-purple animate-pulse">
                            <Sparkles className="w-12 h-12 mb-4" />
                            <p>Crunching Data...</p>
                        </div>
                    ) : data ? (
                        <>
                            {/* KPI Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <StatCard
                                    label="Total Views"
                                    value={formatNumber(data.summary.total_views)}
                                    icon={<Eye className="w-6 h-6 text-white" />}
                                    color="purple"
                                    trend="up"
                                    trendValue="12%"
                                />
                                <StatCard
                                    label="Avg Engagement"
                                    value={data.summary.avg_engagement.toFixed(1)}
                                    icon={<Heart className="w-6 h-6 text-white" />}
                                    color="pink"
                                    subValue="Likes + Comments per View"
                                />
                                <StatCard
                                    label="Followers"
                                    value={formatNumber(data.summary.followers)}
                                    icon={<Sparkles className="w-6 h-6 text-white" />}
                                    color="blue"
                                />
                                <StatCard
                                    label="Analyzed Posts"
                                    value={data.summary.posts_analyzed}
                                    icon={<MessageSquare className="w-6 h-6 text-white" />}
                                    color="green"
                                />
                            </div>

                            {/* Charts Area */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                {/* Main Chart */}
                                <div className="lg:col-span-2 bg-[#0f0a15] border border-white/5 rounded-2xl p-6">
                                    <h3 className="text-lg font-bold mb-6 text-gray-200">Views Growth</h3>
                                    <PerformanceChart data={data.history} />
                                </div>

                                {/* Best Times / Insights (Placeholder for now) */}
                                <div className="bg-[#0f0a15] border border-white/5 rounded-2xl p-6">
                                    <h3 className="text-lg font-bold mb-6 text-gray-200">Oracle Insights</h3>
                                    <div className="space-y-4">
                                        <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                            <div className="text-sm text-gray-400 mb-1">Top Performing Day</div>
                                            <div className="text-xl font-bold text-white">Friday</div>
                                        </div>
                                        <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                            <div className="text-sm text-gray-400 mb-1">Viral Potential</div>
                                            <div className="text-xl font-bold text-synapse-purple">High</div>
                                        </div>
                                        <div className="mt-4 p-4 rounded-xl bg-synapse-purple/10 border border-synapse-purple/20">
                                            <p className="text-xs text-synapse-purple leading-relaxed">
                                                💡 <strong>Tip:</strong> Your videos posted on Fridays get 2x more views than other days.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="h-64 flex items-center justify-center text-gray-500">
                            Select a profile to view analytics.
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
