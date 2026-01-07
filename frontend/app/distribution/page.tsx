"use client";

import { motion } from "framer-motion";
import { Sidebar, Header, StatCard } from "../components";
import { CpuChipIcon, BoltIcon, ServerIcon } from "@heroicons/react/24/outline";

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
                return { label: "TRANSMITTING", dotClass: "bg-synapse-success animate-pulse shadow-[0_0_8px_#10b981]", textClass: "text-synapse-success" };
            case "standby":
                return { label: "STANDBY", dotClass: "bg-yellow-500", textClass: "text-yellow-500" };
            default:
                return { label: "OFFLINE", dotClass: "bg-gray-500", textClass: "text-gray-500" };
        }
    };

    return (
        <main className="min-h-screen flex bg-synapse-bg">
            <div className="fixed inset-0 bg-glow-radial pointer-events-none z-0" />
            <div className="fixed inset-0 bg-cyber-grid pointer-events-none opacity-30 z-0" />

            <Sidebar />

            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                <Header title="Distribution Flow" subtitle="RELAY_NETWORK" />

                <div className="flex-1 overflow-y-auto p-8">
                    {/* Stats Row */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
                    >
                        <StatCard
                            label="Neural Integrity"
                            value="99.7%"
                            icon={CpuChipIcon}
                            color="mint"
                            trend="Network stable"
                        />
                        <StatCard
                            label="Synaptic Throughput"
                            value="1.2K req/min"
                            icon={BoltIcon}
                            color="teal"
                            trend="+18% peak"
                        />
                        <StatCard
                            label="Active Nodes"
                            value="2 of 3"
                            icon={ServerIcon}
                            color="violet"
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
                                <div className="p-2 rounded-lg bg-synapse-primary/10 border border-synapse-primary/20">
                                    <span className="material-symbols-outlined text-synapse-primary text-xl">share</span>
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">Active Data Pathways</h3>
                                    <p className="text-xs text-synapse-muted font-mono">Real-time distribution status</p>
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
                                                    <span className="text-synapse-muted">Throughput</span>
                                                    <span className="text-white font-mono">{pathway.throughput}</span>
                                                </div>
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-synapse-muted">Latency</span>
                                                    <span className="text-white font-mono">{pathway.latency}</span>
                                                </div>
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-synapse-muted">Last Post</span>
                                                    <span className="text-white font-mono">{pathway.lastPost}</span>
                                                </div>
                                            </div>

                                            {pathway.status === "active" && <div className="h-1 mt-4 rounded-full bg-synapse-success/30 overflow-hidden"><div className="h-full w-1/2 bg-synapse-success animate-pulse"></div></div>}
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
                                    <div className="p-2 rounded-lg bg-synapse-success/10 border border-synapse-success/20">
                                        <span className="material-symbols-outlined text-synapse-success text-xl">terminal</span>
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-white">Synapse Console</h3>
                                        <p className="text-xs text-synapse-muted font-mono">Live event stream</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    <span className="size-2 rounded-full bg-synapse-success animate-pulse"></span>
                                    <span className="text-[10px] text-synapse-success font-mono">LIVE</span>
                                </div>
                            </div>

                            <div className="flex-1 bg-black/40 rounded-lg border border-white/5 p-4 font-mono text-xs overflow-y-auto max-h-[400px]">
                                {consoleLogs.map((log, index) => (
                                    <div key={index} className="flex gap-3 mb-2 last:mb-0">
                                        <span className="text-synapse-muted">{log.time}</span>
                                        <span
                                            className={
                                                log.type === "success"
                                                    ? "text-synapse-success"
                                                    : log.type === "warning"
                                                        ? "text-yellow-500"
                                                        : "text-synapse-muted"
                                            }
                                        >
                                            {log.message}
                                        </span>
                                    </div>
                                ))}
                                <div className="flex items-center gap-2 mt-4 text-synapse-muted">
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
