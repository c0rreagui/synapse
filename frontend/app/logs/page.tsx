'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import Badge from '../components/Badge';
import Spinner from '../components/Spinner';
import EmptyState from '../components/EmptyState';
import useWebSocket from '../hooks/useWebSocket';
import {
    ArrowPathIcon, TrashIcon,
    CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XCircleIcon,
    ClockIcon, FunnelIcon
} from '@heroicons/react/24/outline';

interface LogEntry {
    id: string;
    timestamp: string;
    level: 'info' | 'success' | 'warning' | 'error';
    message: string;
    source: string;
}

const API_BASE = 'http://localhost:8000/api/v1';

export default function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [stats, setStats] = useState({ info: 0, success: 0, warning: 0, error: 0, total: 0 });
    const [filter, setFilter] = useState<string>('all');
    const [autoScroll, setAutoScroll] = useState(true);
    const [loading, setLoading] = useState(true);
    const [lastUpdateTime, setLastUpdateTime] = useState<string>('');
    const logContainerRef = useRef<HTMLDivElement>(null);

    // WebSocket for real-time log updates
    useWebSocket({
        onLogEntry: (data) => {
            // Ensure data is treated as LogEntry
            const newLog = (typeof data === 'string' ? JSON.parse(data) : data) as LogEntry;

            // Filter client-side if needed, but usually we define that in the prompt or backend
            setLogs(prev => {
                const updated = [newLog, ...prev].slice(0, 200); // Keep last 200 logs
                return updated;
            });
            setLastUpdateTime(new Date().toLocaleTimeString());

            setStats(prev => ({
                ...prev,
                [newLog.level]: (prev[newLog.level as keyof typeof prev] || 0) + 1,
                total: prev.total + 1
            }));
        },
    });

    const fetchLogs = useCallback(async () => {
        try {
            const [logsRes, statsRes] = await Promise.all([
                fetch(`${API_BASE}/logs/?limit=100${filter !== 'all' ? `&level=${filter}` : ''}`),
                fetch(`${API_BASE}/logs/stats`)
            ]);

            if (logsRes.ok) {
                const data = await logsRes.json();
                setLogs(data.logs);
                setLastUpdateTime(new Date().toLocaleTimeString());
            }

            if (statsRes.ok) {
                setStats(await statsRes.json());
            }
        } catch (err) {
            console.error("Failed to fetch logs:", err);
        }
        setLoading(false);
    }, [filter]);

    const clearLogs = async () => {
        if (!confirm('Tem certeza que deseja limpar todos os logs?')) return;
        try {
            await fetch(`${API_BASE}/logs/clear`, { method: 'DELETE' });
            setLogs([]);
            setStats({ info: 0, success: 0, warning: 0, error: 0, total: 0 });
        } catch {
            console.error("Failed to clear logs");
        }
    };

    const addTestLog = async (level: string) => {
        try {
            await fetch(`${API_BASE}/logs/add?level=${level}&message=Log de teste (${level})&source=frontend`, { method: 'POST' });
            // No need to fetchLogs here, WebSocket should handle it
        } catch { }
    };

    // Initial load
    useEffect(() => {
        fetchLogs();
    }, [fetchLogs]);

    // Auto-scroll logic
    useEffect(() => {
        if (autoScroll && logContainerRef.current) {
            // Scroll to top because list is reversed (newest first)
            logContainerRef.current.scrollTop = 0;
        }
    }, [logs, autoScroll]);

    const getLevelIcon = (level: string) => {
        switch (level) {
            case 'success': return <CheckCircleIcon className="w-4 h-4 text-cmd-green" />;
            case 'warning': return <ExclamationTriangleIcon className="w-4 h-4 text-cmd-yellow" />;
            case 'error': return <XCircleIcon className="w-4 h-4 text-cmd-red" />;
            default: return <InformationCircleIcon className="w-4 h-4 text-cmd-blue" />;
        }
    };

    const getLevelClass = (level: string) => {
        switch (level) {
            case 'success': return 'text-cmd-green bg-cmd-green/10 border-cmd-green/20';
            case 'warning': return 'text-cmd-yellow bg-cmd-yellow/10 border-cmd-yellow/20';
            case 'error': return 'text-cmd-red bg-cmd-red/10 border-cmd-red/20';
            default: return 'text-cmd-blue bg-cmd-blue/10 border-cmd-blue/20';
        }
    };

    return (
        <div className="flex min-h-screen bg-cmd-bg text-gray-300 font-sans selection:bg-cmd-purple selection:text-white">
            <Sidebar />

            <main className="flex-1 p-8 overflow-y-auto max-h-screen custom-scrollbar">
                {/* Header */}
                <header className="flex items-center justify-between mb-8 fade-in">
                    <div>
                        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400 tracking-tight">System Logs</h2>
                        <p className="text-xs text-cmd-text-muted flex items-center gap-2 font-mono mt-1">
                            <ClockIcon className="w-3 h-3" /> Eventos em tempo real via WebSocket
                        </p>
                    </div>
                    <div className="flex gap-2">
                        {/* Test Buttons - Hidden on very small screens */}
                        <div className="hidden lg:flex gap-2 mr-4">
                            {['info', 'success', 'warning', 'error'].map(level => (
                                <button
                                    key={level}
                                    onClick={() => addTestLog(level)}
                                    className={`px-3 py-1.5 rounded-lg border text-xs font-bold uppercase tracking-wider transition-all hover:scale-105 active:scale-95 ${getLevelClass(level)}`}
                                >
                                    + {level}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={clearLogs}
                            title="Limpar todos os logs"
                            className="p-2.5 rounded-lg border border-cmd-border bg-cmd-card text-gray-400 hover:text-cmd-red hover:border-cmd-red/30 transition-all"
                        >
                            <TrashIcon className="w-5 h-5" />
                        </button>
                        <button
                            onClick={fetchLogs}
                            title="Forçar atualização"
                            className="p-2.5 rounded-lg border border-cmd-border bg-cmd-card text-gray-400 hover:text-white hover:bg-white/5 transition-all"
                        >
                            <ArrowPathIcon className="w-5 h-5" />
                        </button>
                    </div>
                </header>

                {/* Filters & Controls */}
                <div className="flex flex-wrap items-center gap-4 mb-6 fade-in stagger-1">
                    <div className="flex items-center gap-2 p-1 rounded-lg bg-cmd-card border border-cmd-border">
                        <div className="px-3 py-1.5 text-xs font-bold text-gray-500 uppercase flex items-center gap-2">
                            <FunnelIcon className="w-3 h-3" /> Filtro
                        </div>
                        {['all', 'info', 'success', 'warning', 'error'].map((level) => (
                            <button
                                key={level}
                                onClick={() => setFilter(level)}
                                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${filter === level
                                    ? 'bg-white/10 text-white shadow-sm'
                                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                                    }`}
                            >
                                {level === 'all' ? 'Todos' : level.charAt(0).toUpperCase() + level.slice(1)}
                            </button>
                        ))}
                    </div>

                    <div className="ml-auto flex items-center gap-3 bg-cmd-card px-4 py-2 rounded-lg border border-cmd-border hover:border-cmd-purple/30 transition-colors">
                        <span className="text-xs font-mono text-gray-400">AUTO-SCROLL</span>
                        <button
                            onClick={() => setAutoScroll(!autoScroll)}
                            className={`w-10 h-5 rounded-full relative transition-colors duration-300 ${autoScroll ? 'bg-cmd-green' : 'bg-gray-700'}`}
                        >
                            <div className={`w-3 h-3 bg-white rounded-full absolute top-1 transition-transform duration-300 ${autoScroll ? 'translate-x-6' : 'translate-x-1'}`} />
                        </button>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8 fade-in stagger-2">
                    {[
                        { label: 'Info', count: stats.info, color: 'text-cmd-blue', border: 'border-cmd-blue/20' },
                        { label: 'Success', count: stats.success, color: 'text-cmd-green', border: 'border-cmd-green/20' },
                        { label: 'Warning', count: stats.warning, color: 'text-cmd-yellow', border: 'border-cmd-yellow/20' },
                        { label: 'Error', count: stats.error, color: 'text-cmd-red', border: 'border-cmd-red/20' },
                    ].map((stat) => (
                        <div key={stat.label} className={`bg-cmd-card border border-cmd-border rounded-xl p-4 flex flex-col items-center justify-center hover:border-opacity-50 transition-all group ${stat.border}`}>
                            <span className={`text-2xl font-bold font-mono ${stat.color} group-hover:scale-110 transition-transform`}>
                                {stat.count}
                            </span>
                            <span className="text-xs text-gray-500 uppercase tracking-widest mt-1">{stat.label}</span>
                        </div>
                    ))}
                </div>

                {/* Live Monitor + Log Stream Layout */}
                <div className="flex flex-col xl:flex-row gap-6 fade-in stagger-3 flex-1 overflow-hidden" style={{ maxHeight: 'calc(100vh - 350px)', minHeight: '400px' }}>

                    {/* LIVE MONITOR PANEL */}
                    <div className="xl:w-1/3 bg-cmd-card border border-cmd-border rounded-xl flex flex-col overflow-hidden">
                        <div className="p-4 border-b border-cmd-border bg-black/20 flex justify-between items-center">
                            <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                                </span>
                                Live Visual Feedback
                            </h3>
                            <span className="text-[10px] bg-red-500/10 text-red-500 border border-red-500/20 px-2 py-0.5 rounded font-mono">
                                REAL-TIME
                            </span>
                        </div>
                        <div className="p-4 flex-1 flex items-center justify-center bg-black relative group">
                            {/* Image with cache busting */}
                            <img
                                src={`http://localhost:8000/static/monitor_live.jpg?t=${logs.length}`}
                                alt="Live Monitor"
                                className="w-full h-full object-contain rounded border border-gray-800"
                                onError={(e) => {
                                    (e.target as HTMLImageElement).src = 'https://placehold.co/600x400/111/444?text=Waiting+Signal...';
                                }}
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4">
                                <p className="text-xs font-mono text-white">
                                    Last Update: {lastUpdateTime}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* LOG STREAM */}
                    <div className="flex-1 glass-card overflow-hidden flex flex-col">
                        <div className="p-4 border-b border-white/5 bg-black/20 flex justify-between items-center">
                            <h3 className="text-sm font-bold text-gray-300 flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-cmd-purple animate-pulse"></span>
                                Terminal Stream
                            </h3>
                            <span className="text-[10px] font-mono text-gray-600 border border-gray-700 px-2 py-0.5 rounded">
                                {logs.length} events
                            </span>
                        </div>

                        <div
                            ref={logContainerRef}
                            className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar font-mono text-sm"
                        >
                            {loading ? (
                                <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-4">
                                    <Spinner size="lg" />
                                    <p className="animate-pulse">Synchronizing logs...</p>
                                </div>
                            ) : logs.length > 0 ? (
                                logs.map((log) => (
                                    <div
                                        key={log.id}
                                        className={`flex items-start gap-3 p-3 rounded-lg border border-transparent transition-all hover:bg-white/5 group animation-slide-in ${log.level === 'error' ? 'bg-red-500/5 hover:bg-red-500/10 border-red-500/10' : ''
                                            }`}
                                    >
                                        <div className="mt-0.5 shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                                            {getLevelIcon(log.level)}
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-0.5">
                                                <span className="text-[10px] text-gray-500 opacity-60">{log.timestamp}</span>
                                                <span className={`text-[10px] px-1.5 rounded uppercase tracking-wider font-bold ${log.level === 'success' ? 'bg-cmd-green/20 text-cmd-green' :
                                                    log.level === 'error' ? 'bg-cmd-red/20 text-cmd-red' :
                                                        log.level === 'warning' ? 'bg-cmd-yellow/20 text-cmd-yellow' :
                                                            'bg-cmd-blue/20 text-cmd-blue'
                                                    }`}>
                                                    {log.source || 'SYSTEM'}
                                                </span>
                                            </div>
                                            <p className="text-gray-300 leading-relaxed break-words opacity-90 group-hover:opacity-100">
                                                {log.message}
                                            </p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="h-full flex items-center justify-center">
                                    <EmptyState
                                        title="No signals detected"
                                        description="System operating normally. Waiting for events..."
                                        icon={<InformationCircleIcon className="w-12 h-12 text-gray-700" />}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
