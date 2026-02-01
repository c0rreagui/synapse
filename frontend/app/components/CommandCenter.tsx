'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useMood } from '../context/MoodContext';
import { getApiUrl } from '../utils/apiClient';
import useWebSocket from '../hooks/useWebSocket';
import { BackendStatus, LogEntry, ScheduleEvent } from '../types';
import { StitchCard } from './StitchCard';
import { NeoButton } from '../../components/design-system/NeoButton';
import BotCard from './BotCard';
import {
    Cpu,
    Clock,
    CirclePause,
    CirclePlay,
    CircleX,
    Terminal,
    CloudUpload,
    MessageSquareText,
    Film,
    Send,
    Activity,
    Server,
    HardDrive
} from 'lucide-react';

interface Props {
    scheduledVideos?: ScheduleEvent[];
}

export default function CommandCenter({ scheduledVideos = [] }: Props) {
    const [status, setStatus] = useState<BackendStatus | null>(null);
    const [expanded, setExpanded] = useState(false);
    const { setMood } = useMood();

    useWebSocket({
        onPipelineUpdate: (data: unknown) => {
            const newStatus = data as BackendStatus;
            setStatus(newStatus);

            if (newStatus.state === 'error') setMood('ERROR');
            else if (newStatus.state === 'busy') setMood('PROCESSING');
            else if (newStatus.job.step === 'completed') setMood('SUCCESS');
            else setMood('IDLE');
        },
        onLogEntry: (data: LogEntry) => {
            if (data.level === 'error') {
                toast.error(data.message);
            } else if (data.level === 'success') {
                toast.success(data.message);
            }
        }
    });

    useEffect(() => {
        const fetchStatus = async () => {
            const API_URL = getApiUrl();
            try {
                const res = await fetch(`${API_URL}/api/v1/status`);
                if (res.ok) {
                    setStatus(await res.json());
                }
            } catch {
                setStatus(prev => prev ? { ...prev, state: 'unknown' } : null);
            }
        };

        fetchStatus();
    }, []);

    const effectiveStatus = status || {
        state: 'unknown' as const,
        last_updated: '',
        job: { name: null, progress: 0, step: 'BACKEND OFFLINE', logs: [] },
        system: undefined
    };

    const isBusy = effectiveStatus.state === 'busy';
    const isError = effectiveStatus.state === 'error' || effectiveStatus.state === 'unknown';

    const TIKTOK_LIMIT_DAYS = 10;
    const now = new Date();

    const furthestDate = scheduledVideos.reduce((max: Date, v: ScheduleEvent) => {
        if (!v.scheduled_time) return max;
        const d = new Date(v.scheduled_time);
        return d > max ? d : max;
    }, now);

    const diffTime = Math.abs(furthestDate.getTime() - now.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const quotaPercent = Math.min((diffDays / TIKTOK_LIMIT_DAYS) * 100, 100);

    return (
        <StitchCard className={`mb-8 p-0 border border-white/5 transition-all duration-500 bg-black/40 backdrop-blur-2xl rounded-3xl overflow-hidden ${isBusy ? 'shadow-[0_0_50px_rgba(16,185,129,0.1)]' : ''}`}>

            {/* Header Bar */}
            <div className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between border-b border-white/5 bg-white/[0.02] gap-4">
                <div className="flex items-center gap-6">
                    {/* Status Badge */}
                    <div className="flex items-center gap-3">
                        <div className="relative w-3 h-3">
                            <div className={`absolute inset-0 rounded-full animate-ping opacity-75 ${isError ? 'bg-red-500' : isBusy ? 'bg-emerald-500' : 'bg-cyan-500'}`}></div>
                            <div className={`relative w-3 h-3 rounded-full ${isError ? 'bg-red-500' : isBusy ? 'bg-emerald-500' : 'bg-cyan-500'}`}></div>
                        </div>
                        <div>
                            <h3 className="m-0 text-sm font-semibold text-white tracking-widest flex items-center gap-2 font-mono">
                                CMD_CENTER <span className="text-white/20">{'//'}</span> <span className={isError ? 'text-red-400' : isBusy ? 'text-emerald-400' : 'text-cyan-400'}>{effectiveStatus.state.toUpperCase()}</span>
                            </h3>
                            <p className={`m-0 text-[10px] font-mono mt-0.5 uppercase tracking-wider opacity-60 ${isError ? 'text-red-300' : 'text-gray-400'}`}>
                                {effectiveStatus.job.step || 'SYSTEM READY'}
                            </p>
                        </div>
                    </div>

                    {/* NETWORK PULSE */}
                    <div className="hidden md:flex items-center gap-3 ml-4 pl-4 border-l border-white/5 h-8">
                        <div className="flex gap-0.5 items-end h-4">
                            {[1, 2, 3, 4].map((i) => (
                                <div
                                    key={i}
                                    className={`w-1 rounded-full transition-all duration-300 ${isBusy
                                        ? `bg-emerald-500 animate-pulse`
                                        : 'bg-white/10 h-2'}`}
                                    style={{
                                        height: isBusy ? `${Math.random() * 100}%` : undefined,
                                        animationDelay: `${i * 75}ms`
                                    }}
                                ></div>
                            ))}
                        </div>
                        <div className="text-[9px] font-mono text-gray-500 leading-3">
                            <div>NET</div>
                            <div className={isBusy ? 'text-emerald-500' : 'text-gray-600'}>{isBusy ? 'ACTIVE' : 'IDLE'}</div>
                        </div>
                    </div>

                    {/* Hardware Widgets */}
                    {effectiveStatus.system && (
                        <div className="hidden lg:flex gap-6 border-l border-white/5 pl-6">
                            <div title="System Load" className="group">
                                <div className="flex items-center gap-1.5 text-[10px] text-gray-500 mb-0.5 uppercase tracking-wider group-hover:text-gray-300 transition-colors">
                                    <Cpu className="w-3 h-3" /> CPU
                                </div>
                                <div className={`text-xs font-mono font-bold ${effectiveStatus.system.cpu_percent > 80 ? 'text-red-400' : 'text-white/80'}`}>
                                    {effectiveStatus.system.cpu_percent.toFixed(1)}%
                                </div>
                            </div>

                            <div title="RAM Usage" className="group">
                                <div className="flex items-center gap-1.5 text-[10px] text-gray-500 mb-0.5 uppercase tracking-wider group-hover:text-gray-300 transition-colors">
                                    <HardDrive className="w-3 h-3" /> RAM
                                </div>
                                <div className={`text-xs font-mono font-bold text-white/80`}>
                                    {effectiveStatus.system.ram_percent.toFixed(1)}%
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Side Controls */}
                <div className="flex items-center gap-4">
                    {/* Worker Controls */}
                    <div className="flex items-center gap-2">
                        <NeoButton variant="ghost" size="icon" className="rounded-full text-gray-400 hover:text-white" title="Pause">
                            <CirclePause className="w-5 h-5" />
                        </NeoButton>
                        <NeoButton variant="ghost" size="icon" className="rounded-full text-emerald-500 hover:text-emerald-400" title="Resume">
                            <CirclePlay className="w-5 h-5" />
                        </NeoButton>
                        <NeoButton variant="danger" size="icon" className="rounded-full" title="STOP">
                            <CircleX className="w-5 h-5" />
                        </NeoButton>
                    </div>

                    <div className="h-6 w-px bg-white/10 hidden md:block"></div>

                    <button
                        onClick={() => setExpanded(!expanded)}
                        className={`transition-all duration-300 flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-lg border ${expanded ? 'bg-white/10 border-white/20 text-white' : 'bg-transparent border-transparent text-gray-500 hover:bg-white/5 hover:text-gray-300'}`}
                    >
                        <Terminal className="w-3.5 h-3.5" />
                        {expanded ? 'HIDE_LOGS' : 'TERMINAL'}
                    </button>
                </div>
            </div>

            {/* Breadcrumbs / Pipeline Stepper */}
            <div className="px-6 py-3 border-b border-white/5 flex overflow-x-auto gap-1 scrollbar-hide bg-black/20">
                {[
                    { id: 'ingesting', label: 'INGEST', icon: CloudUpload },
                    { id: 'transcribing', label: 'CAPTION', icon: MessageSquareText },
                    { id: 'rendering', label: 'RENDER', icon: Film },
                    { id: 'uploading', label: 'PUBLISH', icon: Send }
                ].map((step, i, arr) => {
                    const isActive = effectiveStatus.job.step?.toLowerCase().includes(step.id);
                    const iconColor = isActive ? 'text-white' : 'text-gray-600';
                    const activeClasses = isActive
                        ? 'bg-gradient-to-r from-purple-500/20 to-blue-500/20 border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.1)]'
                        : 'border-transparent opacity-60';

                    return (
                        <div key={step.id} className="flex items-center shrink-0">
                            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${activeClasses} transition-all duration-300`}>
                                <step.icon className={`w-3.5 h-3.5 ${iconColor}`} />
                                <span className={`text-[10px] font-bold tracking-wider ${isActive ? 'text-white' : 'text-gray-600'}`}>{step.label}</span>
                            </div>
                            {i < arr.length - 1 && (
                                <div className="w-4 h-px bg-white/5 mx-2" />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* BOTS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6 border-b border-white/5 bg-gradient-to-b from-transparent to-black/20">
                {(effectiveStatus.bots || []).map(bot => (
                    <BotCard key={bot.id} {...bot} />
                ))}
            </div>

            {/* Expanded Logs */}
            {expanded && (
                <div className="p-4 bg-[#0a0a0a] font-mono text-xs text-gray-300 border-t border-white/10 max-h-[300px] overflow-y-auto custom-scrollbar shadow-inner">
                    {effectiveStatus.job.logs.length > 0 ? (
                        effectiveStatus.job.logs.map((log, i) => (
                            <div key={i} className="mb-2 flex gap-3 opacity-0 animate-in fade-in slide-in-from-bottom-1 duration-300 fill-mode-forwards" style={{ animationDelay: `${i * 50}ms` }}>
                                <span className="text-white/20 text-[10px] select-none shrink-0 w-16">
                                    {new Date(effectiveStatus.last_updated || Date.now()).toLocaleTimeString()}
                                </span>
                                <span className="text-purple-500/50 select-none">➜</span>
                                <span className={`${i === 0 ? 'text-white font-bold' : 'opacity-70'}`}>{log}</span>
                            </div>
                        ))
                    ) : (
                        <div className="opacity-30 italic p-4 text-center">Waiting for system output...</div>
                    )}
                </div>
            )}
            {/* SCHEDULED EVENTS */}
            {scheduledVideos.length > 0 && (
                <div className="p-6 border-t border-white/5 bg-black/40 backdrop-blur-md">
                    <h4 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 text-purple-400" /> Upcoming Transmissions
                    </h4>
                    <div className="space-y-2">
                        {scheduledVideos.slice(0, 5).map(evt => (
                            <div key={evt.id} className="flex items-center justify-between text-xs p-3 rounded-xl bg-white/5 border border-white/5 hover:border-purple-500/30 hover:bg-purple-500/5 transition-all duration-300 group cursor-default">
                                <div className="flex items-center gap-3">
                                    <div className="relative">
                                        <div className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"></div>
                                    </div>
                                    <span className="text-gray-300 font-medium truncate max-w-[200px] group-hover:text-white transition-colors">
                                        {evt.video_path.split(/[\\/]/).pop()}
                                    </span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono text-[10px]">
                                        {evt.profile_id}
                                    </span>
                                    <div className="font-mono text-gray-500 text-[10px]">
                                        {new Date(evt.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </StitchCard>
    );
}
