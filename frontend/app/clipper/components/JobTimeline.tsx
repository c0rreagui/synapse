'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { GlassPanel } from '@/components/design-system/GlassPanel';
import { Activity, Clock, CheckCircle2, AlertTriangle, Play, RefreshCw, Layers } from 'lucide-react';
import { getApiUrl } from '../../utils/apiClient';

interface ClipJob {
    id: number;
    target_id: number;
    status: string;
    current_step: string;
    progress_pct: number;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

export function JobTimeline() {
    const API = getApiUrl();

    // GET Jobs with intelligent polling
    const { data: jobs, isLoading } = useQuery<ClipJob[]>({
        queryKey: ['clipper-jobs'],
        queryFn: async () => {
            const res = await fetch(`${API}/api/clipper/jobs`);
            if (!res.ok) throw new Error('Falha ao carregar jobs');
            return res.json();
        },
        refetchInterval: (query) => {
            // Poll faster if there are pending/editing jobs
            const hasActiveJobs = query.state.data?.some(j => j.status !== 'completed' && j.status !== 'failed');
            return hasActiveJobs ? 3000 : 15000;
        }
    });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed': return <CheckCircle2 className="w-4 h-4" />;
            case 'failed': return <AlertTriangle className="w-4 h-4" />;
            case 'pending':
            default: return <Clock className="w-4 h-4" />;
        }
    };

    const getStatusColorClass = (status: string) => {
        switch (status) {
            case 'completed': return 'text-emerald-500 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.3)]';
            case 'failed': return 'text-red-500 border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.3)]';
            case 'pending':
            default: return 'text-blue-500 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.3)]';
        }
    };

    const formatRelativeTime = (dateStr: string) => {
        const d = new Date(dateStr);
        const agora = new Date();
        const diffMs = agora.getTime() - d.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        if (diffMins < 1) return 'Agora mesmo';
        if (diffMins < 60) return `Há ${diffMins} minutos`;
        const diffHrs = Math.floor(diffMins / 60);
        if (diffHrs < 24) return `Há ${diffHrs} horas`;
        return d.toLocaleDateString();
    };

    return (
        <div className="flex-1 flex flex-col gap-4 min-w-0 h-full">
            <GlassPanel intensity="medium" className="flex-1 p-6 flex flex-col min-h-0">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="font-bold text-lg text-white tracking-wide flex items-center gap-2">
                        <Activity className="text-neo-primary w-5 h-5" />
                        Processing Jobs
                    </h3>
                    <div className="flex items-center gap-2">
                        {isLoading && <RefreshCw className="w-4 h-4 text-gray-500 animate-spin" />}
                        <div className="text-xs font-mono text-gray-500 px-2 py-1 rounded bg-black/40 border border-white/10">
                            Auto-Polling
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
                    {!isLoading && jobs?.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-3">
                            <Layers className="w-12 h-12 opacity-20" />
                            <p>Nenhum job processado ainda.</p>
                        </div>
                    )}

                    {jobs?.map((job) => {
                        const isCompleted = job.status === 'completed';
                        const isFailed = job.status === 'failed';
                        const isActive = !isCompleted && !isFailed;

                        return (
                            <div key={job.id} className="relative pl-8 pb-8 border-l border-white/10 last:border-0 last:pb-0">
                                <div className={`absolute left-[-17px] top-0 w-8 h-8 rounded-full bg-[#050507] border flex items-center justify-center ${getStatusColorClass(job.status)}`}>
                                    {getStatusIcon(job.status)}
                                </div>
                                <div className={`border rounded-xl p-4 flex flex-col gap-2 transition-all ${isCompleted ? 'bg-emerald-500/5 border-emerald-500/20' :
                                    isFailed ? 'bg-red-500/5 border-red-500/20' :
                                        'bg-blue-500/5 border-blue-500/20'
                                    }`}>
                                    <div className="flex items-center justify-between">
                                        <div className="font-bold text-white text-sm">
                                            Job #{job.id} • {job.error_message ? 'Errou' : 'Target ' + job.target_id}
                                        </div>
                                        <div className="text-xs font-mono text-gray-400">
                                            {formatRelativeTime(job.created_at)}
                                        </div>
                                    </div>

                                    {!isCompleted && !isFailed && (
                                        <>
                                            <div className="text-xs text-gray-300 capitalize">{job.current_step || 'Aguardando fila...'}</div>
                                            <div className="w-full bg-black/50 rounded-full h-1.5 mt-2 overflow-hidden">
                                                <div
                                                    className="bg-blue-500 h-full rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                                                    style={{ width: `${job.progress_pct}%` }}
                                                />
                                            </div>
                                        </>
                                    )}

                                    {isFailed && (
                                        <div className="text-xs text-red-400 mt-1 bg-red-500/10 p-2 rounded border border-red-500/20">
                                            {job.error_message}
                                        </div>
                                    )}

                                    {isCompleted && (
                                        <div className="flex items-center justify-between mt-1">
                                            <div className="text-xs text-emerald-400 font-mono">Completed • Próximo ao output</div>
                                            <button className="w-8 h-8 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 flex items-center justify-center transition-all" title="Ver Arquivo (Mock)">
                                                <Play className="w-4 h-4 ml-0.5" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </GlassPanel>
        </div>
    );
}
