'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
// // import Sidebar from '../components/Sidebar';
import { TikTokProfile } from '../types';
import useWebSocket from '../hooks/useWebSocket';
import {
    ArrowLeftIcon, CheckCircleIcon, PlusIcon, TrashIcon, UserGroupIcon, ArrowPathIcon
} from '@heroicons/react/24/outline';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import clsx from 'clsx';
import Modal from '../components/Modal';

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
                    alert(`Falha ao excluir perfil: ${err.detail || "Erro desconhecido"}`);
                }
            } catch (e) {
                console.error("Delete failed", e);
                alert(`Erro de conexão ao excluir: ${e}`);
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
                alert("Cookies válidos! Dados preenchidos.");
            } else {
                alert(`Erro na validação: ${data.error || "Sessão inválida"}`);
            }
        } catch (e) {
            console.error(e);
            alert("Erro ao validar: JSON inválido ou falha na conexão.");
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
                alert(`Erro: ${err.detail}`);
            }
        } catch (e) {
            console.error(e);
            alert('JSON inválido ou erro de conexão.');
        }
    };

    const handleRefreshAvatar = async (profileId: string) => {
        setRefreshingProfiles(prev => ({ ...prev, [profileId]: true }));
        try {
            const res = await fetch(`${API_BASE}/profiles/refresh-avatar/${profileId}`, { method: 'POST' });
            if (res.ok) {
                fetchProfiles();
            } else {
                const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
                alert(`Erro: ${err.detail || "Falha na requisição"}`);
            }
        } catch (e) {
            alert(`Erro de conexão: ${e}`);
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
                            if (confirm("Atualizar todos os perfis sequencialmente? Isso pode levar algum tempo.")) {
                                setIsRefreshingAll(true);
                                try {
                                    for (const p of profiles) {
                                        await handleRefreshAvatar(p.id);
                                    }
                                    alert("Todos os perfis foram atualizados!");
                                } finally {
                                    setIsRefreshingAll(false);
                                }
                            }
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

            {/* Profiles Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-24">
                {loading ? (
                    <p className="text-gray-500 col-span-full text-center py-12">Carregando perfis...</p>
                ) : profiles.length > 0 ? (
                    profiles.map((profile, i) => {
                        if (pendingDeletes.has(profile.id)) return null;
                        const health = getHealthStatus(profile);
                        const isSelected = selectedIds.has(profile.id);

                        return (
                            <StitchCard
                                key={i}
                                className={clsx(
                                    "p-6 relative group transition-all duration-300",
                                    isSelected ? "border-synapse-primary/50 bg-synapse-primary/5" : ""
                                )}
                            >
                                {/* Checkbox Overlay */}
                                <div className="absolute top-4 right-4 z-10">
                                    <input
                                        type="checkbox"
                                        checked={isSelected}
                                        onChange={() => handleSelect(profile.id)}
                                        className="w-4 h-4 rounded border-gray-600 bg-black/50 text-synapse-primary focus:ring-synapse-primary cursor-pointer accent-synapse-primary"
                                    />
                                </div>

                                <div className="flex items-center justify-between mb-4 pr-6">
                                    <div className="flex items-center gap-3">
                                        {/* Avatar Logic */}
                                        <div className="relative">
                                            {profile.avatar_url ? (
                                                <img
                                                    src={profile.avatar_url}
                                                    alt={profile.label}
                                                    className="w-12 h-12 rounded-full object-cover bg-[#30363d] ring-2 ring-transparent group-hover:ring-synapse-primary/50 transition-all"
                                                    onError={(e) => {
                                                        // Fallback on error
                                                        (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${profile.label}&background=random`;
                                                    }}
                                                />
                                            ) : (
                                                <span className="text-4xl">{getProfileIcon(profile.id, profile.icon)}</span>
                                            )}
                                            {/* HEALTH INDICATOR */}
                                            <div className={clsx(
                                                "absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-[#161b22]",
                                                health === 'healthy' ? "bg-emerald-500" :
                                                    health === 'expired' || health === 'error' ? "bg-red-500" : "bg-gray-500"
                                            )}>
                                                {health === 'healthy' && (
                                                    <div className="absolute inset-0 bg-emerald-500 rounded-full animate-ping opacity-75" />
                                                )}
                                            </div>
                                        </div>

                                        <div>
                                            <h3 className="text-base font-bold text-white m-0 truncate max-w-[120px]">{profile.label}</h3>
                                            {profile.username && (
                                                <p className="text-xs text-gray-400 m-0 mt-0.5 truncate max-w-[120px]">@{profile.username}</p>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Health Status Text */}
                                <div className="flex gap-2 mb-4">
                                    <div className={clsx(
                                        "px-2 py-1.5 rounded text-[10px] font-bold uppercase inline-flex items-center gap-1.5 border flex-1 justify-center",
                                        health === 'healthy' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" :
                                            health === 'expired' || health === 'error' ? "bg-red-500/10 text-red-400 border-red-500/20" :
                                                "bg-gray-500/10 text-gray-400 border-gray-500/20"
                                    )}>
                                        {health === 'healthy' ? (
                                            <><CheckCircleIcon className="w-3 h-3" /> ATIVO</>
                                        ) : health === 'expired' ? (
                                            <><div className="w-2 h-2 rounded-full bg-red-500" /> EXPIRADO</>
                                        ) : health === 'error' ? (
                                            <><div className="w-2 h-2 rounded-full bg-red-500" /> ERRO</>
                                        ) : (
                                            <><div className="w-2 h-2 rounded-full bg-gray-500" /> INATIVO</>
                                        )}
                                    </div>

                                    {/* VIEW ERROR BUTTON */}
                                    {profile.last_error_screenshot && (
                                        <button
                                            onClick={() => setViewerImage(`${getApiUrl()}${profile.last_error_screenshot}`)}
                                            className="px-2 py-1.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] font-bold hover:bg-red-500/20 transition-colors"
                                            title="Ver Print do Erro"
                                        >
                                            VER ERRO
                                        </button>
                                    )}
                                </div>


                                <div className="grid grid-cols-2 gap-3 mb-4">
                                    <div className="p-3 rounded-lg bg-black/30 border border-white/5">
                                        <p className="text-[10px] text-gray-500 m-0 uppercase font-mono">UPLOADS</p>
                                        <p className="text-sm text-white font-medium m-0 mt-1">—</p>
                                    </div>
                                    <div className="p-3 rounded-lg bg-black/30 border border-white/5 flex flex-col justify-center">
                                        <p className="text-[10px] text-gray-500 m-0 uppercase font-mono">NICHE</p>
                                        <p className="text-xs text-white/50 m-0 mt-1 truncate">{profile.niche || "Geral"}</p>
                                    </div>
                                </div>

                                <div className="flex gap-2">
                                    <NeonButton variant="primary" className="flex-1 text-xs">
                                        Usar Perfil
                                    </NeonButton>

                                    {/* Refresh Avatar Button */}
                                    <button
                                        onClick={() => handleRefreshAvatar(profile.id)}
                                        disabled={refreshingProfiles[profile.id]}
                                        className={clsx(
                                            "p-2.5 rounded-lg bg-[#1c2128] border border-white/10 text-gray-400 hover:text-white hover:border-synapse-primary/50 transition-all",
                                            refreshingProfiles[profile.id] && "opacity-50 cursor-not-allowed"
                                        )}
                                        title="Atualizar avatar do TikTok"
                                    >
                                        <ArrowPathIcon
                                            className={clsx(
                                                "w-4 h-4",
                                                refreshingProfiles[profile.id] && "animate-spin text-synapse-primary"
                                            )}
                                        />
                                    </button>

                                    <button
                                        title="Excluir perfil"
                                        onClick={() => promptDelete(profile.id)}
                                        className="p-2.5 rounded-lg bg-[#1c2128] border border-white/10 text-gray-400 hover:text-red-400 hover:border-red-500/50 transition-all"
                                    >
                                        <TrashIcon className="w-4 h-4" />
                                    </button>
                                </div>
                            </StitchCard>
                        )
                    })
                ) : (
                    <StitchCard className="p-12 text-center col-span-full flex flex-col items-center justify-center">
                        <UserGroupIcon className="w-12 h-12 text-gray-600 mb-4" />
                        <p className="text-gray-400 m-0">Nenhum perfil encontrado</p>
                        <p className="text-xs text-gray-600 mt-2">Adicione sessões TikTok em backend/data/sessions/</p>
                    </StitchCard>
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
                                    if (confirm(`Excluir ${selectedIds.size} perfis selecionados?`)) {
                                        // Bulk delete logic would go here - for now just alert
                                        // Ideally we iterate and call delete, or have a bulk endpoint
                                        Array.from(selectedIds).forEach(id => {
                                            // Optimistic delete logic will be better here, but for now standard:
                                            fetch(`${API_BASE}/profiles/${id}`, { method: 'DELETE' }).then(() => fetchProfiles());
                                        });
                                        setSelectedIds(new Set());
                                    }
                                }}
                                className="p-2 rounded-full hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors"
                                title="Excluir Selecionados"
                            >
                                <TrashIcon className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Add Profile Card */}
                <div
                    onClick={() => {
                        setImportLabel('');
                        setImportCookies('');
                        setImportUsername('');
                        setImportAvatar('');
                        setShowImportModal(true);
                    }}
                    className="p-6 rounded-xl bg-white/5 border-2 border-dashed border-white/10 flex flex-col items-center justify-center min-h-[200px] cursor-pointer hover:border-synapse-primary/50 hover:bg-white/10 transition-all group"
                >
                    <PlusIcon className="w-8 h-8 text-gray-500 group-hover:text-synapse-primary mb-3 transition-colors" />
                    <p className="text-gray-500 group-hover:text-gray-300 transition-colors m-0">Importar Novo Perfil</p>
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
