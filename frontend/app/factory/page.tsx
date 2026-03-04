'use client';

import React, { useState, useEffect, useCallback } from 'react';
import useWebSocket from '../hooks/useWebSocket';
import { BackendStatus } from '../types';

import { getApiUrl } from '../utils/apiClient';
import { toast } from 'sonner';

const API_BASE = `${getApiUrl()}/api/v1`;

export default function FactoryPage() {
    const [status, setStatus] = useState({ queued: 0, processing: 0, completed: 0, failed: 0 });
    const [scanning, setScanning] = useState(false);
    const [activeJob, setActiveJob] = useState<BackendStatus['job'] | null>(null);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/ingest/status`);
            if (res.ok) setStatus(await res.json());
        } catch (error) {
            console.error('Failed to fetch ingestion status', error);
            // toast.error("Falha ao buscar status de ingestão"); // Retirado toast para não espamar a cada 5s
        }
    }, []);

    const { isConnected } = useWebSocket({
        onPipelineUpdate: (data) => {
            setActiveJob(data.job);
            fetchStatus();
        }
    });

    const triggerScan = async () => {
        setScanning(true);
        try {
            const res = await fetch(`${API_BASE}/content/scan`, { method: 'POST' });
            if (!res.ok) {
                toast.error('Falha ao acionar Injeção manual.');
            } else {
                toast.success('Escaneamento iniciado!');
            }
            await fetchStatus();
        } catch (error) {
            toast.error('Erro de conexão com o painel de Factory.');
        }
        setScanning(false);
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    return (
        <div className="flex flex-col flex-1 h-full relative">
            {/* Header Area */}
            <div className="flex-none px-8 py-6 z-10 border-b border-white/5 bg-black/60 backdrop-blur-md">
                <div className="flex flex-wrap justify-between items-end gap-4">
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-3">
                            <h1 className="text-white text-4xl font-bold tracking-tight font-display">
                                PIPELINE <span className="text-cyan-400 font-mono font-normal">INDUSTRIAL</span>
                            </h1>
                            {isConnected && (
                                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_10px_rgba(0,240,255,0.2)]">
                                    <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></span>
                                    TRANSMISSÃO AO VIVO
                                </div>
                            )}
                        </div>
                        <p className="text-slate-400 text-xs font-mono tracking-wide flex items-center gap-2">
                            STATUS DO SISTEMA: <span className="text-emerald-500">IDEAL</span> // FLUXO_DADOS:
                            <span className="flex gap-0.5 items-end h-3">
                                <span className="w-0.5 bg-cyan-500/50 h-1 animate-pulse"></span>
                                <span className="w-0.5 bg-cyan-500/50 h-2 animate-pulse" style={{ animationDelay: '0.1s' }}></span>
                                <span className="w-0.5 bg-cyan-500/50 h-3 animate-pulse" style={{ animationDelay: '0.2s' }}></span>
                                <span className="w-0.5 bg-cyan-500/50 h-1.5 animate-pulse" style={{ animationDelay: '0.3s' }}></span>
                            </span>
                        </p>
                    </div>

                    <div className="flex gap-6 items-center">
                        <button
                            onClick={triggerScan}
                            disabled={scanning}
                            className={`flex items-center justify-center gap-2 rounded h-8 px-4 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/50 text-cyan-400 text-xs font-bold font-mono tracking-widest uppercase transition-all hover:shadow-[0_0_15px_rgba(0,240,255,0.3)] group ${scanning ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <span className={`material-symbols-outlined text-[16px] ${scanning ? 'animate-spin' : 'group-hover:rotate-90 transition-transform'}`}>
                                {scanning ? 'sync' : 'add'}
                            </span>
                            <span>{scanning ? 'Escaneando...' : 'Injetar Dados'}</span>
                        </button>
                        <div className="flex flex-col items-end border-l border-white/10 pl-6">
                            <span className="text-slate-500 text-[10px] font-mono uppercase tracking-widest">Pacotes Ativos</span>
                            <span className="text-2xl font-mono text-white">{status.processing || 12}<span className="text-cyan-400 text-sm">/{status.queued || 64}</span></span>
                        </div>
                        <div className="flex flex-col items-end border-l border-white/10 pl-6">
                            <span className="text-slate-500 text-[10px] font-mono uppercase tracking-widest">Eficiência</span>
                            <span className="text-2xl font-mono text-emerald-400">
                                {status.completed + status.failed > 0
                                    ? Math.round((status.completed / ((status.completed + status.failed) || 1)) * 100)
                                    : '--'}<span className="text-slate-500 text-sm">%</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Pipeline Content */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden relative z-10 scroll-smooth pb-20 mt-8">
                <div className="max-w-5xl mx-auto px-8 relative min-h-full">

                    {/* Center Laser Line */}
                    <div className="absolute left-8 md:left-[50%] top-0 bottom-0 w-[1px] bg-white/5 transform md:-translate-x-1/2">
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-400 to-transparent opacity-30 w-[1px] blur-[1px]"></div>
                        <div className="absolute top-0 left-[-1px] right-[-1px] h-32 bg-gradient-to-b from-transparent via-cyan-400 to-transparent blur-md animate-laser-flow" style={{ backgroundSize: '100% 200%' }}></div>
                        <div className="absolute top-0 left-[-2px] right-[-2px] h-16 bg-white mix-blend-overlay opacity-80 blur-sm animate-laser-flow" style={{ animationDelay: '1s' }}></div>
                        <div className="absolute w-1.5 h-3 bg-cyan-400 rounded-full left-1/2 -translate-x-1/2 shadow-[0_0_10px_#00f0ff] animate-packet-drop"></div>
                        <div className="absolute w-1 h-2 bg-indigo-500 rounded-full left-1/2 -translate-x-1/2 shadow-[0_0_8px_#6366f1] animate-packet-drop" style={{ animationDelay: '2s', animationDuration: '5s' }}></div>
                    </div>

                    {/* Step 1: Ingestion */}
                    <div className="relative mb-24 group">
                        <div className="absolute left-8 md:left-[50%] top-8 w-4 h-4 bg-black border-2 border-slate-700 group-hover:border-cyan-400 rounded-full transform -translate-x-1/2 z-20 transition-colors shadow-[0_0_15px_rgba(0,0,0,1)]">
                            <div className="w-1.5 h-1.5 bg-slate-700 group-hover:bg-cyan-400 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 transition-colors"></div>
                        </div>
                        <div className="absolute left-16 md:left-[54%] top-7 z-10">
                            <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 group-hover:text-cyan-400 transition-colors flex items-center gap-2">
                                <span className="material-symbols-outlined text-sm">hourglass_empty</span>
                                Fila de Ingestão de Dados
                            </h3>
                            <p className="text-[10px] text-slate-600 font-mono mt-1">{status.queued} Itens Pendentes</p>
                        </div>

                        <div className="md:w-[45%] md:mr-auto pl-16 md:pl-0 md:pr-12 relative">
                            {/* Dynamic Queue Item or Empty State */}
                            {status.queued > 0 ? (
                                <div className="pod-card bg-black/40 border border-white/5 rounded-sm p-1 relative overflow-hidden group/pod backdrop-blur-sm">
                                    <div className="bg-white/5 px-3 py-2 flex justify-between items-center border-b border-white/5">
                                        <span className="text-[10px] font-mono text-slate-400">STATUS: QUEUED</span>
                                        <span className="text-[10px] font-mono text-cyan-400 animate-pulse">AGUARDANDO PROC</span>
                                    </div>
                                    <div className="p-3 flex gap-4">
                                        <div className="relative w-24 h-16 bg-black border border-white/10 overflow-hidden group-hover/pod:border-cyan-500/50 transition-colors shrink-0 flex items-center justify-center">
                                            <span className="material-symbols-outlined text-cyan-500/30 text-2xl">movie</span>
                                            <div className="absolute top-0 w-full h-[2px] bg-cyan-500/50 shadow-[0_0_5px_#00f0ff] animate-laser-flow"></div>
                                        </div>
                                        <div className="flex-1 min-w-0 flex flex-col justify-between py-1">
                                            <div>
                                                <h4 className="text-white font-bold text-sm truncate font-display">Itens em Fila</h4>
                                                <p className="text-slate-500 text-[10px] font-mono mt-1">Lotes Brutos Detectados pelo Watcher</p>
                                            </div>
                                            <div className="flex items-center gap-2 mt-2">
                                                <button className="text-[9px] font-mono border border-slate-700 hover:border-cyan-400 hover:text-cyan-400 hover:bg-cyan-400/5 px-2 py-1 transition-all rounded-sm uppercase opacity-50 cursor-not-allowed">Injeção Padrão</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="pod-card bg-black/20 border border-white/5 border-dashed rounded-sm p-4 text-center">
                                    <p className="text-slate-500 text-xs font-mono">Nenhum diretório pendente na fila primária.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Step 2: Processing Node */}
                    <div className="relative mb-24 group">
                        <div className="absolute left-8 md:left-[50%] top-8 w-4 h-4 bg-black border-2 border-cyan-400 shadow-[0_0_15px_#00f0ff] rounded-full transform -translate-x-1/2 z-20">
                            <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-ping"></div>
                        </div>
                        <div className="hidden md:block absolute left-[50%] top-[2.1rem] w-[calc(50%-1rem)] h-[1px] bg-gradient-to-r from-cyan-400/50 to-transparent z-0">
                            <div className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent via-white to-transparent opacity-50 animate-laser-flow" style={{ width: '20px', backgroundSize: '200% 100%' }}></div>
                        </div>
                        <div className="absolute right-auto left-16 md:right-[54%] md:left-auto top-7 z-10 text-right">
                            <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400 flex items-center justify-end gap-2 text-shadow-[0_0_10px_rgba(0,240,255,0.5)]">
                                Nó de Processamento [GPU-04]
                                <span className="material-symbols-outlined text-sm animate-spin">settings</span>
                            </h3>
                        </div>

                        <div className="md:w-[45%] md:ml-auto pl-16 md:pl-12 md:pr-0 relative">
                            <div className="pod-card active-glow bg-[#050505] border border-cyan-400 rounded-sm p-0 relative overflow-hidden">
                                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 mix-blend-overlay pointer-events-none z-20"></div>

                                <div className="relative w-full aspect-video bg-black overflow-hidden group/video">
                                    <div className="absolute inset-0 bg-[linear-gradient(rgba(0,240,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,240,255,0.1)_1px,transparent_1px)] bg-[size:40px_40px] perspective-[500px] rotate-x-12 opacity-30 animate-pulse"></div>

                                    <div className="absolute top-4 left-4 font-mono text-[10px] text-cyan-400 bg-black/80 px-2 py-1 border-l-2 border-cyan-400 shadow-[0_0_10px_rgba(0,240,255,0.2)]">
                                        {activeJob ? activeJob.step.toUpperCase() : 'IDLE :: AGUARDANDO NODE'}
                                    </div>

                                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-32 h-32 flex items-center justify-center">
                                        {activeJob && <div className="absolute inset-0 border border-cyan-400/20 rounded-full animate-[spin_4s_linear_infinite]"></div>}
                                        <div className="particle-ring absolute w-28 h-28"></div>
                                        <div className="relative w-24 h-24 rounded-full border border-cyan-400/30 flex items-center justify-center backdrop-blur-sm bg-black/40">
                                            {activeJob && <div className="absolute inset-0 border-t-2 border-cyan-400 rounded-full animate-spin shadow-[0_0_15px_#00f0ff]"></div>}
                                            <span className="text-2xl font-bold font-mono text-white drop-shadow-[0_0_5px_#00f0ff]">
                                                {activeJob ? activeJob.progress : '--'}
                                                <span className="text-xs text-cyan-400">%</span>
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-black/60 backdrop-blur border-t border-cyan-400/20 p-4 grid grid-cols-2 gap-4">
                                    <div>
                                        <h4 className="text-white font-bold text-sm truncate uppercase tracking-wide">{activeJob ? activeJob.name : 'Nenhum Pacote Ativo'}</h4>
                                        <p className="text-slate-500 text-[9px] font-mono mt-0.5">ALVO: {activeJob ? 'PROCESSAMENTO_VIDEO' : 'SISTEMA_STANDBY'}</p>
                                    </div>
                                    <div className="flex flex-col gap-1 justify-center">
                                        <div className="flex justify-between text-[9px] font-mono text-cyan-400/70 uppercase">
                                            <span>Uso de VRAM</span>
                                            <span>{activeJob ? '-- GB' : '0.0 GB'}</span>
                                        </div>
                                        <div className="h-1 bg-white/5 w-full rounded-full overflow-hidden relative">
                                            <div className="absolute inset-0 bg-cyan-400/20 animate-pulse"></div>
                                            <div className={`h-full bg-cyan-400 shadow-[0_0_10px_#00f0ff] relative overflow-hidden`} style={{ width: `${activeJob ? activeJob.progress : 0}%` }}>
                                                {activeJob && <div className="absolute inset-0 bg-white/30 skew-x-12 w-4 animate-laser-flow"></div>}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Step 3: Deployment */}
                    <div className="relative group">
                        <div className="absolute left-8 md:left-[50%] top-8 w-4 h-4 bg-black border-2 border-emerald-500 shadow-[0_0_15px_#10b981] rounded-full transform -translate-x-1/2 z-20">
                            <span className="material-symbols-outlined text-[10px] text-emerald-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">check</span>
                        </div>
                        <div className="absolute right-auto left-16 md:right-[54%] md:left-auto top-7 z-10 text-right">
                            <h3 className="text-xs font-mono uppercase tracking-[0.2em] text-emerald-500 flex items-center justify-end gap-2">
                                Pronto para Implantação
                                <span className="material-symbols-outlined text-sm">rocket_launch</span>
                            </h3>
                            <p className="text-[10px] text-emerald-500/60 font-mono mt-1 text-left md:text-right">{status.completed} Itens Concluídos</p>
                        </div>

                        <div className="md:w-[45%] md:ml-auto pl-16 md:pl-12 md:pr-0 relative flex flex-col gap-4">
                            {status.completed > 0 ? (
                                <div className="pod-card bg-black/40 backdrop-blur-sm border border-emerald-900/50 hover:border-emerald-500 rounded-sm p-4 flex flex-col overflow-hidden group/done transition-all duration-300">
                                    <div>
                                        <div className="flex justify-between items-start mb-1">
                                            <h4 className="text-white font-bold text-sm truncate uppercase">Aguardando Avaliação</h4>
                                            <span className="text-[9px] text-amber-500 border border-amber-900 bg-amber-900/20 px-1.5 py-0.5 rounded font-mono shadow-[0_0_8px_rgba(245,158,11,0.2)]">PENDENTE</span>
                                        </div>
                                        <p className="text-slate-500 text-xs font-mono">Último Processamento Finalizado</p>
                                    </div>
                                    <div className="flex gap-2 mt-4 flex-wrap">
                                        <button className="flex-[1_1_100%] bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono uppercase py-2 transition-all flex items-center justify-center gap-2 font-bold">
                                            <span className="material-symbols-outlined text-[16px]">check_circle</span> Aprovar e Enfileirar
                                        </button>
                                        <button className="flex-1 bg-white/5 hover:bg-cyan-500/10 border border-white/10 hover:border-cyan-500/50 text-cyan-400 text-[10px] font-mono uppercase py-2 transition-all flex items-center justify-center gap-2">
                                            <span className="material-symbols-outlined text-[16px]">shuffle</span> Inverter Ordem
                                        </button>
                                        <button className="flex-1 bg-white/5 hover:bg-red-500/10 border border-white/10 hover:border-red-500/50 text-red-500 text-[10px] font-mono uppercase py-2 transition-all flex items-center justify-center gap-2">
                                            <span className="material-symbols-outlined text-[16px]">delete</span> Descartar
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="pod-card bg-black/20 border border-white/5 border-dashed rounded-sm p-4 text-center">
                                    <p className="text-slate-500 text-xs font-mono">Nenhum pipeline finalizado ainda.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="absolute left-8 md:left-[50%] bottom-0 w-2 h-2 bg-white/10 rounded-full transform -translate-x-1/2"></div>
                </div>
            </div>
        </div>
    );
}
