'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { getApiUrl } from '../utils/apiClient';
import { toast } from 'sonner';
import axios from 'axios';

interface Target {
    id: number;
    channel_url: string;
    channel_name: string;
    broadcaster_id?: string;
    profile_image_url?: string;
    offline_image_url?: string;
    active: boolean;
    status?: string;
    last_checked_at?: string;
    last_clip_found_at?: string;
    total_clips_processed?: number;
    consecutive_empty_checks?: number;
    min_clip_views?: number;
    max_clips_per_check?: number;
    check_interval_minutes?: number;
    target_type?: string;
    category_id?: string;
    army_id?: number | null;
}

interface Army {
    id: number;
    name: string;
    description?: string;
    color: string;
    icon: string;
    profiles: Profile[];
}

interface Profile {
    db_id?: number;
    id: string;
    slug: string;
    label?: string;
    username?: string;
    avatar_url?: string;
}

interface ClipJobResponse {
    id: number;
    target_id: number;
    status: string;
    current_step: string;
    progress_pct: number;
    error_message?: string;
    created_at: string;
    updated_at: string;
}

type Tab = 'targets' | 'queue' | 'armies';

export default function ClipperPage() {
    const [activeTab, setActiveTab] = useState<Tab>('targets');
    const [targets, setTargets] = useState<Target[]>([]);
    const [urlInput, setUrlInput] = useState("");
    const [selectedArmyId, setSelectedArmyId] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [profiles, setProfiles] = useState<Profile[]>([]);
    const [armies, setArmies] = useState<Army[]>([]);

    // Queue state (moved from home page)
    const [items, setItems] = useState<ClipJobResponse[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [queueLoading, setQueueLoading] = useState(true);
    const [vitals, setVitals] = useState<{ cpu_percent: number; uptime: string } | null>(null);
    const [targetToDelete, setTargetToDelete] = useState<number | null>(null);
    const [newArmy, setNewArmy] = useState({ name: '', color: '#00f0ff', icon: 'swords', profile_ids: [] as number[] });

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

    const fetchProfiles = async () => {
        try {
            const res = await axios.get(`${API}/api/v1/profiles/list`);
            setProfiles(res.data || []);
        } catch (err) {
            console.error('Failed to fetch profiles:', err);
        }
    };

    const fetchArmies = async () => {
        try {
            const res = await axios.get(`${API}/api/v1/armies`);
            setArmies(res.data || []);
        } catch (err) {
            console.error('Failed to fetch armies:', err);
        }
    };

    useEffect(() => {
        fetchTargets();
        fetchProfiles();
        fetchArmies();
        const interval = setInterval(fetchTargets, 10000);
        return () => clearInterval(interval);
    }, []);

    const handleAddTarget = async () => {
        if (!urlInput.trim()) return;
        setIsLoading(true);
        try {
            const payload: any = { channel_url: urlInput.trim() };
            if (selectedArmyId) {
                payload.army_id = parseInt(selectedArmyId);
            }

            const res = await fetch(`${API}/api/clipper/targets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
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

    const requestDeleteTarget = (id: number) => {
        setTargetToDelete(id);
    };

    const confirmDeleteTarget = async () => {
        if (!targetToDelete) return;
        const id = targetToDelete;
        setTargetToDelete(null); // Fecha o modal imediatamente para UX melhor

        try {
            const res = await fetch(`${API}/api/clipper/targets/${id}`, { method: 'DELETE' });
            if (res.ok) {
                toast.success("Alvo removido da órbita.");
                await fetchTargets();
            } else {
                toast.error("Falha ao remover o alvo.");
            }
        } catch (error) {
            toast.error("Erro ao deletar o alvo.");
        }
    };

    const handleCreateArmy = async () => {
        if (!newArmy.name.trim()) {
            toast.error("O Exército precisa de um nome.");
            return;
        }
        setIsLoading(true);
        try {
            const res = await axios.post(`${API}/api/v1/armies`, newArmy);
            if (res.data) {
                toast.success("Exército formado com sucesso!");
                setNewArmy({ name: '', color: '#00f0ff', icon: 'swords', profile_ids: [] });
                await fetchArmies();
            }
        } catch (error) {
            toast.error("Falha ao criar o Exército.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteArmy = async (id: number) => {
        if (!confirm("Atenção: Ao dissolver este exército, os alvos vinculados a ele se tornarão Órfãos. Deseja prosseguir?")) return;
        try {
            await axios.delete(`${API}/api/v1/armies/${id}`);
            toast.success("Exército dissolvido.");
            await fetchArmies();
            await fetchTargets();
        } catch (error) {
            toast.error("Falha ao dissolver Exército.");
        }
    };

    const handleToggleProfileInArmy = async (armyId: number, profileDbId: number, isCurrentlyLinked: boolean) => {
        const army = armies.find(a => a.id === armyId);
        if (!army) return;

        let newProfileIds: number[] = army.profiles.map((p: any) => p.id as number);
        if (isCurrentlyLinked) {
            newProfileIds = newProfileIds.filter(id => id !== profileDbId);
        } else {
            newProfileIds.push(profileDbId);
        }

        try {
            await axios.put(`${API}/api/v1/armies/${armyId}`, { profile_ids: newProfileIds });
            toast.success("Designação atualizada.");
            await fetchArmies();
        } catch (error) {
            toast.error("Falha ao atualizar designações.");
        }
    };

    const cancelDeleteTarget = () => {
        setTargetToDelete(null);
    };

    const handleToggleTarget = async (id: number, currentActive: boolean) => {
        try {
            const res = await fetch(`${API}/api/clipper/targets/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: !currentActive })
            });
            if (res.ok) {
                toast.success(`Alvo ${!currentActive ? 'ativado' : 'desativado'} com sucesso.`);
                await fetchTargets();
            } else {
                toast.error("Falha ao modificar o status do alvo.");
            }
        } catch (error) {
            toast.error("Erro de conexão ao modificar o alvo.");
        }
    };

    const handleForceCheckTarget = async (id: number) => {
        setIsLoading(true);
        toast.info("Iniciando varredura manual do radar...", { id: `force-${id}` });
        try {
            const res = await fetch(`${API}/api/clipper/targets/${id}/check`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                toast.success(data.message, { id: `force-${id}`, duration: 5000 });
                await fetchTargets();
            } else {
                toast.error(`Falha: ${data.detail}`, { id: `force-${id}` });
            }
        } catch (error) {
            toast.error("Erro de conexão ao forçar varredura.", { id: `force-${id}` });
        } finally {
            setIsLoading(false);
        }
    };

    // ── Queue / Esteira logic ──
    const fetchPending = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/api/clipper/jobs`);
            setItems(res.data || []);
            setCurrentIndex(0);
        } catch (err) {
            console.error('Fetch pending error:', err);
        } finally {
            setQueueLoading(false);
        }
    }, [API]);

    useEffect(() => {
        if (activeTab === 'queue') {
            fetchPending();
        }
    }, [activeTab, fetchPending]);

    // Fetch vitals for header
    useEffect(() => {
        const fetchVitals = async () => {
            try {
                const res = await axios.get(`${API}/api/v1/telemetry/vitals`);
                setVitals(res.data);
            } catch (err) {
                // Ignore silent telemetry errors in UI
            }
        };
        fetchVitals();
        const interval = setInterval(fetchVitals, 5000);
        return () => clearInterval(interval);
    }, [API]);


    // Group targets by army (instead of profile)
    const targetsByArmy = targets.reduce((acc, target) => {
        const aid = target.army_id ? String(target.army_id) : 'orphan';
        if (!acc[aid]) acc[aid] = [];
        acc[aid].push(target);
        return acc;
    }, {} as Record<string, Target[]>);

    return (
        <div className="h-full flex flex-col bg-black overflow-hidden relative">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-end gap-6 pb-2 border-b border-white/5 relative mt-6">
                <div className="absolute bottom-0 right-0 w-1/3 h-px bg-gradient-to-l from-cyan-400/50 to-transparent"></div>
                <div className="relative">
                    <h1 className="text-5xl lg:text-6xl font-bold tracking-tighter text-white font-display">
                        Vigilância do <span className="text-cyan-400 block text-3xl lg:text-4xl tracking-[0.2em] font-mono mt-2 font-normal drop-shadow-[0_0_10px_rgba(0,240,255,0.8)]">Espaço Profundo</span>
                    </h1>
                </div>
                <div className="flex flex-col items-end gap-1">
                    <div className="flex items-center gap-4 text-xs font-mono text-cyan-400/70">
                        <span className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm animate-spin-slow">memory</span>
                            CARGA_CPU: {vitals?.cpu_percent !== undefined ? `${vitals.cpu_percent.toFixed(1)}%` : '--%'}
                        </span>
                        <span className="w-px h-3 bg-white/20"></span>
                        <span className="flex items-center gap-2" title={vitals?.uptime ? `Uptime: ${vitals.uptime}` : ''}>
                            <span className="material-symbols-outlined text-sm animate-pulse">wifi_tethering</span>
                            FLUXO_REDE: {vitals ? 'ON' : '--'}
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
                <button
                    onClick={() => setActiveTab('armies')}
                    className={`px-5 py-2.5 text-xs font-mono font-bold uppercase tracking-widest rounded-lg transition-all duration-200 flex items-center gap-2 ${activeTab === 'armies'
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_-3px_rgba(0,240,255,0.3)]'
                        : 'text-slate-500 hover:text-white hover:bg-white/5 border border-transparent'
                        }`}
                >
                    <span className="material-symbols-outlined text-[18px]">swords</span>
                    Exércitos
                    {armies.length > 0 && (
                        <span className="bg-cyan-500/20 text-cyan-400 text-[10px] px-1.5 py-0.5 rounded-md">{armies.length}</span>
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

                        <div className="relative w-full max-w-4xl group">
                            <div className="absolute -inset-4 border border-cyan-400/40 rounded-3xl border-t-transparent border-l-transparent animate-spin-slow shadow-[0_0_30px_rgba(0,240,255,0.1)] pointer-events-none"></div>
                            <div className="bg-black/80 backdrop-blur-xl border border-cyan-400/60 rounded-3xl p-2 relative shadow-[0_0_50px_-10px_rgba(0,240,255,0.25)] transition-all duration-500 flex flex-col md:flex-row items-center overflow-hidden gap-2">
                                <div className="laser-sweep animate-scan-laser pointer-events-none"></div>
                                <div className="pl-6 pr-4 py-4 md:py-0 text-cyan-400 animate-pulse z-10 shrink-0">
                                    <span className="material-symbols-outlined text-4xl drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]">filter_center_focus</span>
                                </div>
                                <div className="flex-1 w-full relative z-10 flex flex-col px-2 gap-2 pb-2 md:pb-0">
                                    <input
                                        type="text"
                                        value={urlInput}
                                        onChange={(e) => setUrlInput(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && handleAddTarget()}
                                        placeholder="URL DA TWITCH (Canal ou Categoria)..."
                                        className="w-full bg-transparent border-b border-cyan-900/50 focus:border-cyan-400/80 text-white text-lg font-mono placeholder:text-cyan-400/40 focus:ring-0 py-3 tracking-wider focus:outline-none transition-colors"
                                        disabled={isLoading}
                                    />
                                    <div className="w-full max-w-[250px] flex flex-col gap-1">
                                        <select
                                            value={selectedArmyId}
                                            onChange={(e) => setSelectedArmyId(e.target.value)}
                                            className="bg-black/50 border border-cyan-900/50 text-cyan-400 text-xs font-mono uppercase rounded p-2 focus:outline-none focus:border-cyan-500 w-full"
                                            disabled={isLoading}
                                        >
                                            <option value="">[ SEM EXÉRCITO ]</option>
                                            {armies.map(a => (
                                                <option key={a.id} value={a.id}>[{a.name.toUpperCase()}]</option>
                                            ))}
                                        </select>
                                        {armies.length === 0 && (
                                            <div className="text-[9px] text-cyan-500/50 flex flex-col uppercase font-mono pl-1">
                                                <span>Nenhum exército encontrado.</span>
                                                <span onClick={() => setActiveTab('armies')} className="hover:text-cyan-400 transition-colors mt-0.5 underline decoration-cyan-900 underline-offset-2 cursor-pointer">Criar novo Exército &rarr;</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <button
                                    onClick={handleAddTarget}
                                    disabled={isLoading || !urlInput.trim()}
                                    className="z-10 w-full md:w-auto bg-cyan-400/10 hover:bg-cyan-400 hover:text-black text-cyan-400 border border-cyan-400/50 rounded-2xl px-10 py-5 mx-2 md:mr-1 md:ml-2 transition-all duration-300 flex items-center justify-center gap-2 group/btn shadow-[0_0_15px_rgba(0,240,255,0.1)] hover:shadow-[0_0_25px_rgba(0,240,255,0.6)] disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                                >
                                    {isLoading ? (
                                        <span className="material-symbols-outlined animate-spin text-lg">autorenew</span>
                                    ) : (
                                        <>
                                            <span className="font-mono font-bold tracking-widest text-lg">INICIAR</span>
                                            <span className="material-symbols-outlined group-hover/btn:translate-x-1 transition-transform text-lg text-cyan-200">my_location</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* Targets Componentized by Army */}
                    <section className="flex-1 overflow-y-auto custom-scrollbar pb-10 px-4 md:px-8">
                        {targets.length === 0 && (
                            <div className="py-20 text-center text-cyan-400/50 font-mono flex flex-col items-center gap-4">
                                <span className="material-symbols-outlined text-5xl">satellite_alt</span>
                                NENHUM ALVO DETECTADO NO RADAR
                            </div>
                        )}

                        {/* Targets Componentized by Army */}
                        <div className="w-full flex flex-col gap-12 mt-12">
                            {Object.entries(targetsByArmy).map(([armyIdStr, armyTargets]) => {
                                const isOrphan = armyIdStr === 'orphan';
                                const armyData = isOrphan ? null : armies.find(a => a.id.toString() === armyIdStr);

                                return (
                                    <div key={armyIdStr} className="flex flex-col gap-4">
                                        <div className="flex items-center gap-3 pb-2 border-b border-white/5">
                                            {isOrphan ? (
                                                <div className="w-8 h-8 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center">
                                                    <span className="material-symbols-outlined text-slate-500 text-sm">public_off</span>
                                                </div>
                                            ) : (
                                                <div className="w-8 h-8 rounded-full bg-cyan-950 border border-cyan-800 flex items-center justify-center shrink-0 overflow-hidden" style={{ borderColor: armyData?.color }}>
                                                    <span className="material-symbols-outlined text-sm" style={{ color: armyData?.color }}>{armyData?.icon || 'swords'}</span>
                                                </div>
                                            )}
                                            <h2 className="text-xl font-mono font-bold tracking-widest flex items-center gap-3">
                                                {isOrphan ? (
                                                    <span className="text-slate-400">Alvos Órfãos <span className="text-sm font-normal text-slate-600">(Sem Exército)</span></span>
                                                ) : (
                                                    <span style={{ color: armyData?.color || '#00f0ff' }}>
                                                        Exército: {armyData?.name.toUpperCase() || 'DESCONHECIDO'}
                                                    </span>
                                                )}
                                            </h2>
                                            <span className="ml-auto text-xs font-mono text-slate-500">{armyTargets.length} ALVOS</span>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                            {armyTargets.map((target) => (
                                                <div key={target.id} className={`group relative bg-[#0a0f16] border border-[#162730] hover:border-cyan-500/60 transition-all duration-300 overflow-hidden rounded-xl shadow-lg ${!target.active ? 'opacity-60 hover:opacity-100 grayscale contrast-125' : 'hover:shadow-[0_0_20px_rgba(0,240,255,0.15)]'}`}>
                                                    <div className="absolute inset-0 bg-[linear-gradient(transparent_0%,rgba(0,240,255,0.05)_50%,transparent_100%)] h-[200%] w-full -translate-y-1/2 group-hover:translate-y-0 transition-transform duration-1000 ease-in-out pointer-events-none z-20 opacity-0 group-hover:opacity-100"></div>

                                                    <div className="absolute top-0 left-0 w-full z-10 flex justify-between items-start p-3 pointer-events-none">
                                                        {target.active ? (
                                                            <div className="bg-black/80 backdrop-blur border border-red-500/50 text-red-500 px-2 py-0.5 text-[9px] font-bold font-mono uppercase flex items-center gap-1.5 shadow-[0_0_10px_rgba(255,42,42,0.3)] rounded-full">
                                                                <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-ping"></span> SINAL ATIVO
                                                            </div>
                                                        ) : (
                                                            <div className="bg-black/80 backdrop-blur border border-slate-600/50 text-slate-400 px-2 py-0.5 text-[9px] font-bold font-mono uppercase flex items-center gap-1.5 rounded-full">
                                                                <span className="w-1.5 h-1.5 bg-slate-500 rounded-full"></span> INATIVO
                                                            </div>
                                                        )}

                                                        {target.target_type === 'category' && (
                                                            <div className="bg-fuchsia-900/40 backdrop-blur border border-fuchsia-500/50 text-fuchsia-400 px-2 py-0.5 text-[9px] font-bold font-mono uppercase flex items-center gap-1 rounded-full">
                                                                <span className="material-symbols-outlined text-[10px]">category</span> CATEGORIA
                                                            </div>
                                                        )}
                                                    </div>

                                                    <div className="h-32 bg-[#06090e] border-b border-[#162730] relative flex items-center justify-center overflow-hidden">
                                                        {/* Background blur */}
                                                        {target.offline_image_url || target.profile_image_url ? (
                                                            <>
                                                                <img src={target.offline_image_url || target.profile_image_url} alt="Cover" className="absolute inset-0 w-full h-full object-cover opacity-20 blur-md scale-110" />
                                                                <div className="absolute inset-0 bg-gradient-to-t from-[#0a0f16] to-transparent"></div>
                                                            </>
                                                        ) : null}

                                                        {/* Avatar / Box Art */}
                                                        <div className={`relative z-10 ${target.target_type === 'category' ? 'w-16 h-20 rounded-md' : 'w-16 h-16 rounded-full'} border ${target.active ? 'border-cyan-400/50 shadow-[0_0_15px_rgba(0,240,255,0.3)]' : 'border-slate-700'} bg-black overflow-hidden flex items-center justify-center mt-4`}>
                                                            {target.profile_image_url ? (
                                                                <img src={target.profile_image_url} alt={target.channel_name} className="w-full h-full object-cover" />
                                                            ) : (
                                                                <span className="material-symbols-outlined text-slate-500 text-2xl">
                                                                    {target.target_type === 'category' ? 'sports_esports' : 'person'}
                                                                </span>
                                                            )}
                                                        </div>
                                                    </div>

                                                    <div className="p-4 pt-3 flex flex-col gap-3">
                                                        <div className="flex items-start justify-between gap-2">
                                                            <div className="flex-1 min-w-0">
                                                                <h4 className={`font-bold text-lg font-mono ${target.active ? 'text-white' : 'text-slate-400'} truncate`} title={target.channel_name}>
                                                                    {target.channel_name || 'Desconhecido'}
                                                                </h4>
                                                                <div className="text-cyan-500/50 text-[10px] font-mono flex items-center gap-1 uppercase tracking-wider">
                                                                    {target.target_type === 'category' ? 'Jogos/IRL' : 'Canal'}
                                                                    &bull; ID: {target.category_id || target.broadcaster_id || 'N/A'}
                                                                </div>
                                                            </div>
                                                            <button
                                                                onClick={() => handleToggleTarget(target.id, target.active)}
                                                                className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors focus:outline-none ${target.active ? 'bg-cyan-500' : 'bg-slate-700'}`}
                                                            >
                                                                <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${target.active ? 'translate-x-4' : 'translate-x-1'}`} />
                                                            </button>
                                                        </div>

                                                        <div className="bg-black/40 rounded border border-white/5 p-2 font-mono text-[9px] text-slate-400 flex flex-col gap-1.5 mt-2">
                                                            <div className="flex justify-between items-center text-cyan-400/80 mb-1 border-b border-cyan-900/40 pb-1">
                                                                <span className="font-bold flex items-center gap-1.5 tracking-widest"><span className="material-symbols-outlined text-[11px]">terminal</span> DIÁRIO DE BORDO</span>
                                                            </div>
                                                            <div className="flex justify-between"><span>CHECK:</span> <span className="text-slate-300">{target.last_checked_at ? new Date(target.last_checked_at).toLocaleTimeString('pt-BR') : 'N/A'}</span></div>
                                                            <div className="flex justify-between"><span>CLIP:</span> <span className="text-slate-300">{target.last_clip_found_at ? new Date(target.last_clip_found_at).toLocaleTimeString('pt-BR') : 'NONE'}</span></div>
                                                            <div className="flex justify-between"><span>TOTAL PROC:</span> <span className="text-cyan-400 font-bold">{target.total_clips_processed || 0}</span></div>
                                                        </div>

                                                        <div className="flex gap-2 mt-1">
                                                            <button onClick={() => requestDeleteTarget(target.id)} className="w-9 h-8 flex justify-center items-center bg-white/5 hover:bg-red-500/20 hover:text-red-500 hover:border-red-500/50 text-slate-400 rounded border border-white/10 transition-all duration-300" title="Deletar Alvo">
                                                                <span className="material-symbols-outlined text-[16px]">delete</span>
                                                            </button>
                                                            <a href={target.channel_url} target="_blank" rel="noreferrer" className={`w-9 h-8 flex justify-center items-center text-center cursor-pointer ${target.active ? 'bg-cyan-400/10 hover:bg-cyan-400/30 text-cyan-400 border-cyan-400/30 hover:shadow-[0_0_10px_rgba(0,240,255,0.1)]' : 'bg-white/5 hover:bg-white/10 text-slate-400 border-white/10'} rounded border transition-all duration-300`} title="Abrir na Twitch">
                                                                <span className="material-symbols-outlined text-[16px]">open_in_new</span>
                                                            </a>
                                                            <button onClick={() => handleForceCheckTarget(target.id)} disabled={isLoading || !target.active} className={`flex-1 h-8 flex justify-center items-center gap-1.5 cursor-pointer rounded ${target.active && !isLoading ? 'bg-emerald-500/10 hover:bg-emerald-500/30 text-emerald-400 border-emerald-500/30 hover:shadow-[0_0_10px_rgba(16,185,129,0.2)]' : 'bg-white/5 opacity-50 cursor-not-allowed text-slate-500 border-white/10'} text-[10px] font-mono uppercase tracking-wider border transition-all duration-300`} title="Forçar Varredura no Radar">
                                                                <span className={`material-symbols-outlined text-[13px] ${isLoading ? 'animate-spin' : ''}`}>radar</span> SCAN
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                </>
            )}

            {/* ═══ TAB: ESTEIRA DE CURADORIA ═══ */}
            {activeTab === 'queue' && (
                <div className="flex-1 flex flex-col items-center justify-start px-4 py-8 relative overflow-hidden">
                    {queueLoading ? (
                        <div className="text-center mt-20">
                            <div className="w-12 h-12 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                            <p className="text-slate-400 font-mono text-sm">Carregando painel de curadoria...</p>
                        </div>
                    ) : items.length === 0 ? (
                        <div className="text-center max-w-md mt-20">
                            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-slate-800/50 border border-white/5 flex items-center justify-center">
                                <span className="material-symbols-outlined text-4xl text-slate-600">memory</span>
                            </div>
                            <h2 className="text-white text-2xl font-display font-bold mb-2">Nenhum Job Processando</h2>
                            <p className="text-slate-500 font-mono text-sm">
                                O processador de clipes está ocioso. Novos jobs aparecerão aqui quando o radar encontrar novos sinais da Twitch.
                            </p>
                            <div className="mt-6 flex items-center justify-center gap-2 text-[10px] font-mono text-cyan-500/50">
                                <span className="w-1.5 h-1.5 bg-cyan-500/50 rounded-full animate-pulse"></span>
                                AGUARDANDO NOVOS EVENTOS
                            </div>
                        </div>
                    ) : (
                        <div className="w-full max-w-5xl mx-auto flex flex-col gap-6 overflow-y-auto max-h-[80vh] pr-2 custom-scrollbar pb-10">
                            {/* Header Section */}
                            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                                <div className="flex items-center gap-3">
                                    <span className="material-symbols-outlined text-cyan-500/50 text-[20px]">movie_filter</span>
                                    <h3 className="text-xl font-display font-bold text-white tracking-widest">
                                        FILA DE RENDERIZAÇÃO
                                    </h3>
                                </div>
                                <span className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] font-mono px-3 py-1 rounded">
                                    {items.length} JOBS ATIVOS
                                </span>
                            </div>

                            <div className="space-y-4">
                                {items.map((job) => (
                                    <div key={job.id} className="relative bg-[#0a0a0a] border border-white/5 rounded-xl p-5 flex flex-col md:flex-row gap-6 group hover:border-cyan-500/30 hover:bg-[#0c1218] transition-colors items-center shadow-[0_4px_20px_rgba(0,0,0,0.3)]">

                                        {/* Status Header */}
                                        <div className="w-full md:w-auto flex md:flex-col justify-between items-start gap-2 border-b md:border-b-0 md:border-r border-white/5 pb-4 md:pb-0 md:pr-6 min-w-[140px]">
                                            <div>
                                                <div className="font-mono text-[10px] text-slate-500 flex items-center gap-1.5 mb-1">
                                                    <span className="material-symbols-outlined text-[12px]">satellite_alt</span>
                                                    ID_TARGET: {job.target_id}
                                                </div>
                                                <div className="text-white font-mono text-sm font-bold">
                                                    JOB #{job.id}
                                                </div>
                                            </div>

                                            {job.status === 'completed' ? (
                                                <span className="text-[10px] font-mono px-2 py-0.5 border border-emerald-500/30 text-emerald-500 rounded bg-emerald-500/10 shrink-0">CONCLUÍDO</span>
                                            ) : job.status === 'failed' ? (
                                                <span className="text-[10px] font-mono px-2 py-0.5 border border-red-500/30 text-red-500 rounded bg-red-500/10 shrink-0">FALHA</span>
                                            ) : job.status === 'pending' ? (
                                                <span className="text-[10px] font-mono px-2 py-0.5 border border-slate-500/30 text-slate-400 rounded bg-slate-500/10 shrink-0">AGUARDANDO</span>
                                            ) : (
                                                <span className="text-[10px] font-mono px-2 py-0.5 border border-cyan-500/30 text-cyan-500 rounded bg-cyan-500/10 flex items-center gap-1.5 shrink-0 shadow-[0_0_10px_rgba(0,240,255,0.1)]">
                                                    <span className="size-1.5 rounded-full bg-cyan-500 animate-pulse"></span>
                                                    {job.status.toUpperCase()}
                                                </span>
                                            )}
                                        </div>

                                        {/* Main Content */}
                                        <div className="flex-1 w-full">
                                            <div className="flex justify-between items-end mb-2">
                                                <h4 className="text-cyan-400/80 font-mono text-[11px] uppercase tracking-wider">{job.current_step || 'Iniciando pipeline...'}</h4>
                                                <span className="text-xs font-mono text-slate-400">{job.progress_pct}%</span>
                                            </div>

                                            {/* Progress Bar */}
                                            <div className="w-full bg-[#151515] rounded-full h-2 mb-3 border border-[#222]">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-1000 ${job.status === 'failed' ? 'bg-red-500 shadow-[0_0_8px_#ef4444]' : job.status === 'completed' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-cyan-500 shadow-[0_0_8px_#06b6d4]'}`}
                                                    style={{ width: `${job.progress_pct}%` }}
                                                ></div>
                                            </div>

                                            {job.error_message && (
                                                <div className="mt-2 text-[10px] font-mono text-red-400 bg-red-500/5 border border-red-500/20 p-2 rounded break-all whitespace-pre-wrap" title={job.error_message}>
                                                    [ERRO] {job.error_message}
                                                </div>
                                            )}
                                        </div>

                                        {/* Timestamps */}
                                        <div className="w-full md:w-auto flex flex-row md:flex-col justify-between items-end md:items-end gap-1 border-t md:border-t-0 md:border-l border-white/5 pt-4 md:pt-0 md:pl-6 text-[9px] font-mono text-slate-600 min-w-[120px]">
                                            <div className="flex flex-col items-start md:items-end">
                                                <span>Iníciado em</span>
                                                <span className="text-slate-400">{new Date(job.created_at).toLocaleString('pt-BR')}</span>
                                            </div>
                                            <div className="flex flex-col items-start md:items-end">
                                                <span>Último ping</span>
                                                <span className="text-slate-500">{new Date(job.updated_at).toLocaleTimeString('pt-BR')}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ═══ TAB: EXÉRCITOS ═══ */}
            {activeTab === 'armies' && (
                <div className="flex-1 flex flex-col gap-8 px-4 md:px-8 py-8 overflow-y-auto custom-scrollbar">

                    {/* Header / Intro */}
                    <div className="bg-cyan-950/20 border border-cyan-800/50 rounded-2xl p-6 relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,240,255,0.1),transparent_70%)] pointer-events-none"></div>
                        <div className="relative z-10 flex-1">
                            <h2 className="text-2xl font-display font-bold text-white tracking-widest flex items-center gap-3 mb-2">
                                <span className="material-symbols-outlined text-cyan-400">swords</span>
                                QUARTEL GENERAL
                            </h2>
                            <p className="text-slate-400 font-mono text-sm max-w-2xl">
                                Agrupe seus alvos da Twitch em "Exércitos". Mapeie e delegue as contas do TikTok/YouTube (Perfis) que receberão as edições processadas de um determinado Exército.
                            </p>
                        </div>
                    </div>

                    {/* Dashboard Grid */}
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

                        {/* Column 1: Create Army Form */}
                        <div className="xl:col-span-1 bg-[#0a0a0a] border border-white/5 rounded-2xl p-6 h-fit sticky top-8 shadow-2xl">
                            <h3 className="font-mono text-sm font-bold tracking-widest text-cyan-400 mb-6 flex items-center gap-2 border-b border-white/5 pb-2">
                                <span className="material-symbols-outlined text-[16px]">add_circle</span> NOVA FORMAÇÃO
                            </h3>

                            <div className="flex flex-col gap-5">
                                <div>
                                    <label className="text-[10px] text-slate-500 font-mono uppercase tracking-wider mb-1.5 block">Codinome do Exército</label>
                                    <input
                                        type="text"
                                        maxLength={30}
                                        value={newArmy.name}
                                        onChange={(e) => setNewArmy({ ...newArmy, name: e.target.value })}
                                        className="w-full bg-black/40 border border-cyan-900/50 focus:border-cyan-400 text-white font-mono text-sm p-3 rounded-xl focus:outline-none transition-colors"
                                        placeholder="Ex: Tropa do Rato"
                                    />
                                </div>

                                <div>
                                    <label className="text-[10px] text-slate-500 font-mono uppercase tracking-wider mb-1.5 block">Símbolo (Material Icon)</label>
                                    <div className="flex flex-wrap gap-2">
                                        {['swords', 'bolt', 'flag', 'shield', 'visibility', 'skull', 'star', 'diamond', 'rocket', 'local_fire_department'].map(icon => (
                                            <button
                                                key={icon}
                                                type="button"
                                                onClick={() => setNewArmy({ ...newArmy, icon })}
                                                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${newArmy.icon === icon ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 shadow-[0_0_10px_rgba(0,240,255,0.3)]' : 'bg-black/40 text-slate-400 border border-white/5 hover:border-cyan-900/50 hover:text-cyan-200'}`}
                                            >
                                                <span className="material-symbols-outlined text-[20px]">{icon}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <label className="text-[10px] text-slate-500 font-mono uppercase tracking-wider mb-1.5 block">Estandarte (Cor)</label>
                                    <div className="flex items-center gap-3">
                                        <input
                                            type="color"
                                            value={newArmy.color}
                                            onChange={(e) => setNewArmy({ ...newArmy, color: e.target.value })}
                                            className="h-10 w-12 rounded cursor-pointer bg-transparent border-0 p-0"
                                        />
                                        <input
                                            type="text"
                                            value={newArmy.color}
                                            onChange={(e) => setNewArmy({ ...newArmy, color: e.target.value })}
                                            className="flex-1 bg-black/40 border border-cyan-900/50 focus:border-cyan-400 text-white font-mono text-sm p-2 rounded-lg focus:outline-none transition-colors uppercase"
                                        />
                                    </div>
                                </div>

                                <button
                                    onClick={handleCreateArmy}
                                    disabled={isLoading || !newArmy.name.trim()}
                                    className="w-full mt-4 bg-cyan-500/10 hover:bg-cyan-500 hover:text-black text-cyan-400 border border-cyan-500/50 p-3 rounded-xl font-bold font-mono tracking-widest transition-all disabled:opacity-50 flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(0,240,255,0.1)] hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]"
                                >
                                    <span className="material-symbols-outlined text-[18px]">gavel</span>
                                    FORMAR EXÉRCITO
                                </button>
                            </div>
                        </div>

                        {/* Column 2: Armies List */}
                        <div className="xl:col-span-2 flex flex-col gap-6">
                            {armies.length === 0 ? (
                                <div className="text-center py-16 border border-white/5 border-dashed rounded-2xl bg-black/20">
                                    <span className="material-symbols-outlined text-5xl text-slate-700 mb-3">account_tree</span>
                                    <h4 className="text-white font-display mb-1 text-lg">Exércitos Ausentes</h4>
                                    <p className="text-slate-500 text-sm font-mono">Comece criando sua primeira formação ao lado.</p>
                                </div>
                            ) : (
                                armies.map((army) => (
                                    <div key={army.id} className="bg-[#0a0a0a] border border-white/5 rounded-2xl overflow-hidden hover:border-white/10 transition-colors shadow-lg">
                                        <div className="p-5 border-b border-white/5 flex items-center justify-between" style={{ backgroundColor: `${army.color}08` }}>
                                            <div className="flex items-center gap-4">
                                                <div className="w-12 h-12 rounded-xl flex items-center justify-center shadow-inner border border-white/10" style={{ backgroundColor: `${army.color}20`, color: army.color }}>
                                                    <span className="material-symbols-outlined text-2xl">{army.icon || 'swords'}</span>
                                                </div>
                                                <div>
                                                    <h3 className="font-display font-bold text-xl text-white tracking-widest flex items-center gap-2">
                                                        {army.name.toUpperCase()}
                                                    </h3>
                                                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                                                        <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: army.color }}></span>
                                                        {army.profiles.length} Perfis Designados
                                                    </div>
                                                </div>
                                            </div>

                                            <button
                                                onClick={() => handleDeleteArmy(army.id)}
                                                className="w-10 h-10 rounded-full bg-red-500/10 text-red-500 border border-transparent hover:border-red-500/30 flex items-center justify-center transition-all"
                                                title="Dissolver Exército"
                                            >
                                                <span className="material-symbols-outlined text-[18px]">group_remove</span>
                                            </button>
                                        </div>

                                        <div className="p-5 flex flex-col gap-4">
                                            <div className="text-[10px] font-mono text-cyan-500/70 border-b border-white/5 pb-2 uppercase tracking-widest">
                                                Atribuição de Perfis <span className="text-slate-500">(Destino das Edições)</span>
                                            </div>

                                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                                                {profiles.map(profile => {
                                                    const profileDbId = profile.db_id || -1;
                                                    const isLinked = army.profiles.some((p: any) => p.id === profileDbId);
                                                    return (
                                                        <div
                                                            key={profile.id}
                                                            onClick={() => handleToggleProfileInArmy(army.id, profileDbId, isLinked)}
                                                            className={`cursor-pointer p-3 rounded-xl border transition-all flex items-center gap-3 ${isLinked ? 'bg-cyan-500/10 border-cyan-500/40 opacity-100' : 'bg-white/5 border-transparent hover:border-white/10 opacity-60 hover:opacity-100'}`}
                                                        >
                                                            <div className="w-8 h-8 rounded-full overflow-hidden bg-black shrink-0 relative border border-white/10">
                                                                {profile.avatar_url ? (
                                                                    <img src={profile.avatar_url} alt="Profile" className="w-full h-full object-cover" />
                                                                ) : (
                                                                    <div className="w-full h-full flex items-center justify-center text-slate-500">
                                                                        <span className="material-symbols-outlined text-sm">person</span>
                                                                    </div>
                                                                )}
                                                                {isLinked && (
                                                                    <div className="absolute inset-0 bg-cyan-500/20 flex items-center justify-center">
                                                                        <span className="material-symbols-outlined text-white text-[16px] drop-shadow-md">check</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <div className={`font-mono text-xs font-bold truncate ${isLinked ? 'text-cyan-400' : 'text-slate-300'}`}>
                                                                    {profile.username || profile.label}
                                                                </div>
                                                                <div className="text-[9px] font-mono text-slate-500 truncate">
                                                                    @{profile.slug}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )
                                                })}
                                                {profiles.length === 0 && (
                                                    <div className="col-span-full text-[10px] font-mono text-slate-500 bg-white/5 p-4 rounded-xl text-center">
                                                        Nenhum Perfil no Banco de Dados. Importe no Central de Comando primeiro.
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
            {/* Delete Confirmation Modal */}
            {targetToDelete !== null && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-red-500/30 p-6 max-w-md w-full shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-red-900"></div>
                        <div className="flex items-start gap-4 mb-6">
                            <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
                                <span className="material-symbols-outlined text-red-400 text-xl">warning</span>
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white font-display mb-1">Confirmar Exclusão</h3>
                                <p className="text-slate-400 text-sm">
                                    Tem certeza que deseja remover este alvo da órbita do radar? Esta ação não desligará vídeos já baixados, mas impedirá novas buscas.
                                </p>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 font-mono text-xs uppercase tracking-wider">
                            <button
                                onClick={cancelDeleteTarget}
                                className="px-4 py-2 border border-white/10 text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={confirmDeleteTarget}
                                className="px-4 py-2 bg-red-500/20 border border-red-500/50 text-red-400 hover:bg-red-500 hover:text-white transition-colors"
                            >
                                Remover Alvo
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
