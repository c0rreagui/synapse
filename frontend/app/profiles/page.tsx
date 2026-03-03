'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import Link from 'next/link';
// // import Sidebar from '../components/Sidebar';
import { TikTokProfile } from '../types';
import useWebSocket from '../hooks/useWebSocket';
import {
    ArrowLeftIcon, CheckCircleIcon, PlusIcon, TrashIcon, UserGroupIcon, ArrowPathIcon, ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import clsx from 'clsx';
import Modal from '../components/Modal';
import ProfileRepairModal from '../components/ProfileRepairModal'; // [SYN-UX] New Import

import { getApiUrl } from '../utils/apiClient';

const API_BASE = `${getApiUrl()}/api/v1`;

export default function ProfilesPage() {
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [showImportModal, setShowImportModal] = useState(false);
    const [importLabel, setImportLabel] = useState('');
    const [importCookies, setImportCookies] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [refreshingProfiles, setRefreshingProfiles] = useState<Record<string, boolean>>({});
    const [refreshErrors, setRefreshErrors] = useState<Record<string, string | null>>({});
    const [isRefreshingAll, setIsRefreshingAll] = useState(false);

    // BULK ACTIONS STATE
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    // UNDO PATTERN STATE
    const [pendingDeletes, setPendingDeletes] = useState<Set<string>>(new Set());
    const [deleteConfirmationId, setDeleteConfirmationId] = useState<string | null>(null);
    const deleteTimers = useRef<Record<string, NodeJS.Timeout>>({});

    // ERROR MODAL STATE
    const [viewerImage, setViewerImage] = useState<string | null>(null);

    // IMPORT STATE EXTENDED
    const [importUsername, setImportUsername] = useState('');
    const [importAvatar, setImportAvatar] = useState('');
    const [validatingCookies, setValidatingCookies] = useState(false);

    // [SYN-UX] Repair Modal State (Replaces old manual/auto states)
    const [repairProfile, setRepairProfile] = useState<TikTokProfile | null>(null);

    // CONFIRM MODAL STATE (Missing in original file but used in render? Added for safety)
    const [confirmModal, setConfirmModal] = useState<{
        isOpen: boolean;
        title: string;
        type: 'delete' | 'success' | 'warning';
        onConfirm: () => void;
        isLoading?: boolean;
    }>({ isOpen: false, title: '', type: 'success', onConfirm: () => { }, isLoading: false });

    // HELPERS
    const getHealthStatus = (profile: TikTokProfile) => {
        // If we have a screenshot, it implies an error happened recently
        if (profile.last_error_screenshot) return 'error';
        if (!profile.session_valid) return 'expired';
        if (profile.status === 'inactive') return 'inactive';
        return 'healthy';
    };

    const handleSelect = (id: string) => {
        const newSet = new Set(selectedIds);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setSelectedIds(newSet);
    };

    const handleSelectAll = () => {
        if (selectedIds.size === profiles.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(profiles.map(p => p.id)));
        }
    };

    const handleDeleteRequest = (id: string) => {
        setPendingDeletes(prev => {
            const newSet = new Set(prev);
            newSet.add(id);
            return newSet;
        });

        // 3. Start Timer for permanent deletion
        const timer = setTimeout(async () => {
            try {
                const res = await fetch(`${API_BASE}/profiles/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    setProfiles(prev => prev.filter(p => p.id !== id));

                    // Remove from selection if selected
                    setSelectedIds(prev => {
                        if (prev.has(id)) {
                            const newSet = new Set(prev);
                            newSet.delete(id);
                            return newSet;
                        }
                        return prev;
                    });
                } else {
                    const err = await res.json().catch(() => ({ detail: res.statusText }));
                    console.error("Delete failed:", err);
                    toast.error('Falha ao excluir', {
                        description: err.detail || 'Erro desconhecido'
                    });
                }
            } catch (e) {
                console.error("Delete failed", e);
                toast.error('Erro de conexao', {
                    description: 'Falha ao excluir perfil'
                });
            }

            // Remove from pending list (cleanup)
            setPendingDeletes(prev => {
                const newSet = new Set(prev);
                newSet.delete(id);
                return newSet;
            });

            // Cleanup timer ref
            delete deleteTimers.current[id];
        }, 8000);

        deleteTimers.current[id] = timer;
    };

    // Triggered by Trash Icon
    const promptDelete = (id: string) => {
        setDeleteConfirmationId(id);
    };

    // Triggered by Modal Confirm
    const confirmDelete = () => {
        if (deleteConfirmationId) {
            handleDeleteRequest(deleteConfirmationId);
            setDeleteConfirmationId(null);
        }
    };

    const handleUndo = (id: string) => {
        if (deleteTimers.current[id]) {
            clearTimeout(deleteTimers.current[id]);
            delete deleteTimers.current[id];
        }
        setPendingDeletes(prev => {
            const newSet = new Set(prev);
            newSet.delete(id);
            return newSet;
        });
    };

    async function fetchProfiles() {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/profiles/list`);
            if (!res.ok) throw new Error('Falha ao carregar perfis');
            setProfiles(await res.json());
        } catch (err) {
            console.error(err);
            setError('Não foi possível conectar ao servidor. Verifique se o backend está rodando.');
        }
        setLoading(false);
    }

    useWebSocket({
        onProfileChange: (updatedProfile) => {
            setProfiles(prev => {
                const idx = prev.findIndex(p => p.id === updatedProfile.id);
                if (idx === -1) return [...prev, updatedProfile];
                const newArr = [...prev];
                newArr[idx] = updatedProfile;
                return newArr;
            });
        }
    });

    useEffect(() => {
        fetchProfiles();
    }, []);

    const handleValidateCookies = async () => {
        if (!importCookies) return;
        setValidatingCookies(true);
        try {
            // Basic JSON check
            JSON.parse(importCookies);

            const res = await fetch(`${API_BASE}/profiles/validate-cookies`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookies: importCookies })
            });

            const data = await res.json();

            if (data.valid) {
                if (data.username) setImportUsername(data.username);
                if (data.avatar_url) setImportAvatar(data.avatar_url);
                if (!importLabel && data.username) setImportLabel(data.username); // Auto-set label too if empty
                toast.success('Cookies validos!', {
                    description: 'Dados preenchidos automaticamente'
                });
            } else {
                toast.error('Erro na validacao', {
                    description: data.error || 'Sessao invalida'
                });
            }
        } catch (e) {
            console.error(e);
            toast.error('Erro ao validar', {
                description: 'JSON invalido ou falha na conexao'
            });
        }
        setValidatingCookies(false);
    };

    const handleImport = async () => {
        // Label is now optional
        if (!importCookies) return;

        try {
            // Validate JSON basics
            JSON.parse(importCookies);

            const res = await fetch(`${API_BASE}/profiles/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    label: importLabel,
                    cookies: importCookies,
                    username: importUsername, // New field 
                    avatar_url: importAvatar    // New field
                })
            });

            if (res.ok) {
                setShowImportModal(false);
                setImportLabel('');
                setImportCookies('');
                setImportUsername('');
                setImportAvatar('');
                fetchProfiles(); // Refresh list
            } else {
                const err = await res.json();
                toast.error('Erro ao importar', {
                    description: err.detail || 'Falha na importacao'
                });
            }
        } catch (e) {
            console.error(e);
            toast.error('Erro de validacao', {
                description: 'JSON invalido ou erro de conexao'
            });
        }
    };

    const handleRefreshAvatar = async (profileId: string) => {
        setRefreshingProfiles(prev => ({ ...prev, [profileId]: true }));
        setRefreshErrors(prev => ({ ...prev, [profileId]: null })); // Clear errors

        try {
            const res = await fetch(`${API_BASE}/profiles/refresh-avatar/${profileId}`, { method: 'POST' });
            const data = await res.json().catch(() => ({}));

            if (res.ok) {
                // Success - the WebSocket should handle the update, but we refetch to be sure
                fetchProfiles();
            } else {
                let errorMessage = data.detail || "Falha na comunicação com o TikTok";

                // Friendly error mapping
                if (errorMessage.includes("Session Expired")) {
                    errorMessage = "Sessão Expirada. Renove os cookies.";
                } else if (errorMessage.includes("Target page, context or browser has been closed")) {
                    errorMessage = "Navegador fechou. Tente novamente.";
                }

                setRefreshErrors(prev => ({ ...prev, [profileId]: errorMessage }));
            }
        } catch (e) {
            setRefreshErrors(prev => ({ ...prev, [profileId]: "Erro de conexão com o Synapse." }));
        }
        setRefreshingProfiles(prev => ({ ...prev, [profileId]: false }));
    };

    const getProfileIcon = (id: string, customIcon?: string) => {
        if (!id) return '👤';
        if (customIcon && customIcon !== "👤") return customIcon;
        if (id.includes('01')) return '✂️';
        if (id.includes('02')) return '🔥';
        return '👤';
    };

    // [SYN-UX] Repair Session Handler - Removed manual logic in favor of ProfileRepairModal
    // New simplified handler (although direct setter can be used too)
    const handleOpenRepair = (profile: TikTokProfile) => {
        setRepairProfile(profile);
    };

    return (
        <>


            {/* UNDO TOAST CONTAINER */}
            <div className="fixed bottom-8 right-8 z-50 flex flex-col gap-2 pointer-events-none">
                {Array.from(pendingDeletes).map(id => {
                    const profile = profiles.find(p => p.id === id);
                    if (!profile) return null;
                    return (
                        <div key={id} className="bg-[#161b22] border border-white/10 p-4 rounded-xl shadow-2xl flex items-center gap-4 animate-in slide-in-from-right duration-300 pointer-events-auto">
                            <div className="flex flex-col">
                                <span className="text-sm font-bold text-white">Perfil excluído</span>
                                <span className="text-xs text-gray-500">{profile.label}</span>
                            </div>
                            <button
                                onClick={() => handleUndo(id)}
                                className="px-3 py-1.5 rounded bg-synapse-primary/20 text-synapse-primary text-xs font-bold hover:bg-synapse-primary/30 transition-colors"
                            >
                                DESFAZER
                            </button>
                        </div>
                    );
                })}
            </div>

            <header className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <Link href="/">
                        <div className="w-10 h-10 rounded-lg bg-[#1c2128] border border-white/10 flex items-center justify-center cursor-pointer hover:border-synapse-primary/50 transition-colors group">
                            <ArrowLeftIcon className="w-5 h-5 text-gray-400 group-hover:text-synapse-primary" />
                        </div>
                    </Link>
                    <div>
                        <h2 className="text-2xl font-bold text-white m-0">Perfis TikTok</h2>
                        <p className="text-sm text-gray-500 m-0">Gerenciar sessões de upload</p>
                    </div>
                </div>

                <div className="flex gap-3">
                    <NeonButton
                        variant="ghost"
                        onClick={handleSelectAll}
                        className="text-xs"
                    >
                        {selectedIds.size === profiles.length && profiles.length > 0 ? 'Desmarcar Todos' : 'Selecionar Todos'}
                    </NeonButton>
                    <NeonButton
                        variant="ghost"
                        onClick={async () => {
                            setConfirmModal({
                                isOpen: true,
                                title: "Atualizar todos os perfis sequencialmente?",
                                type: 'success',
                                isLoading: false,
                                onConfirm: async () => {
                                    setConfirmModal(prev => ({ ...prev, isLoading: true }));
                                    setIsRefreshingAll(true);
                                    try {
                                        for (const p of profiles) {
                                            await handleRefreshAvatar(p.id);
                                        }
                                        toast.success('Todos os perfis atualizados!');
                                    } finally {
                                        setIsRefreshingAll(false);
                                        setConfirmModal(prev => ({ ...prev, isOpen: false, isLoading: false }));
                                    }
                                }
                            });
                        }}
                        disabled={isRefreshingAll || Object.values(refreshingProfiles).some(v => v)}
                        className="text-xs"
                    >
                        <ArrowPathIcon className={`w-4 h-4 ${isRefreshingAll ? 'animate-spin' : ''}`} />
                        {isRefreshingAll ? 'Atualizando...' : 'Refresh All'}
                    </NeonButton>
                </div>
            </header>

            {error && (
                <StitchCard className="p-4 mb-6 !bg-red-500/10 !border-red-500/30 text-red-400">
                    {error}
                </StitchCard>
            )}

            <div className="text-center mb-16 relative">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[200px] bg-synapse-primary/10 blur-[80px] rounded-full -z-10"></div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1a363a]/30 border border-synapse-primary/20 backdrop-blur-sm text-synapse-primary text-[10px] font-mono tracking-[0.2em] uppercase mb-4">
                    <span className="w-1.5 h-1.5 rounded-full bg-synapse-primary animate-pulse"></span>
                    Topologia de Contas
                </div>
                <h1 className="text-4xl md:text-6xl font-bold text-white tracking-tighter uppercase mb-2">Node Wall</h1>
                <p className="text-slate-500 font-mono text-xs tracking-widest">Matriz de Distribuição • {profiles.length} Nodes</p>
            </div>

            {/* Profiles Main Grid Structure - CSS inside styles/globals.css is needed (hex-cell, hex-border, etc.) */}
            <div className="flex flex-wrap w-full justify-center items-center max-w-[1200px] mx-auto relative pb-24">

                {/* Using a flex wrap layout manually creating "rows" is complex dynamically without strict math, 
                    we can adapt it to a standard grid that mimics the flex wrap offsets using negative margins in mapping 
                    but the Stitch design uses flex-wrap with negative top margins.
                */}

                {loading ? (
                    <p className="text-gray-500 col-span-full text-center py-12">Carregando perfis...</p>
                ) : profiles.length > 0 ? (
                    <div className="flex flex-wrap justify-center w-full gap-x-5 gap-y-5">
                        {profiles.map((profile, i) => {
                            if (pendingDeletes.has(profile.id)) return null;
                            const health = getHealthStatus(profile);
                            const isSelected = selectedIds.has(profile.id);
                            const refreshError = refreshErrors[profile.id];
                            const isRefreshing = refreshingProfiles[profile.id];

                            return (
                                <div key={i} className={clsx(
                                    "group relative w-[300px] h-[340px] m-2 transition-all duration-400 flex justify-center items-center",
                                    "clip-path-hex bg-[#0a1114]/40 backdrop-blur-md hover:z-20 hover:scale-105 hover:bg-[#0f1a1d]/60",
                                    isSelected ? "shadow-[0_0_20px_rgba(7,182,213,0.4)] bg-[#0f1a1d]/60 scale-105" : "",
                                )}
                                    onClick={(e) => {
                                        // only trigger auto select if not clicking buttons inside
                                        const target = e.target as HTMLElement;
                                        if (!target.closest('button') && !target.closest('input')) {
                                            handleSelect(profile.id);
                                        }
                                    }}
                                >

                                    <div className="absolute inset-0 bg-gradient-to-b from-synapse-primary/30 to-synapse-primary/5 clip-path-hex z-0 p-[1px]">
                                        <div className="bg-[#050b0d] w-full h-full clip-path-hex relative flex flex-col">

                                            {/* Background Image / Overlay */}
                                            <div className="absolute inset-0 bg-cover bg-center opacity-40 group-hover:opacity-60 transition-opacity duration-500"
                                                style={{ backgroundImage: profile.avatar_url ? `url('${profile.avatar_url}')` : 'none' }}></div>
                                            <div className="absolute inset-0 bg-gradient-to-t from-[#030608] via-[#030608]/80 to-transparent"></div>

                                            {/* CRT Scanline */}
                                            <div className="absolute top-0 left-0 w-full h-1 bg-synapse-primary/50 shadow-[0_0_10px_rgba(7,182,213,0.8)] opacity-50 animate-[scan_4s_linear_infinite] z-10 pointer-events-none"></div>

                                            {/* Error OVERLAY */}
                                            {refreshError && (
                                                <div className="absolute inset-0 z-30 bg-black/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center animate-in fade-in zoom-in border-4 border-red-500/30 clip-path-hex">
                                                    <ExclamationTriangleIcon className="w-8 h-8 text-red-500 mb-3 animate-pulse" />
                                                    <p className="text-xs text-white font-bold mb-1 uppercase tracking-wider">Falha</p>
                                                    <p className="text-[10px] text-red-300 mb-4 leading-tight opacity-90 font-mono bg-red-900/20 p-2 rounded">{refreshError}</p>

                                                    <div className="flex gap-2 flex-col">
                                                        <button onClick={(e) => { e.stopPropagation(); setRefreshErrors(prev => ({ ...prev, [profile.id]: null })); }} className="px-4 py-2 bg-white/10 hover:bg-white/20 text-[10px] text-white font-bold transition-all border border-white/5">
                                                            FECHAR
                                                        </button>
                                                        {refreshError.includes("cookies") && (
                                                            <button onClick={(e) => { e.stopPropagation(); setRepairProfile(profile); }} className="px-4 py-2 bg-amber-500/20 text-amber-500 hover:bg-amber-500/30 text-[10px] font-bold border border-amber-500/50">
                                                                RENOVAR
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Updating Overlay */}
                                            {isRefreshing && (
                                                <div className="absolute inset-0 z-20 bg-black/80 flex flex-col items-center justify-center clip-path-hex">
                                                    <ArrowPathIcon className="w-8 h-8 text-synapse-primary animate-spin mb-3" />
                                                    <p className="text-[10px] font-bold text-white tracking-[0.2em] animate-pulse">UPDATING</p>
                                                </div>
                                            )}

                                            <div className="relative z-10 w-full h-full flex flex-col justify-between p-6 pt-10 pb-12">

                                                {/* Header Status Row */}
                                                <div className="flex justify-between items-start">
                                                    <div className={clsx(
                                                        "bg-[#0a1114]/80 backdrop-blur border px-2 py-1 rounded text-[10px] font-mono",
                                                        health === 'healthy' ? "border-synapse-primary text-synapse-primary" :
                                                            health === 'expired' || health === 'error' ? "border-red-500/30 text-red-500" :
                                                                "border-gray-500/50 text-gray-500"
                                                    )}>
                                                        {health === 'healthy' ? `ND-${profile.id.slice(0, 4).toUpperCase()}` :
                                                            health === 'inactive' ? 'INATIVO' : 'ERR:404'}
                                                    </div>

                                                    {/* Select Checkbox */}
                                                    <input
                                                        type="checkbox"
                                                        checked={isSelected}
                                                        onChange={() => handleSelect(profile.id)}
                                                        className="w-4 h-4 rounded border-synapse-primary bg-black/50 text-synapse-primary focus:ring-synapse-primary cursor-pointer accent-synapse-primary z-50 absolute right-6 top-10"
                                                    />

                                                    {health === 'healthy' ? (
                                                        <span className="material-symbols-outlined text-white/50 text-xl"></span>
                                                    ) : (
                                                        <span className="material-symbols-outlined text-red-500/80 text-xl animate-pulse"></span>
                                                    )}
                                                </div>

                                                <div className="flex flex-col items-center text-center">
                                                    <div className={clsx(
                                                        "size-12 mb-3 bg-black/50 rounded-lg flex items-center justify-center border shadow-[0_0_15px_rgba(0,0,0,0.3)]",
                                                        health === 'healthy' ? "border-synapse-primary/30 shadow-[0_0_15px_rgba(7,182,213,0.3)]" : "border-red-500/50 shadow-[0_0_15px_rgba(255,42,42,0.3)]"
                                                    )}>
                                                        <span className="text-2xl">{getProfileIcon(profile.id, profile.icon)}</span>
                                                    </div>

                                                    <h3 className="text-lg font-bold text-white tracking-tight truncate w-full max-w-[140px] uppercase">{profile.label}</h3>
                                                    {profile.username && <p className="text-[10px] font-mono text-synapse-primary/70 -mt-1 tracking-widest">@{profile.username}</p>}

                                                    <div className="w-full h-px bg-white/10 my-3"></div>

                                                    <div className="flex justify-between w-full text-[9px] font-mono text-slate-400">
                                                        <span>STATUS</span>
                                                        <span className={health === 'healthy' ? "text-[#00ff9d]" : "text-red-500"}>
                                                            {health === 'healthy' ? "OPTIMAL" : "FAILED"}
                                                        </span>
                                                    </div>

                                                    <div className="flex justify-between w-full text-[9px] font-mono text-slate-400 mt-1 relative z-50">
                                                        <span>ACTIONS</span>
                                                        <div className="flex gap-2">
                                                            {(health === 'error' || health === 'expired' || health === 'inactive') ? (
                                                                <button onClick={(e) => { e.stopPropagation(); setRepairProfile(profile); }} className="text-amber-500 hover:text-amber-400 transition-colors uppercase font-bold tracking-wider">Reparar</button>
                                                            ) : (
                                                                <button onClick={(e) => { e.stopPropagation(); handleRefreshAvatar(profile.id); }} className="text-synapse-primary hover:text-white transition-colors uppercase font-bold tracking-wider">Sync</button>
                                                            )}
                                                            <button onClick={(e) => { e.stopPropagation(); promptDelete(profile.id); }} className="text-red-500 hover:text-white transition-colors uppercase font-bold tracking-wider ml-2">Del</button>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-32 h-1 bg-[#1a363a] rounded-full overflow-hidden">
                                                    <div className={clsx(
                                                        "h-full w-[90%]",
                                                        health === 'healthy' ? "bg-[#00ff9d] shadow-[0_0_8px_#00ff9d]" : "bg-red-500 shadow-[0_0_8px_#ff2a2a] w-[10%]"
                                                    )}></div>
                                                </div>

                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )
                        })}

                        {/* Add Profile Hex */}
                        <div className="group relative w-[300px] h-[340px] m-2 transition-all duration-400 flex justify-center items-center z-10 cursor-pointer"
                            onClick={() => {
                                setImportLabel('');
                                setImportCookies('');
                                setImportUsername('');
                                setImportAvatar('');
                                setShowImportModal(true);
                            }}
                        >
                            <div className="absolute inset-0 bg-transparent border border-dashed border-synapse-primary/50 group-hover:border-synapse-primary transition-colors duration-300 clip-path-hex z-0 p-[1px]">
                                <div className="bg-[#0a1114]/90 w-full h-full clip-path-hex relative flex flex-col items-center justify-center overflow-hidden">
                                    <div className="absolute inset-0 bg-synapse-primary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 animate-pulse"></div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-[80%] h-[80%] border border-synapse-primary/20 rounded-full animate-[spin_10s_linear_infinite]"></div>
                                    </div>
                                    <div className="relative z-10 flex flex-col items-center">
                                        <div className="size-16 rounded-full border-2 border-synapse-primary/50 bg-[#030608] flex items-center justify-center group-hover:scale-110 transition-transform duration-300 mb-4 shadow-[0_0_20px_rgba(7,182,213,0.4)]">
                                            <span className="material-symbols-outlined text-3xl text-synapse-primary">satellite_alt</span>
                                        </div>
                                        <h3 className="text-xl font-bold text-white uppercase tracking-wider group-hover:text-synapse-primary transition-colors">Deploy</h3>
                                        <p className="text-[10px] text-synapse-primary font-mono mt-1 opacity-70">INIT_NEW_NODE</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                ) : (
                    <div className="col-span-full flex flex-col items-center justify-center py-20 pointer-events-auto">
                        <div className="size-24 rounded-full border-4 border-dashed border-synapse-primary/20 flex items-center justify-center mb-6">
                            <span className="material-symbols-outlined text-5xl text-synapse-primary/50">hub</span>
                        </div>
                        <h2 className="text-2xl text-white font-bold tracking-widest uppercase">Nenhum Nó Ativo</h2>
                        <p className="text-xs text-synapse-primary/60 font-mono mt-2 mb-8">INIT_NEW_NODE_SEQ para começar</p>

                        <NeonButton variant="primary" onClick={() => setShowImportModal(true)}>
                            Deploy Novo Nó
                        </NeonButton>
                    </div>
                )}

                {/* Floating Bulk Actions Bar */}
                <div className={clsx(
                    "fixed bottom-8 left-1/2 -translate-x-1/2 z-40 transition-all duration-300 transform",
                    selectedIds.size > 0 ? "translate-y-0 opacity-100" : "translate-y-20 opacity-0 pointer-events-none"
                )}>
                    <div className="bg-[#161b22] border border-synapse-emerald/30 shadow-[0_0_30px_rgba(16,185,129,0.1)] rounded-full px-6 py-3 flex items-center gap-6">
                        <span className="text-sm font-medium text-white">
                            <span className="text-synapse-emerald font-bold">{selectedIds.size}</span> selecionado(s)
                        </span>

                        <div className="h-6 w-px bg-white/10" />

                        <div className="flex items-center gap-2">
                            <button
                                onClick={async () => {
                                    setIsRefreshingAll(true);
                                    try {
                                        for (const id of Array.from(selectedIds)) {
                                            await handleRefreshAvatar(id);
                                        }
                                        setSelectedIds(new Set());
                                    } finally {
                                        setIsRefreshingAll(false);
                                    }
                                }}
                                disabled={isRefreshingAll}
                                className={`p-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors ${isRefreshingAll ? 'opacity-50 cursor-not-allowed' : ''}`}
                                title="Atualizar Selecionados"
                            >
                                <ArrowPathIcon className={`w-5 h-5 ${isRefreshingAll ? 'animate-spin text-synapse-primary' : ''}`} />
                            </button>
                            <button
                                onClick={() => {
                                    setConfirmModal({
                                        isOpen: true,
                                        title: `Excluir ${selectedIds.size} perfis selecionados?`,
                                        type: 'delete',
                                        isLoading: false,
                                        onConfirm: async () => {
                                            setConfirmModal(prev => ({ ...prev, isLoading: true }));
                                            try {
                                                await Promise.all(
                                                    Array.from(selectedIds).map(id =>
                                                        fetch(`${API_BASE}/profiles/${id}`, { method: 'DELETE' })
                                                    )
                                                );
                                                await fetchProfiles();
                                                setSelectedIds(new Set());
                                                toast.success('Perfis excluídos com sucesso!');
                                            } finally {
                                                setConfirmModal(prev => ({ ...prev, isOpen: false, isLoading: false }));
                                            }
                                        }
                                    });
                                }}
                                className="p-2 rounded-full hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors"
                                title="Excluir Selecionados"
                            >
                                <TrashIcon className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* ERROR IMAGE VIEWER MODAL */}
            <Modal
                isOpen={!!viewerImage}
                onClose={() => setViewerImage(null)}
                title="Detalhes do Erro"
            >
                <div className="flex flex-col gap-4">
                    <p className="text-sm text-gray-400">
                        Este foi o estado da página no momento da falha. Use isso para diagnosticar se o TikTok pediu Captcha ou se a sessão expirou.
                    </p>
                    {viewerImage && (
                        <div className="rounded-lg overflow-hidden border border-white/10 bg-black">
                            <img src={viewerImage} alt="Erro Screenshot" className="w-full h-auto object-contain max-h-[60vh]" />
                        </div>
                    )}
                    <div className="flex justify-end">
                        <NeonButton onClick={() => setViewerImage(null)}>
                            Fechar
                        </NeonButton>
                    </div>
                </div>
            </Modal>

            {/* DELETE CONFIRMATION MODAL */}
            <Modal
                isOpen={!!deleteConfirmationId}
                onClose={() => setDeleteConfirmationId(null)}
                title="Excluir Perfil"
            >
                <div className="">
                    <p className="text-gray-300 mb-6">
                        Tem certeza que deseja excluir este perfil?
                        <br /><span className="text-xs text-gray-500">Você terá 8 segundos para desfazer esta ação.</span>
                    </p>
                    <div className="flex justify-end gap-3">
                        <button
                            onClick={() => setDeleteConfirmationId(null)}
                            className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors"
                        >
                            Cancelar
                        </button>
                        <NeonButton
                            variant="primary"
                            onClick={confirmDelete}
                            className="!bg-red-500/20 !text-red-500 border-red-500/50 hover:!bg-red-500/30"
                        >
                            Excluir
                        </NeonButton>
                    </div>
                </div>
            </Modal>

            {/* [SYN-UX] GLOBAL CONFIRM MODAL (Added generic support) */}
            <Modal
                isOpen={confirmModal.isOpen}
                onClose={() => !confirmModal.isLoading && setConfirmModal(prev => ({ ...prev, isOpen: false }))}
                title={confirmModal.title}
            >
                <div className="flex justify-end gap-3 mt-6">
                    <NeonButton
                        variant="ghost"
                        onClick={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
                        disabled={confirmModal.isLoading}
                    >
                        Cancelar
                    </NeonButton>
                    <NeonButton
                        variant={confirmModal.type === 'delete' ? 'primary' : 'primary'}
                        onClick={confirmModal.onConfirm}
                        disabled={confirmModal.isLoading}
                        className={clsx(
                            confirmModal.type === 'delete' ? '!bg-red-500/20 !text-red-500 hover:!bg-red-500/30' : '',
                            confirmModal.isLoading && 'opacity-50 cursor-not-allowed'
                        )}
                    >
                        {confirmModal.isLoading ? (
                            <>
                                <ArrowPathIcon className="w-4 h-4 animate-spin mr-2" />
                                Processando...
                            </>
                        ) : (
                            'Confirmar'
                        )}
                    </NeonButton>
                </div>
            </Modal>

            {/* [SYN-UX] New Repair Modal - Replaces UpdateCookiesModal */}
            <ProfileRepairModal
                isOpen={!!repairProfile}
                onClose={() => setRepairProfile(null)}
                profile={repairProfile}
                onSuccess={() => {
                    if (repairProfile) {
                        handleRefreshAvatar(repairProfile.id); // Auto-verify after repair
                    }
                }}
            />

            {/* Import Modal */}
            <Modal
                isOpen={showImportModal}
                onClose={() => setShowImportModal(false)}
                title="Importar Cookies"
            >
                <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">Nome do Perfil <span className="text-xs opacity-50 lowercase float-right">(opcional)</span></label>
                        <input
                            type="text"
                            value={importLabel}
                            onChange={(e) => setImportLabel(e.target.value)}
                            placeholder="Ex: Canal de Cortes"
                            className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all"
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">Username <span className="text-xs opacity-50 lowercase float-right">(opcional)</span></label>
                        <input
                            type="text"
                            value={importUsername}
                            onChange={(e) => setImportUsername(e.target.value)}
                            placeholder="@usuario"
                            className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all"
                        />
                    </div>
                </div>

                <div className="mb-4">
                    <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">Avatar URL <span className="text-xs opacity-50 lowercase float-right">(opcional)</span></label>
                    <input
                        type="text"
                        value={importAvatar}
                        onChange={(e) => setImportAvatar(e.target.value)}
                        placeholder="https://..."
                        className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all"
                    />
                </div>

                <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                        <label className="text-xs text-gray-400 uppercase font-bold">JSON de Cookies (EditThisCookie)</label>
                        <button
                            onClick={handleValidateCookies}
                            disabled={!importCookies || validatingCookies}
                            className="text-[10px] font-bold text-synapse-primary hover:text-white disabled:opacity-50 transition-colors flex items-center gap-1"
                        >
                            {validatingCookies ? "VALIDANDO..." : "VALIDAR E PREENCHER ✨"}
                        </button>
                    </div>
                    <textarea
                        value={importCookies}
                        onChange={(e) => setImportCookies(e.target.value)}
                        placeholder='[{"domain": ".tiktok.com", ...}]'
                        className="w-full h-40 px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white font-mono text-xs focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none custom-scrollbar resize-none"
                    />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                    <NeonButton variant="ghost" onClick={() => setShowImportModal(false)}>
                        Cancelar
                    </NeonButton>
                    <NeonButton onClick={handleImport}>
                        Importar
                    </NeonButton>
                </div>
            </Modal>
        </>
    );

}
