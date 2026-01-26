'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import useWebSocket from '../hooks/useWebSocket';
import LogTerminal, { LogEntry } from '../components/LogTerminal';
import SystemMonitor from '../components/SystemMonitor';
import { BotStatus } from '../types';
import { StitchCard } from '../components/StitchCard';
import clsx from 'clsx';
import { ComputerDesktopIcon } from '@heroicons/react/24/outline';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace('localhost', '127.0.0.1') + '/api/v1';

// Componente simples para Status dos Bots
const BotStatusCompact = ({ bots }: { bots?: BotStatus[] }) => {
    return (
        <StitchCard className="p-4 font-mono">
            <h3 className="text-xs font-bold text-synapse-emerald mb-4 flex items-center gap-2 border-b border-white/5 pb-2 uppercase tracking-wider">
                <span className="w-1.5 h-1.5 bg-synapse-emerald rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                Active Nodes
            </h3>
            <div className="space-y-3">
                {(bots || []).map(bot => (
                    <div key={bot.id} className="flex items-center justify-between text-xs border-b border-white/5 pb-2 last:border-0 last:pb-0">
                        <div className="flex flex-col">
                            <span className="text-white font-bold">{bot.name}</span>
                            <span className="text-[10px] text-gray-500">{bot.role}</span>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className={clsx("px-2 py-0.5 rounded text-[10px] uppercase font-bold",
                                bot.status === 'online' ? 'bg-synapse-emerald/10 text-synapse-emerald border border-synapse-emerald/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
                            )}>
                                {bot.status}
                            </span>
                            <span className="text-[9px] text-gray-600 mt-0.5">{bot.uptime || '0s'}</span>
                        </div>
                    </div>
                ))}
                {(!bots || bots.length === 0) && (
                    <div className="text-gray-600 text-xs italic text-center py-2">
                        NO_NODES_DETECTED
                    </div>
                )}
            </div>
        </StitchCard>
    );
};

