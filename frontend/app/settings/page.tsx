"use client";

import { useState } from "react";
// import { motion } from "framer-motion";
import { Sidebar } from "../components";

interface Integration {
    id: string;
    name: string;
    icon: string;
    iconBg: string;
    iconColor: string;
    connected: boolean;
    status: "connected" | "inactive";
    latency?: string;
    quota?: string;
    lastSync?: string;
}

export default function SettingsPage() {
    const [integrations, setIntegrations] = useState<Integration[]>([
        {
            id: "youtube",
            name: "YouTube Shorts",
            icon: "play_arrow",
            iconBg: "bg-[#282828]",
            iconColor: "text-red-500",
            connected: true,
            status: "connected",
            latency: "24ms",
            quota: "85%",
        },
        {
            id: "linkedin",
            name: "LinkedIn",
            icon: "business_center",
            iconBg: "bg-[#0077b5]/20",
            iconColor: "text-[#0077b5]",
            connected: true,
            status: "connected",
            lastSync: "2 mins ago",
        },
        {
            id: "tiktok",
            name: "TikTok",
            icon: "music_note",
            iconBg: "bg-black",
            iconColor: "text-white",
            connected: false,
            status: "inactive",
        },
    ]);

    const handleToggle = (id: string, checked: boolean) => {
        setIntegrations((prev) =>
            prev.map((integration) =>
                integration.id === id ? { ...integration, connected: checked } : integration
            )
        );
    };

    return (
        <main className="min-h-screen flex bg-background">
            <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-primary/10 via-background to-background pointer-events-none z-0" />

            <Sidebar />

            <div className="flex-1 flex flex-col h-screen overflow-hidden">
                {/* Top Navigation */}
                <header className="h-16 flex items-center justify-between px-6 border-b border-glass-border bg-background/30 backdrop-blur-sm z-40">
                    {/* Breadcrumbs */}
                    <div className="flex items-center text-sm">
                        <span className="text-gray-500">Home</span>
                        <span className="material-symbols-outlined text-[14px] mx-2 text-gray-600">chevron_right</span>
                        <span className="text-gray-500">Settings</span>
                        <span className="material-symbols-outlined text-[14px] mx-2 text-gray-600">chevron_right</span>
                        <span className="text-white font-medium neon-text">Configuration Hub</span>
                    </div>

                    {/* Right Actions */}
                    <div className="flex items-center gap-4">
                        <div className="relative hidden md:block group">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <span className="material-symbols-outlined text-gray-500 group-focus-within:text-primary transition-colors">search</span>
                            </div>
                            <input
                                className="bg-[#1a1a20] border border-glass-border text-sm rounded-full block w-64 pl-10 p-2 text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all font-body"
                                placeholder="Search parameters..."
                                type="text"
                            />
                        </div>
                        <button className="size-9 rounded-full bg-[#1a1a20] border border-glass-border flex items-center justify-center text-gray-400 hover:text-white hover:border-primary/50 transition-all relative">
                            <span className="material-symbols-outlined text-[20px]">notifications</span>
                            <span className="absolute top-2 right-2 size-2 bg-primary rounded-full animate-pulse"></span>
                        </button>
                        <button className="bg-primary hover:bg-primary/80 text-white text-xs font-bold py-2 px-4 rounded-lg shadow-glow transition-all flex items-center gap-2">
                            <span className="material-symbols-outlined text-[16px]">save</span>
                            SAVE CHANGES
                        </button>
                    </div>
                </header>

                {/* Scrollable Page Content */}
                <div className="flex-1 overflow-y-auto p-6 lg:p-10 space-y-8 pb-20">
                    {/* Page Header */}
                    <div className="flex flex-col gap-2">
                        <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight font-display">Configuration Hub</h1>
                        <p className="text-gray-400 max-w-2xl font-body text-sm md:text-base">
                            Manage your neural pathways, dark profiles, and integration logic to orchestrate content distribution at scale.
                        </p>
                    </div>

                    {/* Three Column Dashboard Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* LEFT COLUMN: Platform Integrations (Span 4) */}
                        <div className="lg:col-span-4 space-y-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-bold flex items-center gap-2 font-display">
                                    <span className="material-symbols-outlined text-primary">share</span>
                                    Integrations
                                </h2>
                                <span className="text-xs font-mono text-secondary bg-secondary/10 px-2 py-1 rounded border border-secondary/20">
                                    ALL SYSTEMS OPERATIONAL
                                </span>
                            </div>

                            {/* Integration Cards */}
                            {integrations.map((integration) => {
                                const glowColor = integration.id === "youtube" ? "bg-red-600/10" : integration.id === "linkedin" ? "bg-blue-600/10" : "bg-pink-600/10";

                                return (
                                    <div key={integration.id} className={`glass-card rounded-xl p-5 relative overflow-hidden group ${integration.status === "inactive" ? "border-white/5 opacity-80 hover:opacity-100" : ""}`}>
                                        <div className={`absolute top-0 right-0 w-20 h-20 ${glowColor} blur-[40px] rounded-full -mr-10 -mt-10`}></div>

                                        <div className="flex items-start justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <div className={`size-10 rounded-lg ${integration.iconBg} flex items-center justify-center border border-white/10`}>
                                                    <span className={`material-symbols-outlined ${integration.iconColor} text-[24px]`}>{integration.icon}</span>
                                                </div>
                                                <div>
                                                    <h3 className="font-bold text-white text-base">{integration.name}</h3>
                                                    <div className="flex items-center gap-1.5 mt-0.5">
                                                        <span className={`size-1.5 rounded-full ${integration.status === "connected" ? "bg-secondary shadow-glow-success" : "bg-gray-500"}`}></span>
                                                        <span className={`text-xs ${integration.status === "connected" ? "text-gray-400" : "text-gray-500"}`}>
                                                            {integration.status === "connected" ? "Connected" : "Inactive"}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Toggle */}
                                            <label className="flex items-center cursor-pointer relative" htmlFor={`toggle-${integration.id}`}>
                                                <input
                                                    checked={integration.connected}
                                                    onChange={(e) => handleToggle(integration.id, e.target.checked)}
                                                    className="sr-only toggle-checkbox"
                                                    id={`toggle-${integration.id}`}
                                                    type="checkbox"
                                                    disabled={integration.status === "inactive"}
                                                    aria-label={`Toggle ${integration.name} integration`}
                                                />
                                                <div className={`w-11 h-6 rounded-full border transition-colors duration-300 toggle-label ${integration.connected && integration.status !== "inactive" ? "bg-gray-700 border-gray-600" : "bg-gray-800 border-gray-700"}`}></div>
                                                <div className={`dot absolute left-1 top-1 w-4 h-4 rounded-full transition-transform duration-300 ${integration.connected && integration.status !== "inactive" ? "translate-x-5 bg-white" : "bg-gray-400"}`}></div>
                                            </label>
                                        </div>

                                        {/* Stats */}
                                        {integration.latency && integration.quota && (
                                            <div className="grid grid-cols-2 gap-2 mt-4">
                                                <div className="bg-black/40 rounded p-2 border border-white/5">
                                                    <p className="text-[10px] text-gray-500 font-mono uppercase">API Latency</p>
                                                    <p className="text-sm font-mono text-white">{integration.latency}</p>
                                                </div>
                                                <div className="bg-black/40 rounded p-2 border border-white/5">
                                                    <p className="text-[10px] text-gray-500 font-mono uppercase">Daily Quota</p>
                                                    <p className="text-sm font-mono text-white">{integration.quota}</p>
                                                </div>
                                            </div>
                                        )}

                                        {integration.lastSync && (
                                            <div className="bg-black/40 rounded p-2 border border-white/5 mt-4 flex items-center justify-between">
                                                <span className="text-[10px] text-gray-500 font-mono uppercase">Last Sync</span>
                                                <span className="text-xs font-mono text-gray-300">{integration.lastSync}</span>
                                            </div>
                                        )}

                                        {integration.status === "inactive" && (
                                            <button className="mt-2 w-full py-1.5 rounded border border-dashed border-gray-700 text-xs text-gray-500 hover:text-white hover:border-gray-500 transition-colors">
                                                Configure API Keys
                                            </button>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* MIDDLE COLUMN: Automation Rules (Span 5) */}
                        <div className="lg:col-span-5 space-y-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-bold flex items-center gap-2 font-display">
                                    <span className="material-symbols-outlined text-primary">account_tree</span>
                                    Automation Logic
                                </h2>
                                <button className="text-primary hover:text-white transition-colors text-sm font-bold flex items-center gap-1">
                                    <span className="material-symbols-outlined text-[16px]">add</span>
                                    NEW RULE
                                </button>
                            </div>

                            {/* Logic Builder Canvas */}
                            <div className="glass-panel rounded-xl p-1 min-h-[400px] relative">
                                {/* Background Grid */}
                                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:20px_20px] rounded-xl pointer-events-none"></div>

                                <div className="relative z-10 p-5 space-y-4">
                                    {/* Rule 1 */}
                                    <div className="flex flex-col gap-2">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-mono text-gray-500">RULE_ID_842</span>
                                            <span className="h-px flex-1 bg-white/10"></span>
                                            <div className="flex gap-1">
                                                <button className="text-gray-500 hover:text-white">
                                                    <span className="material-symbols-outlined text-[16px]">edit</span>
                                                </button>
                                                <button className="text-gray-500 hover:text-red-400">
                                                    <span className="material-symbols-outlined text-[16px]">delete</span>
                                                </button>
                                            </div>
                                        </div>

                                        {/* Logic Node Visual */}
                                        <div className="flex flex-col items-center">
                                            {/* Condition Block */}
                                            <div className="w-full bg-[#1e1b24] border border-l-4 border-primary/50 border-white/5 rounded-r-md p-3 shadow-lg relative group hover:border-primary transition-colors">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <span className="material-symbols-outlined text-yellow-500 text-[18px]">bolt</span>
                                                        <span className="text-sm font-mono text-gray-300">
                                                            IF <span className="text-white font-bold">VIRAL_SCORE</span> &gt; 85
                                                        </span>
                                                    </div>
                                                    <span className="size-2 rounded-full bg-secondary shadow-glow-success animate-pulse"></span>
                                                </div>
                                            </div>

                                            {/* Connector */}
                                            <div className="h-6 w-0.5 bg-gradient-to-b from-primary/50 to-primary/20 my-1 relative">
                                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 size-1.5 rounded-full bg-primary shadow-glow"></div>
                                            </div>

                                            {/* Action Block */}
                                            <div className="w-full bg-[#1e1b24] border border-l-4 border-secondary/50 border-white/5 rounded-r-md p-3 shadow-lg hover:border-secondary transition-colors">
                                                <div className="flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-secondary text-[18px]">send</span>
                                                    <span className="text-sm font-mono text-gray-300">
                                                        THEN <span className="text-white font-bold">CROSSPOST</span> -&gt; LINKEDIN
                                                    </span>
                                                </div>
                                                <div className="mt-2 text-xs text-gray-500 font-mono pl-7">
                                                    DELAY: 15min<br />
                                                    TAGS: #Trending #Tech
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Rule 2 (Collapsed) */}
                                    <div className="mt-6 pt-6 border-t border-white/5">
                                        <div className="flex flex-col gap-2 opacity-60 hover:opacity-100 transition-opacity">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs font-mono text-gray-500">RULE_ID_105</span>
                                                <span className="h-px flex-1 bg-white/10"></span>
                                            </div>
                                            <div className="w-full bg-[#1e1b24] border border-white/5 rounded p-3 flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-gray-400 text-[18px]">schedule</span>
                                                    <span className="text-sm font-mono text-gray-400">
                                                        EVERY <span className="text-white">FRIDAY @ 5PM</span> -&gt; ARCHIVE
                                                    </span>
                                                </div>
                                                <div className="px-2 py-0.5 rounded bg-gray-800 text-[10px] text-gray-400 border border-gray-700">PAUSED</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* RIGHT COLUMN: Profile Management (Span 3) */}
                        <div className="lg:col-span-3 space-y-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-bold flex items-center gap-2 font-display">
                                    <span className="material-symbols-outlined text-primary">face</span>
                                    Dark Profiles
                                </h2>
                            </div>

                            <div className="flex flex-col gap-4">
                                {/* Add New Button */}
                                <button className="w-full py-3 rounded-xl border border-dashed border-primary/40 text-primary hover:bg-primary/5 hover:border-primary transition-all flex items-center justify-center gap-2 font-medium text-sm group">
                                    <span className="material-symbols-outlined group-hover:rotate-90 transition-transform">add_circle</span>
                                    Add Neural Profile
                                </button>

                                {/* Profile List */}
                                <div className="space-y-3">
                                    {/* Profile Card 1 */}
                                    <div className="glass-card rounded-lg p-3 flex items-center gap-3">
                                        <div className="relative">
                                            <div
                                                className="size-10 rounded-full bg-cover bg-center border border-white/20 avatar-nexus"
                                            ></div>
                                            <div className="absolute -bottom-0.5 -right-0.5 size-3 bg-secondary rounded-full border-2 border-[#131118]"></div>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-bold text-white truncate">Nexus_Alpha</h4>
                                            <p className="text-xs text-gray-500 truncate">Tech Influencer (Lvl 5)</p>
                                        </div>
                                        <button className="text-gray-500 hover:text-white">
                                            <span className="material-symbols-outlined text-[18px]">more_vert</span>
                                        </button>
                                    </div>

                                    {/* Profile Card 2 */}
                                    <div className="glass-card rounded-lg p-3 flex items-center gap-3">
                                        <div className="relative">
                                            <div
                                                className="size-10 rounded-full bg-cover bg-center border border-white/20 avatar-crypto"
                                            ></div>
                                            <div className="absolute -bottom-0.5 -right-0.5 size-3 bg-secondary rounded-full border-2 border-[#131118]"></div>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-bold text-white truncate">Crypto_Ghost</h4>
                                            <p className="text-xs text-gray-500 truncate">Finance (Lvl 3)</p>
                                        </div>
                                        <button className="text-gray-500 hover:text-white">
                                            <span className="material-symbols-outlined text-[18px]">more_vert</span>
                                        </button>
                                    </div>

                                    {/* Profile Card 3 */}
                                    <div className="glass-card rounded-lg p-3 flex items-center gap-3 opacity-75">
                                        <div className="relative">
                                            <div
                                                className="size-10 rounded-full bg-cover bg-center border border-white/20 grayscale avatar-echo"
                                            ></div>
                                            <div className="absolute -bottom-0.5 -right-0.5 size-3 bg-yellow-500 rounded-full border-2 border-[#131118]"></div>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-bold text-white truncate">Echo_V2</h4>
                                            <p className="text-xs text-gray-500 truncate">Lifestyle (Suspended)</p>
                                        </div>
                                        <button className="text-gray-500 hover:text-white">
                                            <span className="material-symbols-outlined text-[18px]">more_vert</span>
                                        </button>
                                    </div>
                                </div>

                                {/* Stats Box */}
                                <div className="glass-panel p-4 rounded-xl mt-2 border-primary/20 bg-primary/5">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs font-bold text-primary uppercase">Network Health</span>
                                        <span className="text-xs font-mono text-white">94%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-gradient-to-r from-primary to-secondary w-[94%] shadow-[0_0_10px_rgba(139,92,246,0.5)]"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Footer / Status Bar */}
                    <footer className="mt-8 border-t border-white/5 pt-6 flex flex-col md:flex-row items-center justify-between text-xs text-gray-600 font-mono gap-4">
                        <div className="flex items-center gap-4">
                            <span>SYNAPSE OS v3.4.1</span>
                            <span className="size-1 bg-gray-600 rounded-full"></span>
                            <span>SERVER: US-EAST-1</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-[14px] text-secondary">check_circle</span>
                            <span className="text-gray-400">All Systems Nominal</span>
                        </div>
                    </footer>
                </div>
            </div>
        </main>
    );
}
