import { useState, useEffect } from 'react';
import useWebSocket from '../hooks/useWebSocket';
import { BackendStatus } from '../types';
import {
    CommandLineIcon,
    CpuChipIcon,
    ClockIcon,
    CloudArrowUpIcon,
    ChatBubbleBottomCenterTextIcon,
    FilmIcon,
    PaperAirplaneIcon,
    PauseCircleIcon,
    PlayCircleIcon,
    XCircleIcon
} from '@heroicons/react/24/outline';
import BotCard, { BotProps } from './BotCard';

// MOCK DATA (Depois virá do BackendStatus)
// MOCK DATA REMOVED - Using BackendStatus.bots

interface BackendStatus {
    state: 'idle' | 'busy' | 'error' | 'paused' | 'unknown';
    last_updated: string;
    job: {
        name: string | null;
        progress: number;
        step: string;
        logs: string[];
    };
    system?: {
        cpu_percent: number;
        ram_percent: number;
        disk_usage: number;
    };
    bots?: BotProps[];
}

interface Props {
    scheduledVideos?: { schedule_time?: string }[];
}

export default function CommandCenter({ scheduledVideos = [] }: Props) {
    const [status, setStatus] = useState<BackendStatus | null>(null);
    const [expanded, setExpanded] = useState(false);

    // <--- INTEGRAÇÃO WEBSOCKET AQUI:
    useWebSocket({
        onPipelineUpdate: (data: unknown) => {
            // Atualiza o estado instantaneamente quando o backend avisa
            // console.log('⚡ WebSocket Update:', data);
            setStatus(data as BackendStatus);
        }
    });

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/v1/status');
                if (res.ok) {
                    setStatus(await res.json());
                }
            } catch {
                setStatus(prev => prev ? { ...prev, state: 'unknown' } : null);
            }
        };

        fetchStatus();
        // Polling removed in favor of WebSocket
        // const interval = setInterval(fetchStatus, 1000); 
        // return () => clearInterval(interval);
    }, []);

    // Fallback status when backend is offline
    const effectiveStatus = status || {
        state: 'unknown' as const,
        last_updated: '',
        job: { name: null, progress: 0, step: 'BACKEND OFFLINE', logs: [] },
        system: undefined
    };

    const isBusy = effectiveStatus.state === 'busy';
    const isError = effectiveStatus.state === 'error' || effectiveStatus.state === 'unknown';

    // Cyberpunk Colors
    const activeColor = isError ? '#f85149' : isBusy ? '#2ea043' : '#58a6ff';
    const glowShadow = `0 0 10px ${activeColor} 40`;

    // Calculate Quota (Max 10 days)
    const TIKTOK_LIMIT_DAYS = 10;
    const now = new Date();

    // Find furthest scheduled date
    const furthestDate = scheduledVideos.reduce((max, v) => {
        if (!v.schedule_time) return max;
        const d = new Date(v.schedule_time);
        return d > max ? d : max;
    }, now);

    const diffTime = Math.abs(furthestDate.getTime() - now.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const quotaPercent = Math.min((diffDays / TIKTOK_LIMIT_DAYS) * 100, 100);

    return (
        <div className="command-center fade-in" style={{
            marginBottom: '24px',
            backgroundColor: '#0d1117',
            border: `1px solid ${activeColor} `,
            borderRadius: '12px',
            boxShadow: glowShadow,
            overflow: 'hidden',
            transition: 'all 0.3s ease'
        }}>
            {/* Header Bar */}
            <div style={{
                padding: '12px 20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: expanded ? '1px solid #30363d' : 'none',
                background: `linear - gradient(90deg, ${activeColor}10 0 %, transparent 100 %)`
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                    {/* Status Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div className="pulse-ring" style={{ position: 'relative', width: 12, height: 12 }}>
                            <div style={{
                                width: 12, height: 12, borderRadius: '50%', backgroundColor: activeColor,
                                boxShadow: `0 0 8px ${activeColor} `
                            }} />
                        </div>
                        <div>
                            <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#fff', letterSpacing: '0.5px' }}>
                                CMD_CENTER <span style={{ opacity: 0.5 }}>{'//'}</span> {effectiveStatus.state.toUpperCase()}
                            </h3>
                            <p style={{ margin: 0, fontSize: '11px', color: activeColor, fontFamily: 'monospace' }}>
                                {effectiveStatus.job.step || 'SYSTEM READY'}
                            </p>
                        </div>
                    </div>

                    {/* NETWORK PULSE */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '12px', paddingLeft: '12px', borderLeft: '1px solid #30363d' }}>
                        <div style={{ width: '40px', height: '24px', position: 'relative', overflow: 'hidden' }}>
                            {/* Simulated EKG / Network Activity */}
                            <svg viewBox="0 0 40 24" style={{ width: '100%', height: '100%' }}>
                                <path
                                    d="M0 12 L5 12 L10 4 L15 20 L20 12 L25 12 L30 8 L35 16 L40 12"
                                    fill="none"
                                    stroke={activeColor}
                                    strokeWidth="1.5"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    style={{
                                        filter: `drop - shadow(0 0 2px ${activeColor})`,
                                        opacity: isBusy ? 1 : 0.5,
                                        animation: isBusy ? 'dash 1s linear infinite' : 'pulse 2s ease-in-out infinite'
                                    }}
                                />
                            </svg>
                        </div>
                        <div style={{ fontSize: '9px', fontFamily: 'monospace', color: '#8b949e', lineHeight: 1 }}>
                            <div>NET</div>
                            <div style={{ color: activeColor }}>{isBusy ? 'ACTIVE' : 'IDLE'}</div>
                        </div>
                    </div>

                    {/* Hardware Widgets (CPU/RAM) */}
                    {effectiveStatus.system && (
                        <div style={{ display: 'flex', gap: '16px', borderLeft: '1px solid #30363d', paddingLeft: '16px' }}>
                            <div title="Uso de CPU">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#8b949e', marginBottom: '2px' }}>
                                    <CpuChipIcon style={{ width: 12 }} /> CPU
                                </div>
                                <div style={{ fontSize: '12px', fontWeight: 'bold', color: effectiveStatus.system.cpu_percent > 80 ? '#f85149' : '#c9d1d9' }}>
                                    {effectiveStatus.system.cpu_percent.toFixed(1)}%
                                </div>
                            </div>
                            <div title="Uso de RAM">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#8b949e', marginBottom: '2px' }}>
                                    <CpuChipIcon style={{ width: 12 }} /> RAM
                                </div>
                                <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#c9d1d9' }}>
                                    {effectiveStatus.system.ram_percent.toFixed(1)}%
                                </div>
                            </div>
                            <div title="Janela de Agendamento TikTok (10 days)">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#8b949e', marginBottom: '2px' }}>
                                    <ClockIcon style={{ width: 12 }} /> QUOTA ({diffDays}d)
                                </div>
                                <div style={{ width: '60px', height: '4px', background: '#30363d', borderRadius: '2px', marginTop: '6px' }}>
                                    <div style={{ width: `${quotaPercent}% `, height: '100%', background: quotaPercent > 90 ? '#f85149' : '#a371f7' }} />
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <style jsx>{`
@keyframes dash {
    0 % { stroke- dasharray: 40; stroke - dashoffset: 40;
}
100 % { stroke- dasharray: 40; stroke - dashoffset: 0; }
                    }
@keyframes pulse {
    0 %, 100 % { opacity: 0.3; }
    50 % { opacity: 0.8; }
}
`}</style>

                {/* Breadcrumbs / Pipeline Stepper */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {[
                        { id: 'ingesting', label: 'INGEST', icon: CloudArrowUpIcon },
                        { id: 'transcribing', label: 'CAPTION', icon: ChatBubbleBottomCenterTextIcon },
                        { id: 'rendering', label: 'RENDER', icon: FilmIcon },
                        { id: 'uploading', label: 'PUBLISH', icon: PaperAirplaneIcon }
                    ].map((step, i, arr) => {
                        // Simple mapping logic: active step logic
                        // Ideally backend returns 'step' enum. For now we match string includes or mock.
                        // If status.state is idle, all inactive? Or all active if completed? 
                        // Let's assume status.job.step contains the keyword.

                        const isActive = effectiveStatus.job.step?.toLowerCase().includes(step.id);
                        // const isCompleted = false; // Need better tracking for completion history in this view

                        // Cyberpunk styling
                        // const stepColor = isActive ? activeColor : '#30363d';
                        const iconColor = isActive ? '#fff' : '#484f58';

                        return (
                            <div key={step.id} style={{ display: 'flex', alignItems: 'center' }}>
                                <div style={{
                                    display: 'flex', alignItems: 'center', gap: '6px',
                                    padding: '4px 8px', borderRadius: '4px',
                                    backgroundColor: isActive ? `${activeColor} 20` : 'transparent',
                                    border: `1px solid ${isActive ? `${activeColor}50` : 'transparent'} `
                                }}>
                                    <step.icon style={{ width: 14, height: 14, color: iconColor }} />
                                    <span style={{ fontSize: '10px', fontWeight: 600, color: iconColor }}>{step.label}</span>
                                </div>
                                {i < arr.length - 1 && (
                                    <div style={{ width: '12px', height: '1px', backgroundColor: '#30363d', margin: '0 4px' }} />
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Right Side: Progress + Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                    {isBusy && (
                        <div style={{ width: '200px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span style={{ fontSize: '10px', color: '#8b949e' }}>PROGRESS</span>
                                <span style={{ fontSize: '10px', color: activeColor }}>{effectiveStatus.job.progress}%</span>
                            </div>
                            <div style={{ height: '4px', background: '#30363d', borderRadius: '2px', overflow: 'hidden' }}>
                                <div style={{
                                    width: `${effectiveStatus.job.progress}% `,
                                    height: '100%',
                                    background: activeColor,
                                    transition: 'width 0.5s ease'
                                }} />
                            </div>
                        </div>
                    )}

                    {/* Worker Controls */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderLeft: '1px solid #30363d', paddingLeft: '16px' }}>
                        <button
                            title="Pause Queue"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#8b949e', transition: 'color 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.color = '#e3b341'}
                            onMouseLeave={e => e.currentTarget.style.color = '#8b949e'}
                        >
                            <PauseCircleIcon style={{ width: 18 }} />
                        </button>
                        <button
                            title="Resume Queue"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#8b949e', transition: 'color 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.color = '#3fb950'}
                            onMouseLeave={e => e.currentTarget.style.color = '#8b949e'}
                        >
                            <PlayCircleIcon style={{ width: 18 }} />
                        </button>
                        <button
                            title="EMERGENCY STOP"
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#f85149', opacity: 0.7, transition: 'opacity 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                            onMouseLeave={e => e.currentTarget.style.opacity = '0.7'}
                        >
                            <XCircleIcon style={{ width: 18 }} />
                        </button>
                    </div>

                    <button
                        onClick={() => setExpanded(!expanded)}
                        style={{
                            background: 'none', border: 'none', color: '#8b949e', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px'
                        }}
                    >
                        <CommandLineIcon style={{ width: 16 }} />
                        {expanded ? 'HIDE_LOGS' : 'SHOW_LOGS'}
                    </button>
                </div>
            </div>

            {/* BOTS GRID (Novo) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border-b border-cmd-border/50 bg-[#0d1117]/50">
                {(effectiveStatus.bots || []).map(bot => (
                    <BotCard key={bot.id} {...bot} />
                ))}
            </div>

            {/* Expanded Logs (Terminal View) */}
            {expanded && (
                <div style={{
                    padding: '16px',
                    backgroundColor: '#010409',
                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                    fontSize: '12px',
                    color: '#8b949e',
                    borderTop: '1px solid #30363d',
                    maxHeight: '200px',
                    overflowY: 'auto'
                }}>
                    {effectiveStatus.job.logs.length > 0 ? (
                        effectiveStatus.job.logs.map((log, i) => (
                            <div key={i} style={{ marginBottom: '4px', display: 'flex', gap: '8px' }}>
                                <span style={{ color: '#30363d' }}>{'>'}</span>
                                <span style={{ color: i === 0 ? '#fff' : 'inherit' }}>{log}</span>
                            </div>
                        ))
                    ) : (
                        <div style={{ opacity: 0.5 }}>Waiting for system output...</div>
                    )}
                </div>
            )}
        </div>
    );
}
