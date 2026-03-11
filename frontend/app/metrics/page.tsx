'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getApiUrl } from '../utils/apiClient';
import { apiClient } from '../lib/api';
interface LogEntry {
    level: string;
    message: string;
    module?: string;
    timestamp?: string;
    text?: string;
}

interface Vitals {
    cpu_percent: number;
    mem_used_gb: number;
    mem_total_gb: number;
    mem_percent: number;
    uptime: string;
}

export default function MetricsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [vitals, setVitals] = useState<Vitals | null>(null);
    const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
    const [filterErrors, setFilterErrors] = useState(false);
    const [filterWarnings, setFilterWarnings] = useState(true);
    const [showAll, setShowAll] = useState(true);
    const [paused, setPaused] = useState(false);
    const terminalRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const API = getApiUrl();

    // Fetch vitals every 3 seconds
    useEffect(() => {
        const fetchVitals = async () => {
            try {
                const data = await apiClient.get<Vitals>('/api/v1/telemetry/vitals');
                setVitals(data);
            } catch {
                // silently fail
            }
        };
        fetchVitals();
        const interval = setInterval(fetchVitals, 3000);
        return () => clearInterval(interval);
    }, [API]);

    // WebSocket connection for log stream
    useEffect(() => {
        const wsUrl = `${API.replace('http', 'ws')}/api/v1/telemetry/stream`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => setWsStatus('connected');
        ws.onclose = () => setWsStatus('disconnected');
        ws.onerror = () => setWsStatus('disconnected');

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === 'log_entry' && msg.data) {
                    const entry: LogEntry = {
                        level: msg.data.level || msg.data.record?.level?.name || 'INFO',
                        message: msg.data.message || msg.data.text || msg.data.record?.message || JSON.stringify(msg.data),
                        module: msg.data.module || msg.data.record?.name || 'System',
                        timestamp: msg.data.timestamp || msg.data.record?.time?.repr || new Date().toISOString(),
                    };
                    if (!paused) {
                        setLogs(prev => [...prev.slice(-200), entry]);
                    }
                }
            } catch {
                // ignore parse errors
            }
        };

        // Keepalive ping
        const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 15000);

        return () => {
            clearInterval(pingInterval);
            ws.close();
        };
    }, [API, paused]);

    // Auto-scroll terminal
    useEffect(() => {
        if (terminalRef.current && !paused) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [logs, paused]);

    const clearLogs = useCallback(() => setLogs([]), []);

    const getLevelColor = (level: string) => {
        const l = level.toUpperCase();
        if (l.includes('ERR') || l.includes('CRITICAL') || l.includes('FATAL')) return 'text-magenta-500';
        if (l.includes('WARN')) return 'text-yellow-500';
        if (l.includes('OK') || l.includes('SUCCESS')) return 'text-green-500';
        return 'text-cyan-400';
    };

    const getLevelTag = (level: string) => {
        const l = level.toUpperCase();
        if (l.includes('ERR') || l.includes('CRITICAL')) return '[ERR]';
        if (l.includes('WARN')) return '[WARN]';
        if (l.includes('OK') || l.includes('SUCCESS')) return '[OK]';
        if (l.includes('DEBUG')) return '[DBG]';
        return '[INFO]';
    };

    const getLineStyle = (level: string) => {
        const l = level.toUpperCase();
        if (l.includes('ERR') || l.includes('CRITICAL')) return 'bg-magenta-500/5 hover:bg-magenta-500/10 border border-magenta-500/40 shadow-[0_0_20px_-5px_rgba(255,0,255,0.4)] relative overflow-hidden';
        if (l.includes('WARN')) return 'hover:bg-yellow-500/5 border-l-2 border-transparent hover:border-yellow-500/50';
        if (l.includes('OK') || l.includes('SUCCESS')) return 'hover:bg-green-500/5 border-l-2 border-transparent hover:border-green-500/50';
        return 'hover:bg-white/5 border-l-2 border-transparent hover:border-cyan-400/50';
    };

    const formatTimestamp = (ts?: string) => {
        if (!ts) return new Date().toLocaleString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
        try {
            // Try to parse. If it says 'Invalid Date', fallback to string directly
            const d = new Date(ts);
            if (isNaN(d.getTime())) return ts; // Return original string safely
            return d.toLocaleString('pt-BR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch {
            return String(ts).slice(0, 23);
        }
    };

    const filteredLogs = logs.filter(log => {
        const l = log.level.toUpperCase();

        // If "Apenas Erros" is checked, ONLY show errors
        if (filterErrors && !(l.includes('ERR') || l.includes('CRITICAL'))) return false;

        // If "Avisos" is disabled, hide warnings
        if (!filterWarnings && l.includes('WARN')) return false;

        // If "Todos os Sistemas" is disabled, and it's info/debug, hide it
        if (!showAll && !(l.includes('ERR') || l.includes('CRITICAL') || l.includes('WARN'))) return false;

        return true;
    });

    return (
        <div className="relative flex h-full w-full flex-col bg-black overflow-hidden group/design-root schematic-bg animate-drift" style={{ backgroundSize: '100px 100px' }}>
            <div className="absolute inset-0 pointer-events-none z-50 bg-scanline bg-[length:100%_4px] opacity-15 animate-scan mix-blend-overlay"></div>
            <div className="absolute inset-0 pointer-events-none z-40 crt-overlay opacity-40"></div>
            <div className="absolute inset-0 pointer-events-none z-0 opacity-10 flex items-center justify-center">
                <svg className="w-full h-full stroke-cyan-400 fill-none stroke-[0.5]" style={{ WebkitMaskImage: 'radial-gradient(circle, black 40%, transparent 70%)' }} viewBox="0 0 800 600">
                    <circle cx="400" cy="300" r="250" strokeDasharray="4 4"></circle>
                    <circle cx="400" cy="300" r="150" strokeDasharray="10 5"></circle>
                    <line x1="150" x2="650" y1="300" y2="300"></line>
                    <line x1="400" x2="400" y1="50" y2="550"></line>
                    <rect height="200" strokeWidth="1" width="400" x="200" y="200"></rect>
                </svg>
            </div>

            <main className="flex flex-1 overflow-hidden relative z-20 w-full max-w-[1600px] mx-auto">
                <aside className="hidden lg:flex w-80 flex-col border-r border-white/10 bg-[#020202] p-6 gap-8 shrink-0 relative shadow-[15px_0_30px_-5px_rgba(0,0,0,0.9)] z-30">
                    <div className="absolute top-2 left-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>
                    <div className="absolute top-2 right-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>
                    <div className="absolute bottom-2 left-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>
                    <div className="absolute bottom-2 right-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>

                    <div className="flex flex-col gap-5 mt-6">
                        <p className="text-slate-500 font-display text-sm uppercase tracking-[0.2em] border-b border-white/5 pb-2 text-right">Matriz de Filtro</p>
                        <div className="flex items-center justify-between group py-1">
                            <span className="text-xs text-slate-400 font-mono tracking-widest group-hover:text-cyan-400 transition-colors">TODOS OS SISTEMAS</span>
                            <div className="relative inline-block w-10 align-middle select-none transition duration-200 ease-in">
                                <input className="toggle-checkbox absolute block w-4 h-4 bg-black border border-slate-600 appearance-none cursor-pointer rounded-none transition-all duration-200 ease-in-out checked:bg-cyan-400 checked:translate-x-full" id="toggle1" name="toggle" type="checkbox" checked={showAll} onChange={() => { setShowAll(!showAll); setFilterErrors(false); }} />
                                <label className="toggle-label block overflow-hidden h-4 bg-slate-900 cursor-pointer border border-slate-800" htmlFor="toggle1"><span className="sr-only">Todos os Sistemas</span></label>
                            </div>
                        </div>
                        <div className="flex items-center justify-between group py-1">
                            <span className="text-xs text-slate-400 font-mono tracking-widest group-hover:text-magenta-500 transition-colors shadow-magenta-500/50">APENAS ERROS</span>
                            <div className="relative inline-block w-10 align-middle select-none transition duration-200 ease-in">
                                <input className="toggle-checkbox absolute block w-4 h-4 bg-black border border-slate-600 appearance-none cursor-pointer rounded-none transition-all duration-200 ease-in-out checked:translate-x-full checked:bg-magenta-500" id="toggle2" name="toggle" type="checkbox" checked={filterErrors} onChange={() => { setFilterErrors(!filterErrors); if (!filterErrors) setShowAll(false); }} />
                                <label className="toggle-label block overflow-hidden h-4 bg-slate-900 cursor-pointer border border-slate-800" htmlFor="toggle2"><span className="sr-only">Apenas Erros</span></label>
                            </div>
                        </div>
                        <div className="flex items-center justify-between group py-1">
                            <span className="text-xs text-slate-400 font-mono tracking-widest group-hover:text-yellow-400 transition-colors">AVISOS</span>
                            <div className="relative inline-block w-10 align-middle select-none transition duration-200 ease-in">
                                <input className="toggle-checkbox absolute block w-4 h-4 bg-black border border-slate-600 appearance-none cursor-pointer rounded-none transition-all duration-200 ease-in-out checked:translate-x-full checked:bg-yellow-400" id="toggle3" name="toggle" type="checkbox" checked={filterWarnings} onChange={() => setFilterWarnings(!filterWarnings)} />
                                <label className="toggle-label block overflow-hidden h-4 bg-slate-900 cursor-pointer border border-slate-800" htmlFor="toggle3"><span className="sr-only">Avisos</span></label>
                            </div>
                        </div>
                    </div>

                    <div className="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-2"></div>

                    <div className="flex flex-col gap-3">
                        <p className="text-slate-500 font-display text-xs uppercase tracking-[0.2em] mb-2 text-right">Modos de Operação</p>
                        <button
                            onClick={() => setPaused(false)}
                            className={`w-full border ${!paused ? 'border-cyan-400/40 text-cyan-400 bg-cyan-400/5' : 'border-slate-800 text-slate-500'} hover:bg-cyan-400/10 py-2.5 px-4 text-[10px] font-mono uppercase tracking-[0.15em] transition-all flex items-center justify-between shadow-[0_0_10px_rgba(0,240,255,0.05)] group`}
                        >
                            <span className="group-hover:translate-x-1 transition-transform">Log ao Vivo</span>
                            <span className={`material-symbols-outlined text-[14px] ${!paused ? 'animate-spin' : ''} group-hover:text-white transition-colors`}>sync</span>
                        </button>
                        <button
                            onClick={() => setPaused(true)}
                            className={`w-full border ${paused ? 'border-yellow-400/40 text-yellow-400 bg-yellow-400/5' : 'border-slate-800 text-slate-500'} hover:text-white hover:border-white/20 bg-transparent py-2.5 px-4 text-[10px] font-mono uppercase tracking-[0.15em] transition-all flex items-center justify-between group`}
                        >
                            <span className="group-hover:translate-x-1 transition-transform">Modo Pausa</span>
                            <span className="material-symbols-outlined text-[14px] group-hover:text-white transition-colors">pause</span>
                        </button>
                    </div>

                    <div className="mt-auto bg-[#030303] border border-white/10 p-4 relative overflow-hidden group">
                        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(0,240,255,0.03)_50%,transparent_75%,transparent_100%)] bg-[length:250%_250%,100%_100%] bg-[position:-100%_0,0_0] bg-no-repeat transition-[background-position_0s_ease] hover:bg-[position:200%_0,0_0] duration-1000"></div>
                        <div className="flex items-center justify-between mb-3 relative z-10">
                            <span className="text-[10px] text-cyan-400 font-display tracking-widest">BUFFER_LOG</span>
                            <span className="text-[10px] text-cyan-400 font-mono">{Math.min(100, Math.round(logs.length / 2))}%</span>
                        </div>
                        <div className="flex gap-0.5 h-1.5 w-full">
                            {Array.from({ length: 8 }).map((_, i) => (
                                <div key={i} className={`flex-1 ${i < Math.ceil(Math.min(logs.length, 200) / 25) ? 'bg-cyan-400 shadow-[0_0_5px_#00f0ff]' : 'bg-cyan-400/20'}`}></div>
                            ))}
                        </div>
                        <div className="mt-2 text-[8px] text-slate-600 font-mono text-right">{logs.length} entradas</div>
                    </div>
                </aside>

                <div className="flex-1 flex flex-col bg-transparent relative overflow-hidden hud-perspective">
                    <div className="flex items-center justify-between px-6 py-2 pb-4 pt-6 border-b border-white/10 bg-black/80 backdrop-blur z-10 shrink-0">
                        <div className="flex items-center gap-4">
                            <h1 className="text-4xl font-display tracking-[0.2em] text-white uppercase drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">Fluxo de Telemetria</h1>
                            <span className={`px-2 py-0.5 ${wsStatus === 'connected' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-magenta-500/10 border-magenta-500/30 text-magenta-500'} border text-[9px] font-mono tracking-wider ${wsStatus === 'connected' ? 'animate-pulse' : ''}`}>
                                {wsStatus === 'connected' ? 'CANAL ATIVO // STREAM' : wsStatus === 'connecting' ? 'CONECTANDO...' : 'DESCONECTADO'}
                            </span>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={clearLogs} className="p-1.5 text-magenta-500 hover:bg-magenta-500/10 border border-transparent hover:border-magenta-500/30 transition-colors" title="Clear Console">
                                <span className="material-symbols-outlined text-[18px]">delete_sweep</span>
                            </button>
                            <button onClick={() => setPaused(!paused)} className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 border border-transparent hover:border-white/30 transition-colors" title={paused ? 'Resume' : 'Pause'}>
                                <span className="material-symbols-outlined text-[18px]">{paused ? 'play_arrow' : 'pause'}</span>
                            </button>
                        </div>
                    </div>

                    <div ref={terminalRef} className="flex-1 overflow-y-auto overflow-x-hidden p-8 font-mono text-sm leading-relaxed relative" id="terminal-content">
                        <div className="w-full max-w-7xl mx-auto min-h-[800px] h-full backdrop-blur-sm relative p-10 pb-20">
                            <div className="absolute top-0 left-0 w-16 h-16 border-t border-l border-cyan-400/60"></div>
                            <div className="absolute top-0 right-0 w-16 h-16 border-t border-r border-cyan-400/60"></div>
                            <div className="absolute bottom-0 left-0 w-16 h-16 border-b border-l border-cyan-400/60"></div>
                            <div className="absolute bottom-0 right-0 w-16 h-16 border-b border-r border-cyan-400/60"></div>

                            <div className="absolute top-2 left-2 text-[9px] text-cyan-400/40 font-mono">COORD: 45.21, 12.90</div>
                            <div className="absolute bottom-2 right-2 text-[9px] text-cyan-400/40 font-mono">HUD_VER: 4.2</div>

                            <div className="flex flex-col gap-0.5 w-full relative z-10">
                                {filteredLogs.length === 0 && (
                                    <div className="log-line flex gap-4 p-2 px-4 mt-6 transition-colors group items-center border border-cyan-400/40 bg-cyan-400/5 shadow-[0_0_20px_-5px_rgba(0,240,255,0.4)]">
                                        <span className="text-cyan-400/70 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider">{new Date().toLocaleString('pt-BR')}</span>
                                        <span className="text-cyan-400 font-bold w-12 shrink-0 tracking-wider text-xs">[INFO]</span>
                                        <span className="text-cyan-400/70 w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest">System</span>
                                        <span className="text-white font-bold text-scan-effect uppercase tracking-widest text-xs">
                                            {wsStatus === 'connected' ? 'Fluxo de log ao vivo ativo...' : 'Aguardando conexão WebSocket...'}
                                            <span className="animate-ping text-cyan-400">_</span>
                                        </span>
                                    </div>
                                )}
                                {filteredLogs.map((log, idx) => (
                                    <div key={idx} className={`log-line flex gap-4 p-1 px-4 transition-colors group items-center ${getLineStyle(log.level)}`}>
                                        {log.level.toUpperCase().includes('ERR') && (
                                            <>
                                                <div className="absolute inset-0 bg-magenta-500/5 animate-pulse"></div>
                                                <div className="absolute top-0 bottom-0 left-0 w-1 bg-magenta-500 animate-pulse"></div>
                                            </>
                                        )}
                                        <span className={`${log.level.toUpperCase().includes('ERR') ? 'text-magenta-500/60' : 'text-slate-600'} font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider opacity-70 relative z-10`}>
                                            {formatTimestamp(log.timestamp)}
                                        </span>
                                        <span className={`${getLevelColor(log.level)} font-bold w-12 shrink-0 tracking-wider text-xs relative z-10`}>
                                            {getLevelTag(log.level)}
                                        </span>
                                        <span className={`${log.level.toUpperCase().includes('ERR') ? 'text-magenta-500/80' : 'text-slate-500'} w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest relative z-10`}>
                                            {(log.module || 'System').slice(0, 12)}
                                        </span>
                                        <span className={`${log.level.toUpperCase().includes('ERR') ? 'text-white font-bold' : 'text-slate-300 group-hover:text-cyan-400'} transition-colors font-light text-xs relative z-10`}>
                                            {log.message}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="shrink-0 bg-black/90 backdrop-blur border-t border-white/10 px-6 py-3 flex items-center justify-between text-xs font-mono z-30">
                        <div className="flex items-center gap-8">
                            <span className="flex items-center gap-2 text-cyan-400 drop-shadow-[0_0_5px_rgba(0,240,255,0.5)] truncate max-w-[400px]">
                                <span className={`shrink-0 size-2 rounded-full ${wsStatus === 'connected' ? 'bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(0,240,255,0.8)]' : 'bg-red-500'}`}></span>
                                <span className="tracking-widest text-[10px] uppercase truncate">
                                    Stream: {API.replace('http', 'ws')}/api/v1/telemetry/stream
                                </span>
                            </span>
                            <span className="text-slate-500 text-[10px] uppercase tracking-wider shrink-0">
                                LOGS: <span className="text-white font-bold">{filteredLogs.length}</span>
                            </span>
                        </div>
                        <div className="flex items-center gap-8 text-slate-500 text-[10px] uppercase tracking-wider">
                            <span>
                                MEM: <span className="text-white">{vitals ? `${vitals.mem_used_gb} GB` : '-- GB'}</span>
                                <span className="text-slate-700 mx-1">/</span>
                                {vitals ? `${vitals.mem_total_gb} GB` : '-- GB'}
                            </span>
                            <span>
                                CPU: <span className="text-white">{vitals ? `${vitals.cpu_percent}%` : '--%'}</span>
                            </span>
                            <span className="text-magenta-500 drop-shadow-[0_0_5px_rgba(255,0,255,0.5)]">
                                UPTIME: {vitals ? vitals.uptime : '--d --h --m'}
                            </span>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
