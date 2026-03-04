'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { getApiUrl } from '../utils/apiClient';

export default function SettingsPage() {
    const [threads, setThreads] = useState(12);
    const [vram, setVram] = useState(24);
    const [nasaKey, setNasaKey] = useState("");
    const [esaKey, setEsaKey] = useState("");
    const [jaxKey, setJaxKey] = useState("");
    const [health, setHealth] = useState("VERIFYING");

    useEffect(() => {
        const loadUplink = async () => {
            try {
                const healthRes = await axios.get(`${getApiUrl()}/api/v1/system/health`);
                setHealth(healthRes.data.status === 'online' ? 'OPTIMAL' : 'DEGRADED');
            } catch (e) {
                setHealth('OFFLINE');
            }

            try {
                const res = await axios.get(`${getApiUrl()}/api/v1/system/settings`);
                const s = res.data;
                if (s?.system?.max_concurrent_tasks) setThreads(s.system.max_concurrent_tasks);
                if (s?.integrations?.openai_api_key) setNasaKey(s.integrations.openai_api_key);
                if (s?.integrations?.groq_api_key) setEsaKey(s.integrations.groq_api_key);
                if (s?.integrations?.gemini_api_key) setJaxKey(s.integrations.gemini_api_key);
            } catch (e) {
                toast.error("Telemetry Uplink Failed: Couldn't fetch settings");
            }
        };
        loadUplink();
    }, []);

    const saveSettings = async () => {
        try {
            const payloadFields: any = {
                system: { max_concurrent_tasks: threads },
                integrations: {}
            };

            if (nasaKey && !nasaKey.includes('sk-...')) payloadFields.integrations.openai_api_key = nasaKey;
            if (esaKey && !esaKey.includes('...')) payloadFields.integrations.groq_api_key = esaKey;
            if (jaxKey && !jaxKey.includes('...')) payloadFields.integrations.gemini_api_key = jaxKey;

            if (Object.keys(payloadFields.integrations).length === 0) {
                delete payloadFields.integrations;
            }

            await axios.post(`${getApiUrl()}/api/v1/system/settings`, { settings: payloadFields });
            toast.success("Matrix parameters updated successfully.");
        } catch (e) {
            toast.error("Failed to sequence Matrix override.");
        }
    };

    return (
        <div className="flex-1 overflow-x-hidden min-h-screen flex flex-col relative text-slate-100 bg-[#020408] selection:bg-cyan-500/30 selection:text-cyan-500 font-display">
            {/* Background elements */}
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
                <div className="absolute inset-0 bg-grid-pattern blueprint-grid opacity-15"></div>
                <div className="absolute inset-0 z-0 scanning-line"></div>

                {/* 3D wireframe decoration */}
                <div className="absolute right-[-5%] top-[15%] w-[800px] h-[800px] opacity-[0.07] flex items-center justify-center transform perspective-[1000px] rotate-12 pointer-events-none">
                    <div className="wireframe-model relative w-full h-full border border-sky-500/20 rounded-full animate-spin-slow border-dashed">
                        <div className="absolute inset-[15%] border border-sky-500/10 rounded-full animate-[spin_15s_linear_infinite_reverse]"></div>
                        <div className="absolute inset-[35%] border border-sky-500/20 rounded-full border-dashed animate-[spin_25s_linear_infinite]"></div>
                        <div className="absolute top-1/2 left-0 right-0 h-px bg-sky-500/20"></div>
                        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-sky-500/20"></div>
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 border border-sky-500/40 rotate-45"></div>
                    </div>
                </div>
            </div>

            <div className="flex flex-1 overflow-hidden z-10 relative">
                <main className="flex-1 overflow-y-auto relative bg-transparent scroll-smooth z-10">
                    <div className="max-w-[1600px] mx-auto px-8 py-10 relative z-10">
                        {/* Header Area */}
                        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-slate-800 pb-8 bg-gradient-to-r from-transparent via-slate-900/40 to-transparent">
                            <div className="relative">
                                <div className="absolute -left-4 top-2 bottom-2 w-1 bg-sky-500/50 rounded-sm"></div>
                                <div className="flex items-center gap-2 text-sky-500/80 mb-2 font-mono text-[10px] uppercase tracking-[0.2em] pl-2">
                                    <span className="w-1.5 h-1.5 bg-sky-500 rounded-full animate-pulse shadow-[0_0_5px_#0ea5e9]"></span>
                                    <span>System Admin Level 1</span>
                                    <span className="text-slate-500 mx-2">//</span>
                                    <span>ID: 994-AZ-20</span>
                                </div>
                                <h1 className="text-5xl font-bold text-white tracking-tighter uppercase font-display relative inline-block pl-2">
                                    Core Calibration
                                    <span className="text-sky-500 ml-3">Pro</span>
                                    <div className="absolute -top-3 -right-6 text-[9px] text-sky-500 border border-sky-500/50 bg-sky-500/10 px-1.5 py-0.5 font-mono tracking-widest rounded-sm">BETA_BUILD</div>
                                </h1>
                                <p className="text-slate-400 text-sm font-mono mt-3 max-w-2xl pl-2 text-balance leading-relaxed">
                                    :: Configure high-bandwidth neural pathways, external uplinks, and distributed render farm allocation across the grid.
                                </p>
                            </div>

                            <div className="flex gap-4">
                                <button className="ripple-btn px-5 py-2.5 border border-slate-700 bg-[#0f172a] text-slate-400 text-[11px] font-mono hover:text-white hover:border-white/30 transition-all uppercase tracking-widest clip-path-slant shadow-lg">
                                    [ Reset_Defaults ]
                                </button>
                                <button
                                    onClick={saveSettings}
                                    className="ripple-btn px-8 py-2.5 bg-sky-500/10 border border-sky-500 text-sky-500 font-bold text-[11px] font-mono hover:bg-sky-500 hover:text-[#0b0f11] hover:shadow-[0_0_15px_-3px_rgba(14,165,233,0.4)] transition-all uppercase tracking-widest clip-path-slant flex items-center gap-3 group shadow-[0_0_15px_-5px_#0ea5e9]"
                                >
                                    <span className="material-symbols-outlined text-[18px] group-hover:animate-bounce">save</span>
                                    Save_Config
                                </button>
                            </div>
                        </div>

                        {/* Content Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                            <div className="lg:col-span-8 flex flex-col gap-8">

                                <section className="vault-card rounded-sm p-8 group hover:z-20 transition-all duration-300">
                                    <div className="tech-corner tech-corner-tl shadow-[0_0_5px_#0ea5e9]"></div>
                                    <div className="tech-corner tech-corner-tr shadow-[0_0_5px_#0ea5e9]"></div>
                                    <div className="tech-corner tech-corner-bl shadow-[0_0_5px_#0ea5e9]"></div>
                                    <div className="tech-corner tech-corner-br shadow-[0_0_5px_#0ea5e9]"></div>

                                    <div className="flex items-center gap-5 mb-8 border-b border-dashed border-slate-700 pb-6 relative">
                                        <div className="absolute bottom-0 left-0 w-24 h-[1px] bg-sky-500/50"></div>
                                        <div className="p-4 border border-sky-500/30 bg-sky-500/5 text-sky-500 relative overflow-hidden">
                                            <div className="absolute inset-0 bg-sky-500/5 animate-pulse"></div>
                                            <span className="material-symbols-outlined animate-spin-slow text-3xl" style={{ animationDuration: '10s' }}>settings_system_daydream</span>
                                        </div>
                                        <div className="flex-1">
                                            <h2 className="text-xl font-bold text-white uppercase font-mono tracking-[0.2em] flex items-center gap-3">
                                                Security Vault
                                                <span className="text-[9px] bg-red-500/10 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-sm tracking-widest shadow-[0_0_10px_-3px_rgba(239,68,68,0.4)]">RESTRICTED_ACCESS</span>
                                            </h2>
                                            <p className="text-xs text-slate-400 font-mono mt-1 flex items-center gap-2">
                                                <span className="text-sky-500">&gt;</span>
                                                Deep space telemetry credentials
                                            </p>
                                        </div>
                                        <div className="text-[10px] font-mono text-sky-500/50 border border-sky-500/20 px-2 py-1 bg-sky-500/5">
                                            SEC_LEVEL_5
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <div className="space-y-3 group/input relative">
                                            <div className="flex justify-between items-end">
                                                <label className="text-[11px] font-bold text-sky-400 uppercase tracking-widest font-mono flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-[12px]">key</span>
                                                    NASA_UPLINK_KEY
                                                </label>
                                                <span className="text-[9px] text-emerald-500 font-mono opacity-0 group-hover/input:opacity-100 transition-opacity tracking-wider">[ ENCRYPTED_AES-256 ]</span>
                                            </div>
                                            <div className="relative h-16 bg-[#050a14] border border-slate-800 overflow-hidden group-hover/input:border-sky-500/50 transition-colors shadow-inner">
                                                <div className="absolute inset-0 z-20 bg-[#0b101b] vault-door flex items-center justify-center transition-transform duration-500 ease-out group-hover/input:-translate-y-full border-b border-sky-500/50 shadow-lg">
                                                    <div className="flex flex-col items-center gap-1">
                                                        <div className="flex items-center gap-2 text-gray-500">
                                                            <span className="material-symbols-outlined text-sm">lock</span>
                                                            <span className="text-[9px] font-mono uppercase tracking-widest">LOCKED</span>
                                                        </div>
                                                        <div className="h-0.5 w-16 bg-gray-700/50 relative overflow-hidden">
                                                            <div className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent via-gray-500 to-transparent -translate-x-full group-hover/input:animate-[shimmer_1s_infinite]"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="absolute inset-0 z-10 flex items-center px-4 bg-[#020408]">
                                                    <input className="w-full bg-transparent border-none text-sky-500 font-mono tracking-[0.2em] text-sm focus:ring-0 p-0 shadow-[0_0_15px_-5px_rgba(14,165,233,0.5)] outline-none" type="text" value={nasaKey} onChange={e => setNasaKey(e.target.value)} />
                                                    <button className="text-sky-500/40 hover:text-white transition-colors p-2 hover:bg-white/5 rounded-full">
                                                        <span className="material-symbols-outlined text-[16px]">content_copy</span>
                                                    </button>
                                                </div>
                                                <div className="absolute inset-0 bg-sky-500/0 z-0 group-hover/input:bg-sky-500/5 group-hover/input:shadow-[inset_0_0_30px_rgba(14,165,233,0.15)] transition-all duration-500"></div>
                                            </div>
                                        </div>

                                        <div className="space-y-3 group/input relative">
                                            <div className="flex justify-between items-end">
                                                <label className="text-[11px] font-bold text-indigo-400 uppercase tracking-widest font-mono flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-[12px]">token</span>
                                                    ESA_ACCESS_TOKEN
                                                </label>
                                                <span className="text-[9px] text-emerald-500 font-mono opacity-0 group-hover/input:opacity-100 transition-opacity tracking-wider">[ ENCRYPTED_AES-256 ]</span>
                                            </div>
                                            <div className="relative h-16 bg-[#050a14] border border-slate-800 overflow-hidden group-hover/input:border-sky-500/50 transition-colors shadow-inner">
                                                <div className="absolute inset-0 z-20 bg-[#0b101b] vault-door flex items-center justify-center transition-transform duration-500 ease-out group-hover/input:-translate-y-full border-b border-sky-500/50 shadow-lg">
                                                    <div className="flex flex-col items-center gap-1">
                                                        <div className="flex items-center gap-2 text-gray-500">
                                                            <span className="material-symbols-outlined text-sm">lock</span>
                                                            <span className="text-[9px] font-mono uppercase tracking-widest">LOCKED</span>
                                                        </div>
                                                        <div className="h-0.5 w-16 bg-gray-700/50 relative overflow-hidden">
                                                            <div className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent via-gray-500 to-transparent -translate-x-full group-hover/input:animate-[shimmer_1s_infinite]"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="absolute inset-0 z-10 flex items-center px-4 bg-[#020408]">
                                                    <input className="w-full bg-transparent border-none text-indigo-500 font-mono tracking-[0.2em] text-sm focus:ring-0 p-0 shadow-[0_0_15px_-5px_rgba(99,102,241,0.5)] outline-none" type="text" placeholder="GROQ_KEY" value={esaKey} onChange={e => setEsaKey(e.target.value)} />
                                                    <button className="text-indigo-500/40 hover:text-white transition-colors p-2 hover:bg-white/5 rounded-full">
                                                        <span className="material-symbols-outlined text-[16px]">content_copy</span>
                                                    </button>
                                                </div>
                                                <div className="absolute inset-0 bg-indigo-500/0 z-0 group-hover/input:bg-indigo-500/5 group-hover/input:shadow-[inset_0_0_30px_rgba(99,102,241,0.15)] transition-all duration-500"></div>
                                            </div>
                                        </div>

                                        <div className="space-y-3 group/input relative md:col-span-2">
                                            <div className="flex justify-between items-end">
                                                <label className="text-[11px] font-bold text-rose-400 uppercase tracking-widest font-mono flex items-center gap-2">
                                                    <span className="material-symbols-outlined text-[12px]">network_node</span>
                                                    JAX_NEURAL_LINK
                                                </label>
                                                <span className="text-[9px] text-emerald-500 font-mono opacity-0 group-hover/input:opacity-100 transition-opacity tracking-wider">[ ENCRYPTED_AES-256 ]</span>
                                            </div>
                                            <div className="relative h-16 bg-[#050a14] border border-slate-800 overflow-hidden group-hover/input:border-sky-500/50 transition-colors shadow-inner">
                                                <div className="absolute inset-0 z-20 bg-[#0b101b] vault-door flex items-center justify-center transition-transform duration-500 ease-out group-hover/input:-translate-y-full border-b border-sky-500/50 shadow-lg">
                                                    <div className="flex flex-col items-center gap-1">
                                                        <div className="flex items-center gap-2 text-gray-500">
                                                            <span className="material-symbols-outlined text-sm">lock</span>
                                                            <span className="text-[9px] font-mono uppercase tracking-widest">LOCKED</span>
                                                        </div>
                                                        <div className="h-0.5 w-16 bg-gray-700/50 relative overflow-hidden">
                                                            <div className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent via-gray-500 to-transparent -translate-x-full group-hover/input:animate-[shimmer_1s_infinite]"></div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="absolute inset-0 z-10 flex items-center px-4 bg-[#020408]">
                                                    <input className="w-full bg-transparent border-none text-rose-500 font-mono tracking-[0.2em] text-sm focus:ring-0 p-0 shadow-[0_0_15px_-5px_rgba(244,63,94,0.5)] outline-none" type="text" placeholder="GEMINI_KEY" value={jaxKey} onChange={e => setJaxKey(e.target.value)} />
                                                    <button className="text-rose-500/40 hover:text-white transition-colors p-2 hover:bg-white/5 rounded-full">
                                                        <span className="material-symbols-outlined text-[16px]">content_copy</span>
                                                    </button>
                                                </div>
                                                <div className="absolute inset-0 bg-rose-500/0 z-0 group-hover/input:bg-rose-500/5 group-hover/input:shadow-[inset_0_0_30px_rgba(244,63,94,0.15)] transition-all duration-500"></div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="col-span-1 md:col-span-2 mt-4 pt-6 border-t border-slate-800 relative">
                                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-1 bg-slate-700"></div>
                                        <div className="flex items-center justify-between p-4 bg-[#080d16] border border-slate-700 hover:border-sky-500/30 transition-colors group rounded-sm shadow-md">
                                            <div className="flex items-center gap-6">
                                                <div className="industrial-toggle shadow-lg">
                                                    <input defaultChecked type="checkbox" />
                                                    <div className="toggle-track"></div>
                                                    <div className="toggle-lever"></div>
                                                    <div className="indicator-light"></div>
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-bold text-white font-mono uppercase tracking-wide">Auto-rotate Keys</span>
                                                    <span className="text-[10px] text-slate-400 font-mono mt-0.5">Monthly rotation cycle active</span>
                                                </div>
                                            </div>
                                            <div className="text-sky-500 opacity-30 group-hover:opacity-100 transition-opacity">
                                                <span className="material-symbols-outlined animate-spin-slow">autorenew</span>
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                <section className="bg-[#0b101b]/60 border border-slate-800 p-1 relative overflow-hidden group hover:shadow-[0_0_40px_-10px_rgba(14,165,233,0.15)] transition-all duration-500">
                                    <div className="absolute inset-0 bg-grid-pattern blueprint-grid opacity-10 pointer-events-none"></div>
                                    <div className="border border-slate-700 p-8 relative z-10 backdrop-blur-sm">
                                        <div className="flex items-center justify-between mb-8">
                                            <div className="flex items-center gap-4">
                                                <div className="p-2 border border-indigo-500/30 text-indigo-500 bg-indigo-500/5 shadow-[0_0_15px_-5px_rgba(99,102,241,0.5)]">
                                                    <span className="material-symbols-outlined">precision_manufacturing</span>
                                                </div>
                                                <div>
                                                    <h2 className="text-lg font-bold text-white font-mono uppercase tracking-[0.2em]">Processing Unit</h2>
                                                    <p className="text-xs text-slate-400 font-mono">:: Neural processing allocation matrix</p>
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end border-r-2 border-green-500/30 pr-3">
                                                <span className="text-[9px] font-mono text-slate-400 uppercase tracking-widest">SYS_STATUS</span>
                                                <span className={`text-xs font-mono font-bold ${health === 'OPTIMAL' ? 'text-green-400 shadow-[0_0_10px_rgba(74,222,128,0.2)]' : 'text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.2)]'}`}>
                                                    {health}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="space-y-10">
                                            <div className="space-y-3 relative group/slider">
                                                <div className="flex justify-between items-end border-b border-slate-800 pb-2 mb-2">
                                                    <label className="text-[11px] font-bold text-sky-400 uppercase font-mono tracking-wider flex items-center">
                                                        <span className="mr-2 text-sky-500">&gt;&gt;</span>Thread_Count
                                                    </label>
                                                    <span className="text-xl font-bold font-mono text-white tracking-widest shadow-[0_0_15px_-3px_rgba(14,165,233,0.4)] px-2">{threads}<span className="text-xs text-slate-400 ml-1">/64</span></span>
                                                </div>
                                                <div className="relative w-full h-10 bg-[#050a14] border border-slate-800 flex items-center px-1 shadow-inner overflow-hidden">
                                                    <div className="absolute inset-0 flex justify-between px-2 opacity-20 pointer-events-none z-0">
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                    </div>
                                                    <input className="w-full h-full bg-transparent appearance-none cursor-pointer z-20 hover:opacity-100 opacity-0 absolute inset-0" title="Slide" max="64" min="1" type="range" value={threads} onChange={(e) => setThreads(parseInt(e.target.value))} />
                                                    <div className="absolute left-0 top-0 bottom-0 bg-sky-500/20 border-r-2 border-sky-500 pointer-events-none z-10 flex justify-end items-center pr-1" style={{ width: `${(threads / 64) * 100}%` }}>
                                                        <div className="w-4 h-8 bg-sky-500 border border-white/50 box-shadow-[0_0_15px_#0ea5e9]"></div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="space-y-3 relative group/slider">
                                                <div className="flex justify-between items-end border-b border-slate-800 pb-2 mb-2">
                                                    <label className="text-[11px] font-bold text-sky-400 uppercase font-mono tracking-wider flex items-center">
                                                        <span className="mr-2 text-indigo-500">&gt;&gt;</span>VRAM_Allocation
                                                    </label>
                                                    <span className="text-xl font-bold font-mono text-white tracking-widest shadow-[0_0_15px_-5px_rgba(99,102,241,0.5)] px-2">{vram}<span className="text-xs text-slate-400 ml-1">GB</span></span>
                                                </div>
                                                <div className="relative w-full h-10 bg-[#050a14] border border-slate-800 flex items-center px-1 shadow-inner overflow-hidden">
                                                    <div className="absolute inset-0 flex justify-between px-2 opacity-20 pointer-events-none z-0">
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                        <div className="w-px h-full bg-white"></div>
                                                    </div>
                                                    <input className="w-full h-full bg-transparent appearance-none cursor-pointer z-20 hover:opacity-100 opacity-0 absolute inset-0" title="Slide" max="48" min="1" type="range" value={vram} onChange={(e) => setVram(parseInt(e.target.value))} />
                                                    <div className="absolute left-0 top-0 bottom-0 bg-indigo-500/20 border-r-2 border-indigo-500 pointer-events-none z-10 flex justify-end items-center pr-1" style={{ width: `${(vram / 48) * 100}%` }}>
                                                        <div className="w-4 h-8 bg-indigo-500 border border-white/50 box-shadow-[0_0_15px_#6366f1]"></div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent my-8 opacity-50"></div>

                                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                                <div className="flex items-center justify-between p-5 bg-[#080d16] border border-slate-800 relative group hover:border-sky-500/40 transition-colors shadow-md">
                                                    <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-white/20 group-hover:border-sky-500/60 transition-colors"></div>
                                                    <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-white/20 group-hover:border-sky-500/60 transition-colors"></div>
                                                    <span className="text-xs text-slate-200 font-mono uppercase tracking-wide">GPU Acceleration</span>
                                                    <div className="industrial-toggle">
                                                        <input defaultChecked type="checkbox" />
                                                        <div className="toggle-track"></div>
                                                        <div className="toggle-lever"></div>
                                                        <div className="indicator-light"></div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center justify-between p-5 bg-[#080d16] border border-slate-800 relative group hover:border-sky-500/40 transition-colors shadow-md">
                                                    <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-white/20 group-hover:border-sky-500/60 transition-colors"></div>
                                                    <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-white/20 group-hover:border-sky-500/60 transition-colors"></div>
                                                    <span className="text-xs text-slate-200 font-mono uppercase tracking-wide">Bg Processing</span>
                                                    <div className="industrial-toggle">
                                                        <input type="checkbox" />
                                                        <div className="toggle-track"></div>
                                                        <div className="toggle-lever"></div>
                                                        <div className="indicator-light"></div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </section>
                            </div>

                            <div className="lg:col-span-4 flex flex-col gap-8">
                                <section className="bg-[#050a14] border border-slate-800 p-6 relative group hover:border-amber-500/40 transition-colors duration-300">
                                    <div className="absolute -right-1 -top-1 w-16 h-16 border-t-2 border-r-2 border-amber-500/30 rounded-tr-3xl group-hover:border-amber-500/60 transition-colors"></div>
                                    <div className="flex items-center gap-3 mb-6">
                                        <div className="p-1.5 border border-amber-500/20 bg-amber-500/5 rounded-sm">
                                            <span className="material-symbols-outlined text-amber-500 text-sm">palette</span>
                                        </div>
                                        <h2 className="text-sm font-bold text-white uppercase font-mono tracking-widest">Interface Params</h2>
                                    </div>

                                    <div className="space-y-6">
                                        <div>
                                            <label className="block text-[10px] font-bold text-slate-500 mb-2 uppercase font-mono tracking-wider">Theme Preset</label>
                                            <div className="relative">
                                                <select className="w-full bg-[#0a101d] border border-slate-700 text-white text-xs font-mono rounded-none focus:ring-1 focus:ring-sky-500 focus:border-sky-500 p-3 uppercase tracking-wide appearance-none cursor-pointer hover:bg-slate-800 transition-colors outline-none">
                                                    <option>Deep Space [Default]</option>
                                                    <option>Orbital Station Light</option>
                                                    <option>High Contrast Tech</option>
                                                </select>
                                                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-white/50">
                                                    <span className="material-symbols-outlined text-sm">expand_more</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <label className="block text-[10px] font-bold text-slate-500 mb-2 uppercase font-mono tracking-wider">Hologram Hue</label>
                                            <div className="grid grid-cols-4 gap-3">
                                                <button className="h-10 border border-white/20 bg-[#0ea5e9]/20 relative group hover:bg-[#0ea5e9]/40 transition-colors overflow-hidden">
                                                    <div className="absolute inset-0 border-2 border-white opacity-0 group-hover:opacity-100 transition-opacity scale-90 group-hover:scale-100"></div>
                                                    <div className="w-2 h-2 bg-[#0ea5e9] rounded-full mx-auto shadow-[0_0_8px_#0ea5e9]"></div>
                                                </button>
                                                <button className="h-10 border border-white/20 bg-[#6366f1]/20 hover:bg-[#6366f1]/40 hover:border-white transition-colors">
                                                    <div className="w-2 h-2 bg-[#6366f1] rounded-full mx-auto shadow-[0_0_8px_#6366f1]"></div>
                                                </button>
                                                <button className="h-10 border border-white/20 bg-[#10b981]/20 hover:bg-[#10b981]/40 hover:border-white transition-colors">
                                                    <div className="w-2 h-2 bg-[#10b981] rounded-full mx-auto shadow-[0_0_8px_#10b981]"></div>
                                                </button>
                                                <button className="h-10 border border-white/20 bg-[#f59e0b]/20 hover:bg-[#f59e0b]/40 hover:border-white transition-colors">
                                                    <div className="w-2 h-2 bg-[#f59e0b] rounded-full mx-auto shadow-[0_0_8px_#f59e0b]"></div>
                                                </button>
                                            </div>
                                        </div>

                                        <div className="pt-5 border-t border-slate-800 border-dashed">
                                            <label className="flex items-center gap-3 cursor-pointer group">
                                                <div className="relative flex items-center justify-center size-5 border border-slate-700 bg-[#050a14] group-hover:border-sky-500 transition-colors">
                                                    <input defaultChecked className="peer appearance-none absolute inset-0 w-full h-full cursor-pointer z-10" type="checkbox" />
                                                    <div className="w-3 h-3 bg-sky-500 opacity-0 peer-checked:opacity-100 transition-opacity shadow-[0_0_5px_#0ea5e9]"></div>
                                                </div>
                                                <span className="text-xs font-mono uppercase text-slate-300 group-hover:text-white transition-colors">Reduce UI Motion</span>
                                            </label>
                                        </div>
                                    </div>
                                </section>

                                <div className="relative overflow-hidden bg-gradient-to-br from-[#0b101b] to-black border border-slate-700 p-6 transition-all hover:scale-[1.01] duration-300 group shadow-[0_0_15px_-3px_rgba(14,165,233,0.4)]">
                                    <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 bg-[length:100%_2px,3px_100%] pointer-events-none opacity-50"></div>
                                    <div className="absolute top-0 left-0 w-full h-1 bg-sky-500/30 shadow-[0_0_15px_#0ea5e9] animate-scan z-0 opacity-20"></div>

                                    <div className="relative z-10">
                                        <div className="flex justify-between items-start mb-4">
                                            <h3 className="text-[10px] font-bold text-sky-500 uppercase tracking-[0.2em] font-mono border-b border-sky-500/20 pb-1">Plan_Matrix</h3>
                                            <div className="relative">
                                                <span className="material-symbols-outlined text-white/10 text-5xl absolute right-0 -top-4 group-hover:text-sky-500/20 transition-colors duration-500">rocket</span>
                                            </div>
                                        </div>

                                        <div className="flex items-baseline gap-3 mb-8">
                                            <span className="text-4xl font-bold text-white font-display tracking-tighter drop-shadow-[0_0_15px_rgba(14,165,233,0.4)]">PRO</span>
                                            <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider bg-white/5 px-2 py-0.5 rounded-sm">Enterprise Tier</span>
                                        </div>

                                        <div className="space-y-6">
                                            <div className="space-y-1.5">
                                                <div className="flex justify-between text-[10px] uppercase font-mono text-slate-300 tracking-wider">
                                                    <span>Credits_Consumption</span>
                                                    <span className="text-sky-500 font-bold">84%</span>
                                                </div>
                                                <div className="h-2.5 w-full bg-[#050a14] border border-slate-700 relative overflow-hidden rounded-sm">
                                                    <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-sky-500 to-blue-400 w-[84%] shadow-[0_0_15px_#0ea5e9]"></div>
                                                    <div className="absolute top-0 bottom-0 w-[5px] bg-white/80 blur-[2px] animate-[ping_3s_linear_infinite] left-[84%]"></div>
                                                </div>
                                            </div>

                                            <div className="space-y-1.5">
                                                <div className="flex justify-between text-[10px] uppercase font-mono text-slate-300 tracking-wider">
                                                    <span>Data_Storage</span>
                                                    <span className="text-indigo-500 font-bold">1.2TB / 2TB</span>
                                                </div>
                                                <div className="h-2.5 w-full bg-[#050a14] border border-slate-700 relative overflow-hidden rounded-sm">
                                                    <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-indigo-500 to-indigo-400 w-[60%] shadow-[0_0_15px_#6366f1]"></div>
                                                </div>
                                            </div>
                                        </div>

                                        <button className="ripple-btn mt-8 w-full py-3.5 border border-sky-500/50 text-sky-500 text-xs font-bold font-mono uppercase hover:bg-sky-500 hover:text-black hover:shadow-[0_0_20px_rgba(14,165,233,0.6)] transition-all tracking-[0.15em] relative overflow-hidden group/btn">
                                            <span className="relative z-10 flex items-center justify-center gap-2">
                                                Upgrade_Matrix
                                                <span className="material-symbols-outlined text-sm group-hover/btn:translate-x-1 transition-transform">arrow_forward</span>
                                            </span>
                                        </button>
                                    </div>
                                </div>

                                <div className="font-mono text-[10px] text-slate-500 opacity-60 p-3 border-l-2 border-slate-800 bg-slate-900/30">
                                    <p className="mb-1 text-sky-500/70">&gt; System check complete.</p>
                                    <p className="mb-1">&gt; Telemetry uplink established [OK].</p>
                                    <p className="mb-1">&gt; Render farm at 42% capacity.</p>
                                    <p className="animate-pulse text-white">&gt; Waiting for user input<span className="animate-pulse">_</span></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}