export default function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [systemStats, setSystemStats] = useState({ cpu_percent: 0, ram_percent: 0, disk_usage: 0 });
    const [bots, setBots] = useState<BotStatus[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdateTime, setLastUpdateTime] = useState<string>('');

    // WebSocket for real-time log updates AND system stats
    useWebSocket({
        onLogEntry: (data) => {
            const newLog = (typeof data === 'string' ? JSON.parse(data) : data) as LogEntry;
            setLogs(prev => {
                const updated = [...prev, newLog].slice(-200); // Keep last 200 logs, appending to end for terminal feel
                return updated;
            });
            // Update time on client to avoid hydration mismatch
            setLastUpdateTime(new Date().toLocaleTimeString());
        },
        onPipelineUpdate: (status) => {
            if (status.system) {
                setSystemStats(status.system);
            }
            if (status.bots) {
                setBots(status.bots);
            }
        }
    });

    const fetchLogs = useCallback(async () => {
        try {
            const [logsRes, statusRes] = await Promise.all([
                fetch(`${API_BASE}/logs/?limit=100`),
                fetch(`${API_BASE}/status`)
            ]);

            if (logsRes.ok) {
                const data = await logsRes.json();
                // API returns newest first, reverse for terminal (oldest top, newest bottom)
                setLogs([...data.logs].reverse());
                setLastUpdateTime(new Date().toLocaleTimeString());
            }

            if (statusRes.ok) {
                const statusData = await statusRes.json();
                if (statusData.system) setSystemStats(statusData.system);
                if (statusData.bots) setBots(statusData.bots);
            }

        } catch (err) {
            console.error("Failed to fetch initial data:", err);
        }
        setLoading(false);
    }, []);

    // Initial load
    useEffect(() => {
        fetchLogs();
    }, [fetchLogs]);


    return (
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans overflow-hidden selection:bg-synapse-primary selection:text-white">
            <Sidebar />

            <main className="flex-1 p-6 flex flex-col h-screen overflow-hidden relative bg-grid-pattern">

                {/* Header */}
                <header className="flex justify-between items-center mb-6 z-10 border-b border-white/10 pb-4 bg-black/40 backdrop-blur-md sticky top-0">
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-3">
                            <ComputerDesktopIcon className="w-8 h-8 text-synapse-emerald" />
                            SYSTEM_DIAGNOSTICS
                        </h1>
                        <p className="text-xs text-synapse-emerald/70 mt-1 uppercase tracking-[0.2em] font-mono">
                            // Realtime_Monitoring_Protocol_v2.0
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">System Time</p>
                            <p className="text-sm text-white font-mono font-bold bg-black/30 px-2 py-1 rounded border border-white/5">{lastUpdateTime || '--:--:--'}</p>
                        </div>
                        <div className={clsx("w-3 h-3 rounded-full shadow-[0_0_10px_currentColor]", loading ? 'bg-synapse-amber animate-bounce text-synapse-amber' : 'bg-synapse-emerald animate-pulse text-synapse-emerald')} />
                    </div>
                </header>

                {/* Main Grid Content */}
                <div className="flex-1 min-h-0 z-10 grid grid-cols-1 lg:grid-cols-4 gap-6">

                    {/* LEFT COLUMN: Metrics & Visuals */}
                    <div className="lg:col-span-1 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
                        {/* Live Visual Feedback */}
                        <StitchCard className="p-1 !border-synapse-emerald/30 shadow-[0_0_20px_rgba(16,185,129,0.1)]">
                            <div className="relative aspect-video bg-[#0f0a15] rounded-lg overflow-hidden group border border-white/5 flex flex-col items-center justify-center">
                                {/* Placeholder Clean State */}
                                <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 z-0">
                                    <div className="w-16 h-16 mb-4 rounded-full border-2 border-synapse-emerald/30 flex items-center justify-center animate-[pulse_3s_linear_infinite]">
                                        <div className="w-12 h-12 rounded-full border-t-2 border-synapse-emerald shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
                                    </div>
                                    <h3 className="text-synapse-emerald font-mono font-bold tracking-[0.2em] text-sm animate-pulse">
                                        SYSTEM_ONLINE
                                    </h3>
                                    <p className="text-[10px] text-synapse-emerald/50 mt-1 font-mono">
                                        MONITORING_ACTIVE
                                    </p>
                                </div>
                                {/* Scanline overlay */}
                                <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(16,185,129,0.05)_50%)] bg-[length:100%_4px] pointer-events-none" />
                                <div className="absolute top-2 left-2 px-2 py-0.5 bg-red-500/90 text-white text-[9px] font-bold uppercase tracking-wider rounded animate-pulse shadow-lg">
                                    Live Feed
                                </div>
                            </div>
                        </StitchCard>

                        {/* System Monitor (Wrapped components should ideally be updated too, but wrapper helps) */}
                        <div className="rounded-xl overflow-hidden border border-white/10 bg-black/20">
                            <SystemMonitor system={systemStats} />
                        </div>

                        {/* Bot Status */}
                        <BotStatusCompact bots={bots} />
                    </div>

                    {/* RIGHT COLUMN: Terminal */}
                    <div className="lg:col-span-3 flex flex-col min-h-0 relative group">
                        {/* Terminal Container */}
                        <StitchCard className="flex-1 h-full !p-0 overflow-hidden flex flex-col !bg-[#0c0c0c] !border-white/10 relative">
                            {/* Scanline Animation for Terminal */}
                            <div className="absolute top-0 left-0 w-full h-1 bg-synapse-emerald/20 animate-scanline z-20 pointer-events-none opacity-30"></div>

                            {/* Toolbar */}
                            <div className="h-8 bg-white/5 border-b border-white/5 flex items-center px-4 gap-2">
                                <div className="w-2.5 h-2.5 rounded-full bg-red-500/50"></div>
                                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></div>
                                <div className="w-2.5 h-2.5 rounded-full bg-green-500/50"></div>
                                <div className="ml-auto text-[10px] text-gray-600 font-mono">bash --synapse-core</div>
                            </div>

                            <LogTerminal logs={logs} className="flex-1 h-full p-4 font-mono text-sm" />
                        </StitchCard>
                    </div>

                </div>
            </main>
        </div>
    );
}
