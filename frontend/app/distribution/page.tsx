"use client";

import { motion } from "framer-motion";
import { Sidebar, Header, StatCard } from "../components";

interface DataPathway {
    id: number;
    name: string;
    icon: string;
    iconColor: string;
    iconBg: string;
    status: "active" | "standby" | "offline";
    throughput: string;
    latency: string;
    lastPost: string;
}

const pathways: DataPathway[] = [
    {
        id: 1,
        name: "YouTube",
        icon: "smart_display",
        iconColor: "text-[#ff0000]",
        iconBg: "bg-[#ff0000]/10",
        status: "active",
        throughput: "24 posts/day",
        latency: "120ms",
        lastPost: "2 min ago",
    },
    {
        id: 2,
        name: "LinkedIn",
        icon: "work",
        iconColor: "text-[#0077b5]",
        iconBg: "bg-[#0077b5]/10",
        status: "standby",
        throughput: "8 posts/day",
        latency: "89ms",
        lastPost: "4 hours ago",
    },
    {
        id: 3,
        name: "TikTok",
        icon: "music_note",
        iconColor: "text-pink-500",
        iconBg: "bg-pink-500/10",
        status: "offline",
        throughput: "0 posts/day",
        latency: "--",
        lastPost: "Never",
    },
];

const consoleLogs = [
    { time: "23:45:12", type: "success", message: "[DEPLOY] clip_viral_001.mp4 → YouTube @channel_alpha" },
    { time: "23:44:58", type: "info", message: "[QUEUE] 3 clips pending distribution" },
    { time: "23:44:32", type: "success", message: "[DEPLOY] interview_cut_02.mp4 → LinkedIn @profile_beta" },
    { time: "23:43:17", type: "warning", message: "[RETRY] TikTok rate limit, backing off 60s" },
    { time: "23:42:45", type: "success", message: "[PROCESS] Transcoding complete: talk_highlights.mp4" },
    { time: "23:41:22", type: "info", message: "[SCAN] New file detected in watch folder" },
];

export default function DistributionPage() {
    const getStatusConfig = (status: string) => {
        switch (status) {
            case "active":
                return { label: "TRANSMITTING", dotClass: "bg-success animate-pulse shadow-[0_0_8px_#10b981]", textClass: "text-success" };
            case "standby":
                return { label: "STANDBY", dotClass: "bg-idle", textClass: "text-idle" };
            default:
                return { label: "OFFLINE", dotClass: "bg-gray-500", textClass: "text-gray-500" };
        }
    };

    return (
        <main className="min-h-screen flex bg-background">
            <div className="fixed inset-0 bg-synapse-gradient pointer-events-none z-0" />
            <div className="fixed inset-0 bg-grid-pattern synapse-grid pointer-events-none opacity-30 animate-grid-move z-0" />

            <Sidebar />

            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                <Header title="Distribution Flow" subtitle="RELAY_NETWORK" />

                <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {/* Stats Row */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
                    >
                        <StatCard
                            label="Neural Integrity"
                            value="99.7%"
                            icon={<span className="material-symbols-outlined">hub</span>}
                            color="success"
                            trend="Network stable"
                        />
                        <StatCard
                            label="Synaptic Throughput"
                            value="1.2K req/min"
                            icon={<span className="material-symbols-outlined">speed</span>}
                            color="primary"
                            trend="+18% peak"
                        />
                        <StatCard
                            label="Active Nodes"
                            value="2 of 3"
                            icon={<span className="material-symbols-outlined">settings_input_component</span>}
                            color="secondary"
                            trend="1 offline"
                        />
                    </motion.div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Data Pathways - 2 columns */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="lg:col-span-2 glass-panel rounded-2xl p-6"
                        >
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                                    <span className="material-symbols-outlined text-primary text-xl">share</span>
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">Active Data Pathways</h3>
                                    <p className="text-xs text-gray-500 font-mono">Real-time distribution status</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {pathways.map((pathway) => {
                                    const statusConfig = getStatusConfig(pathway.status);
                                    return (
                                        <div
                                            key={pathway.id}
                                            className={`glass-panel rounded-xl p-5 relative overflow-hidden group ${pathway.status === "offline" ? "opacity-60" : ""
                                                }`}
                                        >
                                            {/* Glow effect */}
                                            <div className={`absolute top-0 right-0 w-16 h-16 ${pathway.iconBg} blur-[30px] rounded-full -mr-8 -mt-8`}></div>

                                            <div className="flex items-center justify-between mb-4">
                                                <div className={`size-12 rounded-lg ${pathway.iconBg} flex items-center justify-center border border-white/10`}>
                                                    <span className={`material-symbols-outlined ${pathway.iconColor} text-[28px]`}>{pathway.icon}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`size-2 rounded-full ${statusConfig.dotClass}`}></span>
                                                    <span className={`text-[10px] font-mono ${statusConfig.textClass}`}>{statusConfig.label}</span>
                                                </div>
                                            </div>

                                            <h4 className="text-white font-bold mb-3">{pathway.name}</h4>

                                            <div className="space-y-2">
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-gray-500">Throughput</span>
                                                    <span className="text-white font-mono">{pathway.throughput}</span>
                                                </div>
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-gray-500">Latency</span>
                                                    <span className="text-white font-mono">{pathway.latency}</span>
                                                </div>
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-gray-500">Last Post</span>
                                                    <span className="text-white font-mono">{pathway.lastPost}</span>
                                                </div>
                                            </div>

                                            {pathway.status === "active" && <div className="data-flow-line mt-4"></div>}
                                        </div>
                                    );
                                })}
                            </div>
                        </motion.div>

                        {/* Synapse Console - 1 column */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="glass-panel rounded-2xl p-6 flex flex-col"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-success/10 border border-success/20">
                                        <span className="material-symbols-outlined text-success text-xl">terminal</span>
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-white">Synapse Console</h3>
                                        <p className="text-xs text-gray-500 font-mono">Live event stream</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    <span className="size-2 rounded-full bg-success animate-pulse"></span>
                                    <span className="text-[10px] text-success font-mono">LIVE</span>
                                </div>
                            </div>

                            <div className="flex-1 bg-black/40 rounded-lg border border-white/5 p-4 font-mono text-xs overflow-y-auto max-h-[400px] custom-scrollbar">
                                {consoleLogs.map((log, index) => (
                                    <div key={index} className="flex gap-3 mb-2 last:mb-0">
                                        <span className="text-gray-600">{log.time}</span>
                                        <span
                                            className={
                                                log.type === "success"
                                                    ? "text-success"
                                                    : log.type === "warning"
                                                        ? "text-warning"
                                                        : "text-gray-400"
                                            }
                                        >
                                            {log.message}
                                        </span>
                                    </div>
                                ))}
                                <div className="flex items-center gap-2 mt-4 text-gray-500">
                                    <span className="animate-pulse">▊</span>
                                    <span>Awaiting next event...</span>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </div>
        </main>
    );
}
