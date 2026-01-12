'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { useMood } from '../context/MoodContext';
import useWebSocket from '../hooks/useWebSocket';
import { BackendStatus, LogEntry, ScheduleEvent } from '../types';
import { StitchCard } from './StitchCard';
import { NeonButton } from './NeonButton';
import BotCard from './BotCard';
import {
    CpuChipIcon,
    ClockIcon,
    PauseCircleIcon,
    PlayCircleIcon,
    XCircleIcon,
    CommandLineIcon,
    CloudArrowUpIcon,
    ChatBubbleBottomCenterTextIcon,
    FilmIcon,
    PaperAirplaneIcon
} from '@heroicons/react/24/outline';

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
        <StitchCard className={`mb-6 p-0 border transition-all duration-300 bg-[#0d1117] ${isBusy ? 'shadow-[0_0_30px_rgba(16,185,129,0.15)] scanline-active' : ''}`}>

            {/* Header Bar */}
            <div className="px-5 py-3 flex flex-col md:flex-row md:items-center justify-between border-b border-white/5 bg-gradient-to-r from-white/5 to-transparent gap-4">
                <div className="flex items-center gap-6">
                    {/* Status Badge */}
                    <div className="flex items-center gap-3">
                        <div className="relative w-3 h-3">
                            <div className={`absolute inset-0 rounded-full animate-ping opacity-75 ${isError ? 'bg-red-500' : isBusy ? 'bg-synapse-emerald' : 'bg-synapse-cyan'}`}></div>
                            <div className={`relative w-3 h-3 rounded-full ${isError ? 'bg-red-500' : isBusy ? 'bg-synapse-emerald' : 'bg-synapse-cyan'}`}></div>
                        </div>
                        <div>
                            <h3 className="m-0 text-sm font-semibold text-white tracking-widest flex items-center gap-2">
                                CMD_CENTER <span className="text-gray-600">{'//'}</span> <span className={isError ? 'text-red-500' : isBusy ? 'text-synapse-emerald' : 'text-synapse-cyan'}>{effectiveStatus.state.toUpperCase()}</span>
                            </h3>
                            <p className={`m-0 text-[10px] font-mono mt-0.5 ${isError ? 'text-red-400' : 'text-gray-400'}`}>
                                {effectiveStatus.job.step || 'SYSTEM READY'}
                            </p>
                        </div>
                    </div>

                    {/* NETWORK PULSE */}
                    <div className="hidden md:flex items-center gap-2 ml-3 pl-3 border-l border-white/10 h-8">
                        {/* Simple CSS-based Signal Viz for performance instead of SVG */}
                        <div className="flex gap-0.5 items-end h-4">
                            <div className={`w-1 bg-current transition-all duration-300 ${isBusy ? 'h-full animate-pulse text-synapse-emerald' : 'h-2 text-gray-700'}`}></div>
                            <div className={`w-1 bg-current transition-all duration-300 ${isBusy ? 'h-3 animate-pulse delay-75 text-synapse-emerald' : 'h-1 text-gray-700'}`}></div>
                            <div className={`w-1 bg-current transition-all duration-300 ${isBusy ? 'h-full animate-pulse delay-150 text-synapse-emerald' : 'h-2 text-gray-700'}`}></div>
                            <div className={`w-1 bg-current transition-all duration-300 ${isBusy ? 'h-2 animate-pulse delay-100 text-synapse-emerald' : 'h-1 text-gray-700'}`}></div>
                        </div>
                        <div className="text-[9px] font-mono text-gray-500 leading-3">
                            <div>NET</div>
                            <div className={isBusy ? 'text-synapse-emerald' : 'text-gray-700'}>{isBusy ? 'TX/RX' : 'IDLE'}</div>
                        </div>
                    </div>

                    {/* Hardware Widgets */}
                    {effectiveStatus.system && (
                        <div className="hidden lg:flex gap-4 border-l border-white/10 pl-4">
                            <div title="System Load">
                                <div className="flex items-center gap-1 text-[10px] text-gray-500 mb-0.5">
                                    <CpuChipIcon className="w-3 h-3" /> CPU
                                </div>
                                <div className={`text-xs font-bold ${effectiveStatus.system.cpu_percent > 80 ? 'text-red-500' : 'text-gray-300'}`}>
                                    {effectiveStatus.system.cpu_percent.toFixed(1)}%
                                </div>
                            </div>

                            <div title="RAM Usage">
                                <div className="flex items-center gap-1 text-[10px] text-gray-500 mb-0.5">
                                    <CpuChipIcon className="w-3 h-3" /> RAM
                                </div>
                                <div className={`text-xs font-bold text-gray-300`}>
                                    {effectiveStatus.system.ram_percent.toFixed(1)}%
                                </div>
                            </div>

                            <div title="TikTok Schedule Window">
                                <div className="flex items-center gap-1 text-[10px] text-gray-500 mb-0.5">
                                    <ClockIcon className="w-3 h-3" /> QUOTA
                                </div>
                                <div className="w-16 h-1 mt-1 bg-gray-800 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${quotaPercent > 90 ? 'bg-red-500' : 'bg-synapse-primary'}`}
                                        style={{ width: `${quotaPercent}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Side Controls */}
                <div className="flex items-center gap-4">
                    {/* Worker Controls */}
                    <div className="flex items-center gap-2">
                        <NeonButton variant="ghost" className="p-1.5 h-8 w-8 rounded-full" title="Pause"><PauseCircleIcon className="w-5 h-5" /></NeonButton>
                        <NeonButton variant="ghost" className="p-1.5 h-8 w-8 rounded-full text-synapse-emerald" title="Resume"><PlayCircleIcon className="w-5 h-5" /></NeonButton>
                        <NeonButton variant="danger" className="p-1.5 h-8 w-8 rounded-full" title="STOP"><XCircleIcon className="w-5 h-5" /></NeonButton>
                    </div>

                    <div className="h-6 w-px bg-white/10 hidden md:block"></div>

                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="text-gray-500 hover:text-white transition-colors flex items-center gap-2 text-xs font-mono group"
                    >
                        <CommandLineIcon className="w-4 h-4 group-hover:text-synapse-primary" />
                        {expanded ? 'HIDE_LOGS' : '>_ TERMINAL'}
                    </button>
                </div>
            </div>

            {/* Breadcrumbs / Pipeline Stepper */}
            <div className="px-5 py-2 border-b border-white/5 flex overflow-x-auto gap-4 scrollbar-hide">
                {[
                    { id: 'ingesting', label: 'INGEST', icon: CloudArrowUpIcon },
                    { id: 'transcribing', label: 'CAPTION', icon: ChatBubbleBottomCenterTextIcon },
                    { id: 'rendering', label: 'RENDER', icon: FilmIcon },
                    { id: 'uploading', label: 'PUBLISH', icon: PaperAirplaneIcon }
                ].map((step, i, arr) => {
                    const isActive = effectiveStatus.job.step?.toLowerCase().includes(step.id);
                    const isCompleted = false; // logic placeholder
                    const iconColor = isActive ? 'text-white' : 'text-gray-600';
                    const activeBg = isActive ? 'bg-synapse-primary/20 border-synapse-primary/40' : 'border-transparent';

                    return (
                        <div key={step.id} className="flex items-center shrink-0">
                            <div className={`flex items-center gap-2 px-2 py-1 rounded border ${activeBg} transition-all`}>
                                <step.icon className={`w-3.5 h-3.5 ${iconColor}`} />
                                <span className={`text-[10px] font-bold ${isActive ? 'text-white' : 'text-gray-600'}`}>{step.label}</span>
                            </div>
                            {i < arr.length - 1 && (
                                <div className="w-3 h-px bg-white/10 mx-2" />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* BOTS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border-b border-white/5 bg-black/20">
                {(effectiveStatus.bots || []).map(bot => (
                    <BotCard key={bot.id} {...bot} />
                ))}
            </div>

            {/* Expanded Logs */}
            {expanded && (
                <div className="p-4 bg-[#05040a] font-mono text-xs text-synapse-text border-t border-synapse-border max-h-[200px] overflow-y-auto custom-scrollbar">
                    {effectiveStatus.job.logs.length > 0 ? (
                        effectiveStatus.job.logs.map((log, i) => (
                            <div key={i} className="mb-1.5 flex gap-2">
                                <span className="text-synapse-primary/50 text-[10px] opacity-50 select-none leading-5">
                                    {new Date(effectiveStatus.last_updated || Date.now()).toLocaleTimeString()}
                                </span>
                                <span className="text-synapse-secondary select-none">➜</span>
                                <span className={`${i === 0 ? 'text-white font-bold' : 'opacity-80'}`}>{log}</span>
                            </div>
                        ))
                    ) : (
                        <div className="opacity-30 italic">Waiting for system output...</div>
                    )}
                </div>
            )}
        </StitchCard>
    );
}
