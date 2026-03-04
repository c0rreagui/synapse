'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '../utils/apiClient';
import { toast } from 'sonner';
import axios from 'axios';

interface Target {
    id: number;
    channel_url: string;
    channel_name: string;
    broadcaster_id?: string;
    active: boolean;
    status?: string;
}

interface PendingItem {
    id: number;
    clip_job_id: number | null;
    video_path: string;
    thumbnail_path: string | null;
    streamer_name: string | null;
    title: string | null;
    duration_seconds: number | null;
    file_size_bytes: number | null;
    status: string;
    created_at: string;
}

interface QueueStatus {
    profile: string;
    queued: number;
    scheduled: number;
    failed: number;
    total_pending: number;
}

type Tab = 'targets' | 'queue';

export default function ClipperPage() {
    const [activeTab, setActiveTab] = useState<Tab>('targets');
    const [targets, setTargets] = useState<Target[]>([]);
    const [urlInput, setUrlInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    // Queue state (moved from home page)
    const [items, setItems] = useState<PendingItem[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [queueLoading, setQueueLoading] = useState(true);
    const [actionFeedback, setActionFeedback] = useState<string | null>(null);
    const [feedbackType, setFeedbackType] = useState<'approve' | 'reject' | 'invert' | null>(null);
    const [processing, setProcessing] = useState(false);
    const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);

    const API = getApiUrl();

    // ── Targets logic ──
    const fetchTargets = async () => {
        try {
            const res = await fetch(`${API}/api/clipper/targets`);
            if (res.ok) setTargets(await res.json());
        } catch (error) {
            console.error("Failed to fetch targets:", error);
        }
    };

    useEffect(() => {
        fetchTargets();
        const interval = setInterval(fetchTargets, 10000);
        return () => clearInterval(interval);
    }, []);

    const handleAddTarget = async () => {
        if (!urlInput.trim()) return;
        setIsLoading(true);
        try {
            const res = await fetch(`${API}/api/clipper/targets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel_url: urlInput.trim() })
            });
            if (res.ok) {
                setUrlInput("");
                toast.success("Novo alvo detectado e adicionado à órbita.");
                await fetchTargets();
            } else {
                const errorData = await res.json();
                toast.error(`Erro: ${errorData.detail}`);
            }
        } catch (error) {
            toast.error("Erro de conexão com o painel orbital.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteTarget = async (id: number) => {
        if (!confirm("Tem certeza que deseja remover este alvo da órbita?")) return;
        try {
            const res = await fetch(`${API}/api/clipper/targets/${id}`, { method: 'DELETE' });
            if (res.ok) {
                toast.success("Alvo removido da radar.");
                await fetchTargets();
            } else {
                toast.error("Falha ao remover o alvo.");
            }
        } catch (error) {
            toast.error("Erro de conexão ao tentar deletar o alvo.");
        }
    };

    // ── Queue / Esteira logic ──
    const fetchPending = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/api/v1/factory/pending`);
            setItems(res.data || []);
            setCurrentIndex(0);
        } catch (err) {
            console.error('Fetch pending error:', err);
        } finally {
            setQueueLoading(false);
        }
    }, [API]);

    const fetchQueueStatus = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/api/v1/factory/queue-status`);
            setQueueStatus(res.data);
        } catch (err) {
            console.error('Fetch queue status error:', err);
        }
    }, [API]);

    useEffect(() => {
        if (activeTab === 'queue') {
            fetchPending();
            fetchQueueStatus();
        }
    }, [activeTab, fetchPending, fetchQueueStatus]);

    const current = items[currentIndex] || null;

    const showFeedback = (msg: string, type: 'approve' | 'reject' | 'invert') => {
        setActionFeedback(msg);
        setFeedbackType(type);
        setTimeout(() => { setActionFeedback(null); setFeedbackType(null); }, 1500);
    };

    const handleApprove = async () => {
        if (!current || processing) return;
        setProcessing(true);
        try {
            const res = await axios.post(`${API}/api/v1/factory/approve/${current.id}`);
            showFeedback(`✅ ${res.data.message}`, 'approve');
            setItems(prev => prev.filter(i => i.id !== current.id));
            await fetchQueueStatus();
            if (currentIndex >= items.length - 1) setCurrentIndex(Math.max(0, currentIndex - 1));
        } catch (err: any) {
            showFeedback(`❌ ${err?.response?.data?.detail || 'Erro ao aprovar'}`, 'reject');
        } finally {
            setProcessing(false);
        }
    };

    const handleReject = async () => {
        if (!current || processing) return;
        setProcessing(true);
        try {
            await axios.delete(`${API}/api/v1/factory/reject/${current.id}`);
            showFeedback('🗑️ Vídeo descartado', 'reject');
            setItems(prev => prev.filter(i => i.id !== current.id));
            await fetchQueueStatus();
            if (currentIndex >= items.length - 1) setCurrentIndex(Math.max(0, currentIndex - 1));
        } catch (err: any) {
            showFeedback(`❌ ${err?.response?.data?.detail || 'Erro ao rejeitar'}`, 'reject');
        } finally {
            setProcessing(false);
        }
    };

    const handleInvert = async () => {
        if (!current || processing) return;
        setProcessing(true);
        try {
            await axios.post(`${API}/api/v1/factory/invert/${current.id}`);
            showFeedback('🔀 Layout invertido!', 'invert');
            await fetchPending();
        } catch (err: any) {
            showFeedback(`❌ ${err?.response?.data?.detail || 'Erro ao inverter'}`, 'reject');
        } finally {
            setProcessing(false);
        }
    };

    const goNext = () => { if (currentIndex < items.length - 1) setCurrentIndex(prev => prev + 1); };
    const goPrev = () => { if (currentIndex > 0) setCurrentIndex(prev => prev - 1); };

    // Keyboard shortcuts only when queue tab active
    useEffect(() => {
        if (activeTab !== 'queue') return;
        const handleKey = (e: KeyboardEvent) => {
            if (e.key === 'ArrowRight') goNext();
            if (e.key === 'ArrowLeft') goPrev();
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleApprove(); }
            if (e.key === 'Backspace' || e.key === 'Delete') handleReject();
            if (e.key === 'i' || e.key === 'I') handleInvert();
        };
        globalThis.addEventListener('keydown', handleKey);
        return () => globalThis.removeEventListener('keydown', handleKey);
    }, [activeTab, current, currentIndex, items.length]);

    const formatDuration = (s: number | null) => {
        if (!s) return '--:--';
        const m = Math.floor(s / 60);
        const sec = s % 60;
        return `${m}:${sec.toString().padStart(2, '0')}`;
    };

    const formatSize = (b: number | null) => {
        if (!b) return '-- MB';
        return `${(b / 1024 / 1024).toFixed(1)} MB`;
    };

    const getVideoPreviewUrl = (path: string) => {
        const filename = path.replaceAll('\\', '/').split('/').pop();
        return `${API}/clipper-output/${filename}`;
    };

    const feedbackColors = {
        approve: 'from-emerald-500/20 border-emerald-500/50 text-emerald-400',
        reject: 'from-red-500/20 border-red-500/50 text-red-400',
        invert: 'from-indigo-500/20 border-indigo-500/50 text-indigo-400',
    };

    return (
        <div className="flex-1 flex flex-col max-w-[1600px] w-full mx-auto gap-6 relative z-10 h-full">

            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-end gap-6 pb-2 border-b border-white/5 relative mt-6">
                <div className="absolute bottom-0 right-0 w-1/3 h-px bg-gradient-to-l from-cyan-400/50 to-transparent"></div>
                <div className="relative">
                    <h1 className="text-5xl lg:text-6xl font-bold tracking-tighter text-white uppercase drop-shadow-[0_0_25px_rgba(0,240,255,0.2)] font-display">
                        Vigilância do <span className="text-cyan-400 block text-3xl lg:text-4xl tracking-[0.2em] font-mono mt-2 font-normal drop-shadow-[0_0_10px_rgba(0,240,255,0.8)]">Espaço Profundo</span>
                    </h1>
                </div>
                <div className="flex flex-col items-end gap-1">
                    <div className="flex items-center gap-4 text-xs font-mono text-cyan-400/70">
                        <span className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm animate-spin-slow">memory</span>
                            CARGA_CPU: --%
                        </span>
                        <span className="w-px h-3 bg-white/20"></span>
                        <span className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm animate-pulse">wifi_tethering</span>
                            FLUXO_REDE: -- Mbps
                        </span>
                    </div>
                    <div className="w-full h-1 bg-surface-border mt-1 relative overflow-hidden rounded-full">
                        <div className="absolute inset-0 bg-cyan-400/80 w-1/3 animate-scan-laser" style={{ animationDuration: '3s' }}></div>
                    </div>
                </div>
            </div>

            {/* ═══ TAB SWITCHER ═══ */}
            <div className="flex items-center gap-1 bg-black/40 backdrop-blur-md border border-white/5 rounded-xl p-1 self-start">
                <button
                    onClick={() => setActiveTab('targets')}
                    className={`px-5 py-2.5 text-xs font-mono font-bold uppercase tracking-widest rounded-lg transition-all duration-200 flex items-center gap-2 ${activeTab === 'targets'
                            ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_-3px_rgba(0,240,255,0.3)]'
                            : 'text-slate-500 hover:text-white hover:bg-white/5 border border-transparent'
                        }`}
                >
                    <span className="material-symbols-outlined text-[18px]">radar</span>
                    Alvos
                    {targets.length > 0 && (
                        <span className="bg-cyan-500/20 text-cyan-400 text-[10px] px-1.5 py-0.5 rounded-md">{targets.length}</span>
                    )}
                </button>
                <button
                    onClick={() => setActiveTab('queue')}
                    className={`px-5 py-2.5 text-xs font-mono font-bold uppercase tracking-widest rounded-lg transition-all duration-200 flex items-center gap-2 ${activeTab === 'queue'
                            ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_-3px_rgba(0,240,255,0.3)]'
                            : 'text-slate-500 hover:text-white hover:bg-white/5 border border-transparent'
                        }`}
                >
                    <span className="material-symbols-outlined text-[18px]">movie_filter</span>
                    Esteira
                    {items.length > 0 && (
                        <span className="bg-amber-500/20 text-amber-400 text-[10px] px-1.5 py-0.5 rounded-md">{items.length}</span>
                    )}
                </button>
            </div>

            {/* ═══ TAB: ALVOS ═══ */}
            {activeTab === 'targets' && (
                <>
                    {/* Input Target Section */}
                    <section className="flex justify-center py-12 relative shrink-0">
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="w-[600px] h-[600px] border border-white/5 rounded-full absolute animate-spin-slow opacity-50" style={{ animationDuration: '60s' }}></div>
                            <div className="w-[400px] h-[400px] border border-dashed border-cyan-400/30 rounded-full absolute animate-spin-slow" style={{ animationDirection: 'reverse', animationDuration: '40s' }}></div>
                        </div>

                        <div className="relative w-full max-w-2xl group">
                            <div className="absolute -inset-4 border border-cyan-400/40 rounded-full border-t-transparent border-l-transparent animate-spin-slow shadow-[0_0_30px_rgba(0,240,255,0.1)]"></div>
                            <div className="bg-black/80 backdrop-blur-xl border border-cyan-400/60 rounded-full p-2 relative shadow-[0_0_50px_-10px_rgba(0,240,255,0.25)] aperture-ring transition-all duration-500 flex items-center overflow-hidden">
                                <div className="laser-sweep animate-scan-laser"></div>
                                <div className="pl-6 pr-4 text-cyan-400 animate-pulse z-10">
                                    <span className="material-symbols-outlined text-3xl drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]">filter_center_focus</span>
                                </div>
                                <div className="flex-1 aperture-input relative z-10">
                                    <input
                                        type="text"
                                        value={urlInput}
                                        onChange={(e) => setUrlInput(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleAddTarget()}
                                        placeholder="INSERIR_COORDENADAS_ALVO [URL da Twitch]..."
                                        className="w-full bg-transparent border-none text-white text-lg font-mono placeholder:text-cyan-400/40 focus:ring-0 py-4 tracking-wider uppercase focus:outline-none"
                                        disabled={isLoading}
                                    />
                                </div>
                                <button
                                    onClick={handleAddTarget}
                                    disabled={isLoading}
                                    className="z-10 bg-cyan-400/10 hover:bg-cyan-400 hover:text-black text-cyan-400 border border-cyan-400/50 rounded-full px-8 py-3 mr-1 transition-all duration-300 flex items-center gap-2 group/btn shadow-[0_0_15px_rgba(0,240,255,0.1)] hover:shadow-[0_0_25px_rgba(0,240,255,0.6)] disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? (
                                        <span className="material-symbols-outlined animate-spin text-sm">autorenew</span>
                                    ) : (
                                        <>
                                            <span className="font-mono font-bold tracking-widest text-sm">INICIAR</span>
                                            <span className="material-symbols-outlined group-hover/btn:translate-x-1 transition-transform text-sm">sensors</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* Targets Grid */}
                    <section className="flex-1 overflow-y-auto custom-scrollbar pb-10">
                        <div className="flex items-center justify-between mb-6 border-b border-cyan-400/20 pb-2">
                            <h3 className="text-xl font-bold text-white flex items-center gap-3 font-mono">
                                <span className="material-symbols-outlined text-cyan-400 animate-pulse">grid_view</span>
                                ALVOS_DE_RECONHECIMENTO_ORBITAL
                            </h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {targets.length === 0 && (
                                <div className="col-span-full py-20 text-center text-cyan-400/50 font-mono flex flex-col items-center gap-4">
                                    <span className="material-symbols-outlined text-5xl">satellite_alt</span>
                                    NENHUM_ALVO_DETECTADO_NO_RADAR
                                </div>
                            )}

                            {targets.map(target => (
                                <div key={target.id} className={`group relative bg-[#050a0f] border border-[#122026] hover:border-cyan-400/60 transition-all duration-300 overflow-hidden rounded-lg shadow-[0_0_0_1px_rgba(0,0,0,0)] hover:shadow-[0_0_20px_rgba(0,240,255,0.15)] ${!target.active ? 'opacity-60 hover:opacity-100 grayscale contrast-125' : ''}`}>
                                    <div className="absolute inset-0 bg-[linear-gradient(transparent_0%,rgba(0,240,255,0.08)_50%,transparent_100%)] h-[200%] w-full -translate-y-1/2 group-hover:translate-y-0 transition-transform duration-1000 ease-in-out pointer-events-none z-20 opacity-0 group-hover:opacity-100"></div>

                                    <div className="absolute top-0 left-0 w-full z-10 flex justify-between items-start p-4">
                                        {target.active ? (
                                            <div className="bg-black/70 backdrop-blur border border-red-500/50 text-red-500 px-3 py-1 text-[10px] font-bold font-mono uppercase tracking-widest flex items-center gap-2 shadow-[0_0_15px_rgba(255,42,42,0.3)]">
                                                <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-ping"></span>
                                                SINAL_AO_VIVO
                                            </div>
                                        ) : (
                                            <div className="bg-black/60 backdrop-blur border border-slate-600/50 text-slate-400 px-3 py-1 text-[10px] font-bold font-mono uppercase tracking-widest flex items-center gap-2">
                                                <span className="w-1.5 h-1.5 bg-slate-500 rounded-full"></span>
                                                SINAL_INATIVO
                                            </div>
                                        )}
                                    </div>

                                    <div className={`h-48 bg-[#0a0a0a] relative ${target.active ? 'group-hover:scale-105 transition-transform duration-700' : ''}`}>
                                        <div className="absolute inset-0 bg-gradient-to-t from-[#050a0f] via-[#050a0f]/30 to-transparent z-10"></div>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <span className="material-symbols-outlined text-white/10 text-6xl">videocam</span>
                                        </div>
                                        {target.active && (
                                            <div className="absolute bottom-4 left-4 right-4 h-12 flex items-end gap-1 justify-center opacity-90 pb-2 border-b border-cyan-400/20 z-20">
                                                <div className="waveform-bar h-full" style={{ animationDuration: '0.6s' }}></div>
                                                <div className="waveform-bar h-full" style={{ animationDuration: '0.8s', animationDelay: '0.1s' }}></div>
                                                <div className="waveform-bar h-full" style={{ animationDuration: '1.1s', animationDelay: '0.2s' }}></div>
                                                <div className="waveform-bar h-full" style={{ animationDuration: '0.7s', animationDelay: '0.05s' }}></div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="p-5 relative z-10 -mt-10">
                                        <div className="flex items-end gap-4 mb-4">
                                            <div className={`size-12 rounded border ${target.active ? 'border-cyan-400/50 shadow-[0_0_15px_rgba(0,240,255,0.3)]' : 'border-slate-700'} bg-[#111] flex items-center justify-center overflow-hidden`}>
                                                <span className={`${target.active ? 'text-cyan-400' : 'text-slate-500'} text-xs font-bold font-mono`}>
                                                    {target.channel_name ? target.channel_name.substring(0, 4).toUpperCase() : '---'}
                                                </span>
                                            </div>
                                            <div>
                                                <h4 className={`font-bold text-lg font-mono ${target.active ? 'text-white group-hover:text-cyan-400' : 'text-slate-400'} transition-colors truncate max-w-[150px]`}>
                                                    {target.channel_name || 'Desconhecido'}
                                                </h4>
                                                <p className={`${target.active ? 'text-cyan-400/60' : 'text-slate-600'} text-xs font-mono uppercase tracking-wider flex items-center gap-1`}>
                                                    {target.active && <span className="size-1 bg-cyan-400 rounded-full"></span>}
                                                    {target.active ? 'Modo de Transmissão: Ativo' : 'Offline'}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <button onClick={() => handleDeleteTarget(target.id)} className="flex-1 bg-white/5 hover:bg-red-500/20 hover:text-red-500 hover:border-red-500/50 text-white text-xs font-mono uppercase tracking-wider py-2 border border-white/10 transition-all duration-300">
                                                Deletar Alvo
                                            </button>
                                            <a href={target.channel_url} target="_blank" rel="noreferrer" className={`flex-1 flex justify-center items-center text-center cursor-pointer ${target.active ? 'bg-cyan-400/10 hover:bg-cyan-400/30 text-cyan-400 border-cyan-400/30 hover:shadow-[0_0_10px_rgba(0,240,255,0.1)]' : 'bg-white/5 hover:bg-white/10 text-white border-white/10'} text-xs font-mono uppercase tracking-wider py-2 border transition-all duration-300`}>
                                                Abrir Radar
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                </>
            )}

            {/* ═══ TAB: ESTEIRA DE CURADORIA ═══ */}
            {activeTab === 'queue' && (
                <div className="flex-1 flex flex-col items-center justify-center px-4 py-6 relative overflow-hidden">

                    {/* Action Feedback Overlay */}
                    {actionFeedback && feedbackType && (
                        <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none">
                            <div className={`bg-gradient-to-br ${feedbackColors[feedbackType]} border backdrop-blur-xl rounded-2xl px-8 py-5 shadow-2xl animate-[fadeInScale_0.3s_ease-out]`}>
                                <p className="text-lg font-bold font-mono">{actionFeedback}</p>
                            </div>
                        </div>
                    )}

                    {queueLoading ? (
                        <div className="text-center">
                            <div className="w-12 h-12 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                            <p className="text-slate-400 font-mono text-sm">Carregando vitrine de curadoria...</p>
                        </div>
                    ) : items.length === 0 ? (
                        <div className="text-center max-w-md">
                            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-slate-800/50 border border-white/5 flex items-center justify-center">
                                <span className="material-symbols-outlined text-4xl text-slate-600">movie_filter</span>
                            </div>
                            <h2 className="text-white text-2xl font-display font-bold mb-2">Nenhum Clipe Pendente</h2>
                            <p className="text-slate-500 font-mono text-sm">
                                A esteira do Clipper está vazia. Novos clipes aparecerão aqui automaticamente
                                quando o monitor da Twitch detectar conteúdo novo.
                            </p>
                            <div className="mt-6 flex items-center justify-center gap-2 text-[10px] font-mono text-cyan-500/50">
                                <span className="w-1.5 h-1.5 bg-cyan-500/50 rounded-full animate-pulse"></span>
                                MONITOR ATIVO // AGUARDANDO CLIPES
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* Counter Badge */}
                            <div className="mb-4 flex items-center gap-3">
                                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
                                    Vitrine de Curadoria
                                </span>
                                <span className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-mono px-2 py-0.5 rounded">
                                    {currentIndex + 1} / {items.length}
                                </span>
                            </div>

                            {/* Main Card */}
                            <div className="relative w-full max-w-sm mx-auto">

                                {/* Navigation Arrows */}
                                {items.length > 1 && (
                                    <>
                                        <button
                                            onClick={goPrev}
                                            disabled={currentIndex === 0}
                                            className="absolute left-[-56px] top-1/2 -translate-y-1/2 z-30 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-all disabled:opacity-20 disabled:cursor-not-allowed"
                                        >
                                            <span className="material-symbols-outlined text-xl">chevron_left</span>
                                        </button>
                                        <button
                                            onClick={goNext}
                                            disabled={currentIndex === items.length - 1}
                                            className="absolute right-[-56px] top-1/2 -translate-y-1/2 z-30 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-slate-400 hover:text-white transition-all disabled:opacity-20 disabled:cursor-not-allowed"
                                        >
                                            <span className="material-symbols-outlined text-xl">chevron_right</span>
                                        </button>
                                    </>
                                )}

                                {/* Video Preview Card */}
                                <div className="relative bg-black/60 border border-white/10 rounded-2xl overflow-hidden shadow-[0_0_60px_rgba(0,0,0,0.5)] backdrop-blur-md group">
                                    <div className="relative aspect-[9/16] bg-black overflow-hidden">
                                        <video
                                            key={current?.video_path}
                                            src={current ? getVideoPreviewUrl(current.video_path) : ''}
                                            className="w-full h-full object-cover"
                                            autoPlay
                                            loop
                                            muted
                                            playsInline
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none"></div>

                                        {/* Top info */}
                                        <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-start z-10">
                                            <div className="bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1.5 border border-white/10">
                                                <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                                                    <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse"></span>
                                                    {current?.streamer_name || 'UNKNOWN'}
                                                </span>
                                            </div>
                                            <div className="bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1.5 border border-white/10">
                                                <span className="text-[10px] font-mono text-white/70">
                                                    {formatDuration(current?.duration_seconds || null)}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Bottom info */}
                                        <div className="absolute bottom-0 left-0 right-0 p-4 z-10">
                                            <h3 className="text-white font-bold text-lg font-display mb-1 drop-shadow-lg">
                                                {current?.title || 'Clip sem título'}
                                            </h3>
                                            <div className="flex items-center gap-3 text-[10px] font-mono text-slate-400">
                                                <span className="flex items-center gap-1">
                                                    <span className="material-symbols-outlined text-[12px]">storage</span>
                                                    {formatSize(current?.file_size_bytes || null)}
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <span className="material-symbols-outlined text-[12px]">schedule</span>
                                                    {current?.created_at ? new Date(current.created_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '--'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex items-center justify-center gap-4 mt-6">
                                    <button onClick={handleReject} disabled={processing} className="group relative w-14 h-14 rounded-full bg-red-500/10 hover:bg-red-500/20 border-2 border-red-500/30 hover:border-red-500 flex items-center justify-center transition-all duration-300 hover:scale-110 hover:shadow-[0_0_30px_rgba(239,68,68,0.3)] disabled:opacity-40 disabled:cursor-not-allowed" title="Rejeitar (Delete)">
                                        <span className="material-symbols-outlined text-red-400 group-hover:text-red-300 text-2xl">close</span>
                                    </button>
                                    <button onClick={handleInvert} disabled={processing} className="group relative w-12 h-12 rounded-full bg-indigo-500/10 hover:bg-indigo-500/20 border-2 border-indigo-500/30 hover:border-indigo-500 flex items-center justify-center transition-all duration-300 hover:scale-110 hover:shadow-[0_0_30px_rgba(99,102,241,0.3)] disabled:opacity-40 disabled:cursor-not-allowed" title="Inverter Layout (I)">
                                        <span className="material-symbols-outlined text-indigo-400 group-hover:text-indigo-300 text-xl">swap_vert</span>
                                    </button>
                                    <button onClick={handleApprove} disabled={processing} className="group relative w-14 h-14 rounded-full bg-emerald-500/10 hover:bg-emerald-500/20 border-2 border-emerald-500/30 hover:border-emerald-500 flex items-center justify-center transition-all duration-300 hover:scale-110 hover:shadow-[0_0_30px_rgba(16,185,129,0.3)] disabled:opacity-40 disabled:cursor-not-allowed" title="Aprovar e Agendar (Enter)">
                                        <span className="material-symbols-outlined text-emerald-400 group-hover:text-emerald-300 text-2xl">check</span>
                                    </button>
                                </div>

                                {/* Queue Status Widget */}
                                {queueStatus && (
                                    <div className="mt-8 bg-black/40 border border-white/5 rounded-xl p-4 max-w-sm mx-auto backdrop-blur-md">
                                        <div className="flex items-center justify-between mb-3">
                                            <span className="text-[10px] font-mono text-cyan-500/70 uppercase tracking-widest flex items-center gap-2">
                                                <span className="material-symbols-outlined text-[14px]">tune</span>
                                                Smart Queue
                                            </span>
                                            <span className="text-[10px] font-mono text-slate-500">@{queueStatus.profile}</span>
                                        </div>
                                        <div className="grid grid-cols-3 gap-2">
                                            <div className="bg-white/5 rounded-lg p-2 text-center">
                                                <div className="text-lg font-bold font-mono text-amber-400">{queueStatus.queued}</div>
                                                <div className="text-[9px] font-mono text-slate-400 uppercase">Na Fila</div>
                                            </div>
                                            <div className="bg-white/5 rounded-lg p-2 text-center border border-emerald-500/20">
                                                <div className="text-lg font-bold font-mono text-emerald-400">{queueStatus.scheduled}</div>
                                                <div className="text-[9px] font-mono text-slate-400 uppercase">No App</div>
                                            </div>
                                            <div className="bg-white/5 rounded-lg p-2 text-center">
                                                <div className="text-lg font-bold font-mono text-red-400/70">{queueStatus.failed}</div>
                                                <div className="text-[9px] font-mono text-slate-400 uppercase">Falhas</div>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Keyboard shortcuts hint */}
                                <div className="mt-4 text-center">
                                    <p className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">
                                        ← → Navegar &nbsp;|&nbsp; Enter Aprovar &nbsp;|&nbsp; Del Rejeitar &nbsp;|&nbsp; I Inverter
                                    </p>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}
