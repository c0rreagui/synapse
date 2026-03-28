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
import { apiClient } from '../lib/api';

// Build WebSocket URL: connect directly to backend (Next.js rewrites don't support WS)
const getWsUrl = () => {
    const apiUrl = getApiUrl();
    if (apiUrl && apiUrl.startsWith('http')) {
        return apiUrl.replace('http', 'ws');
    }
    if (typeof window !== 'undefined') {
        return `ws://${window.location.hostname}:8000`;
    }
    return '';
};

export default function ProfilesPage() {
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
    const [proxies, setProxies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showImportModal, setShowImportModal] = useState(false);
    const [importLabel, setImportLabel] = useState('');
    const [importCookies, setImportCookies] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [refreshingProfiles, setRefreshingProfiles] = useState<Record<string, boolean>>({});
    const [refreshErrors, setRefreshErrors] = useState<Record<string, string | null>>({});
    const [isRefreshingAll, setIsRefreshingAll] = useState(false);

    // INLINE EDIT STATE
    const [editingProfileId, setEditingProfileId] = useState<string | null>(null);
    const [editLabel, setEditLabel] = useState('');
    const [editUsername, setEditUsername] = useState('');

    // BULK ACTIONS STATE
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    // UNDO PATTERN STATE
    const [pendingDeletes, setPendingDeletes] = useState<Set<string>>(new Set());
    const [deleteConfirmationId, setDeleteConfirmationId] = useState<string | null>(null);
    const deleteTimers = useRef<Record<string, NodeJS.Timeout>>({});

    // ERROR MODAL STATE
    const [viewerImage, setViewerImage] = useState<string | null>(null);

    // REMOTE SESSION STATE
    const [remoteSession, setRemoteSession] = useState<{ active: boolean; novnc_url?: string; profile_slug?: string; session_type?: string } | null>(null);
    const [startingRemote, setStartingRemote] = useState(false);

    // VNC FÁBRICA STATE
    const [showFactoryModal, setShowFactoryModal] = useState(false);
    const [factoryStep, setFactoryStep] = useState<1 | 2 | 3>(1);
    const [factoryProxyId, setFactoryProxyId] = useState<number | null>(null);
    const [factoryLabel, setFactoryLabel] = useState('');
    const [factorySession, setFactorySession] = useState<{ active: boolean; novnc_url?: string } | null>(null);
    const [factoryCapturing, setFactoryCapturing] = useState(false);
    const [startingFactory, setStartingFactory] = useState(false);
    const [factoryResult, setFactoryResult] = useState<{ profile_id: string; username?: string; label: string } | null>(null);

    // IMPORT STATE EXTENDED
    const [importUsername, setImportUsername] = useState('');
    const [importAvatar, setImportAvatar] = useState('');
    const [importFingerprint, setImportFingerprint] = useState('');
    const [importProxyId, setImportProxyId] = useState<number | null>(null);
    const [validatingCookies, setValidatingCookies] = useState(false);

    // SYN-105: Inline Proxy State
    const [proxyMode, setProxyMode] = useState<'existing' | 'new'>('existing');
    const [importProxyServer, setImportProxyServer] = useState('');
    const [importProxyUser, setImportProxyUser] = useState('');
    const [importProxyPass, setImportProxyPass] = useState('');
    const [importProxyNickname, setImportProxyNickname] = useState('');

    // [SYN-UX] Repair Modal State (Replaces old manual/auto states)
    const [repairProfile, setRepairProfile] = useState<TikTokProfile | null>(null);

    // BACKEND INTEGRATION: Proxy Validation State
    const [validatingProxy, setValidatingProxy] = useState(false);
    const [proxyLocation, setProxyLocation] = useState<{ city: string, region: string, country: string } | null>(null);
    const [proxyError, setProxyError] = useState<string | null>(null);

    // [TELEMETRY & LOGS]
    const [systemVitals, setSystemVitals] = useState<any>(null);
    const [realLogs, setRealLogs] = useState<any[]>([]);

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
                await apiClient.delete(`/api/v1/profiles/${id}`);
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
            } catch (e: any) {
                console.error("Delete failed", e);
                toast.error('Erro ao excluir', {
                    description: e?.data?.detail || 'Erro desconhecido'
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
        }, 30000); // [SYN-111] Expanded from 15s to 30s for A11y safety

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

    useEffect(() => {
        // 1. Fetch system vitals periodically
        const fetchVitals = async () => {
            try {
                const data = await apiClient.get<any>('/api/v1/telemetry/vitals');
                setSystemVitals(data);
            } catch (e) {

                // silent
            }
        };
        fetchVitals();
        const interval = setInterval(fetchVitals, 5000);

        // [SYN-109] 2. Connect to real-time log stream with graceful retry
        let ws: WebSocket | null = null;
        let wsRetryCount = 0;
        let wsReconnectTimer: NodeJS.Timeout | null = null;
        let wsPingInterval: NodeJS.Timeout | null = null;
        let isMounted = true;

        const connectWs = () => {
            if (!isMounted) return;
            try {
                const wsUrl = getWsUrl() + '/api/v1/telemetry/stream';
                ws = new WebSocket(wsUrl);

                ws.onopen = () => {
                    wsRetryCount = 0; // Reset backoff on success
                    // Keepalive ping
                    wsPingInterval = setInterval(() => {
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send('ping');
                        }
                    }, 30000);
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'log_entry') {
                            setRealLogs(prev => {
                                const newLogs = [...prev, data.data].slice(-50);
                                return newLogs;
                            });
                        }
                    } catch (e) { }
                };

                ws.onclose = () => {
                    if (wsPingInterval) clearInterval(wsPingInterval);
                    wsPingInterval = null;
                    if (!isMounted) return;
                    // Exponential backoff: 3s -> 6s -> 12s -> 24s -> 30s (max)
                    const delay = Math.min(3000 * Math.pow(2, wsRetryCount), 30000);
                    wsRetryCount++;
                    wsReconnectTimer = setTimeout(connectWs, delay);
                };

                ws.onerror = () => {
                    // Silently let onclose handle reconnect — no console spam
                };
            } catch (e) {
                // [SYN-109] Graceful: if WebSocket constructor itself fails, retry silently
                if (isMounted) {
                    const delay = Math.min(3000 * Math.pow(2, wsRetryCount), 30000);
                    wsRetryCount++;
                    wsReconnectTimer = setTimeout(connectWs, delay);
                }
            }
        };

        connectWs();

        return () => {
            isMounted = false;
            clearInterval(interval);
            if (wsPingInterval) clearInterval(wsPingInterval);
            if (wsReconnectTimer) clearTimeout(wsReconnectTimer);
            if (ws) ws.close();
        };
    }, []);

    async function fetchProfiles() {
        setLoading(true);
        setError(null);
        try {
            const data = await apiClient.get<TikTokProfile[]>('/api/v1/profiles/list');
            setProfiles(data);
        } catch (err) {
            console.error(err);
            setError('Não foi possível conectar ao servidor. Verifique se o backend está rodando.');
        }
        setLoading(false);
    }

    async function loadProxies() {
        try {
            const data = await apiClient.get<any[]>('/api/v1/proxies');
            setProxies(data);
        } catch (err) {
            console.error("Failed to load proxies", err);
            toast.error('Erro de Servidor', {
                description: 'Falha grave ao contatar o endpoint de proxies.'
            });
        }
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
        loadProxies();
        fetchProfiles();
    }, []);

    const updateProxy = async (profileId: string, proxyId: number | null) => {
        try {
            await apiClient.put(`/api/v1/profiles/${profileId}`, { proxy_id: proxyId || null });

            toast.success('Nó de conexão atualizado com sucesso');
            setProfiles(prev => prev.map(p => {
                if (p.id === profileId) {
                    return { ...p, proxy_id: proxyId || undefined };
                }
                return p;
            }));
        } catch (e: any) {
            toast.error('Grave: Falha na comunicação', { description: e?.message });
        }
    };

    const handleEditSave = async (profileId: string) => {
        try {
            await apiClient.put(`/api/v1/profiles/${profileId}`, { label: editLabel, username: editUsername });

            toast.success('Perfil atualizado com sucesso');
            setProfiles(prev => prev.map(p => {
                if (p.id === profileId) {
                    return { ...p, label: editLabel, username: editUsername };
                }
                return p;
            }));
        } catch (e) {
            toast.error('Grave: Falha na comunicação');
        }
        setEditingProfileId(null);
    };


    const handleValidateCookies = async () => {
        if (!importCookies) return;
        setValidatingCookies(true);
        try {
            // Basic JSON check
            JSON.parse(importCookies);

            const data = await apiClient.post<any>('/api/v1/profiles/validate-cookies', { cookies: importCookies });

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

            const payload: Record<string, any> = {
                label: importLabel,
                cookies: importCookies,
                username: importUsername,
                avatar_url: importAvatar,
                fingerprint_ua: importFingerprint ? importFingerprint : undefined
            };

            // SYN-105: Send either existing proxy_id or inline proxy data
            if (proxyMode === 'existing' && importProxyId) {
                payload.proxy_id = importProxyId;
            } else if (proxyMode === 'new' && importProxyServer.trim()) {
                payload.proxy_server = importProxyServer.trim();
                payload.proxy_username = importProxyUser.trim() || undefined;
                payload.proxy_password = importProxyPass.trim() || undefined;

                // Priorize user-typed nickname. Fallback to location-based one if validated
                if (importProxyNickname.trim()) {
                    payload.proxy_nickname = importProxyNickname.trim();
                } else if (proxyLocation) {
                    payload.proxy_nickname = `${proxyLocation.country}-${proxyLocation.region} (${proxyLocation.city})`;
                }
            }

            await apiClient.post('/api/v1/profiles/import', payload);

            setShowImportModal(false);
            setImportLabel('');
            setImportCookies('');
            setImportUsername('');
            setImportAvatar('');
            setImportFingerprint('');
            setImportProxyId(null);
            setImportProxyServer('');
            setImportProxyUser('');
            setImportProxyPass('');
            setImportProxyNickname('');
            setProxyLocation(null);
            setProxyError(null);
            setProxyMode('existing');
            fetchProfiles(); // Refresh list
            loadProxies(); // Refresh proxies list
        } catch (e: any) {
            console.error(e);
            toast.error('Erro de validacao / importação', {
                description: e?.data?.detail || 'JSON invalido ou erro de conexao'
            });
        }
    };

    // ─── Remote Session (VNC) Handlers ───────────────────────────────────
    const fetchRemoteSessionStatus = useCallback(async () => {
        try {
            const data = await apiClient.get<any>('/api/v1/profiles/remote-session/status');
            setRemoteSession(data);
        } catch {
            // silent — VNC not available in dev
        }
    }, []);

    const handleStartRemoteSession = async (profileSlug: string) => {
        setStartingRemote(true);
        try {
            const data = await apiClient.post<any>(`/api/v1/profiles/remote-session/start/${profileSlug}`);
            setRemoteSession(data);
            toast.success('Sessão remota iniciada', {
                description: 'O browser está acessível via VNC. Resolva o CAPTCHA e encerre a sessão.',
            });
        } catch (e: any) {
            toast.error('Erro ao iniciar sessão remota', {
                description: e?.data?.detail || 'Verifique se o container tem suporte a VNC.',
            });
        } finally {
            setStartingRemote(false);
        }
    };

    const handleStopRemoteSession = async () => {
        try {
            const data = await apiClient.post<any>('/api/v1/profiles/remote-session/stop');
            setRemoteSession({ active: false });
            toast.success(data.message || 'Sessão remota encerrada');
        } catch (e: any) {
            toast.error('Erro ao encerrar sessão', {
                description: e?.data?.detail || 'Erro desconhecido',
            });
        }
    };

    // VNC FÁBRICA HANDLERS
    const resetFactoryModal = () => {
        setShowFactoryModal(false);
        setFactoryStep(1);
        setFactoryProxyId(null);
        setFactoryLabel('');
        setFactorySession(null);
        setFactoryResult(null);
        setFactoryCapturing(false);
    };

    const handleStartFactorySession = async () => {
        if (!factoryProxyId) {
            toast.error('Selecione um proxy antes de iniciar.');
            return;
        }
        setStartingFactory(true);
        try {
            const data = await apiClient.post<any>('/api/v1/vnc-factory/start', { proxy_id: factoryProxyId });
            setFactorySession(data);
            setRemoteSession({ active: true, session_type: 'factory', novnc_url: data.novnc_url });
            setFactoryStep(2);
            toast.success('Sessão fábrica iniciada', {
                description: 'Faça login no TikTok via VNC e clique em Capturar.',
            });
        } catch (e: any) {
            toast.error('Erro ao iniciar VNC Fábrica', {
                description: e?.data?.detail || 'Verifique se há outra sessão ativa.',
            });
        } finally {
            setStartingFactory(false);
        }
    };

    const handleCaptureFactoryProfile = async () => {
        setFactoryCapturing(true);
        try {
            const data = await apiClient.post<any>('/api/v1/vnc-factory/capture', {
                label: factoryLabel || undefined,
                proxy_id: factoryProxyId,
            });
            setFactoryResult(data);
            setFactoryStep(3);
            setFactorySession(null);
            setRemoteSession({ active: false });
            fetchProfiles();
            toast.success('Perfil capturado!', {
                description: `${data.username ? `@${data.username}` : data.label} adicionado ao sistema.`,
            });
        } catch (e: any) {
            const status = e?.status || e?.response?.status;
            const detail = e?.data?.detail || 'Erro desconhecido';
            if (status === 422) {
                toast.error('Login ainda não concluído', { description: 'Complete o login no TikTok antes de capturar.' });
            } else {
                toast.error('Falha ao capturar perfil', { description: detail });
            }
        } finally {
            setFactoryCapturing(false);
        }
    };

    const handleStopFactorySession = async () => {
        try {
            await apiClient.post('/api/v1/vnc-factory/stop');
            setFactorySession(null);
            setRemoteSession({ active: false });
            setFactoryStep(1);
            setFactoryResult(null);
            toast.success('Sessão fábrica encerrada');
        } catch (e: any) {
            toast.error('Erro ao encerrar fábrica', { description: e?.data?.detail || 'Erro desconhecido' });
        }
    };

    // Poll remote session status on mount
    useEffect(() => {
        fetchRemoteSessionStatus();
    }, [fetchRemoteSessionStatus]);

    const handleValidateProxy = async () => {
        if (!importProxyServer) {
            toast.error("Preencha o servidor do proxy (IP:Porta)");
            return;
        }
        setValidatingProxy(true);
        setProxyLocation(null);
        setProxyError(null);

        try {
            const data = await apiClient.post<any>('/api/v1/proxies/validate', {
                server: importProxyServer,
                username: importProxyUser || null,
                password: importProxyPass || null
            });
            if (data.status === 'success') {
                toast.success(data.message);
                setProxyLocation({
                    city: data.city,
                    region: data.region,
                    country: data.country
                });
            } else {
                toast.error(data.message || 'Falha ao conectar no proxy');
                setProxyError(data.message || 'Falha ao conectar no proxy');
            }
        } catch (e: any) {
            const msg = e?.data?.message || 'Erro de conexão ao testar proxy';
            toast.error(msg);
            setProxyError(msg);
        } finally {
            setValidatingProxy(false);
        }
    };

    const handleRefreshAvatar = async (profileId: string) => {
        setRefreshingProfiles(prev => ({ ...prev, [profileId]: true }));
        setRefreshErrors(prev => ({ ...prev, [profileId]: null })); // Clear errors

        try {
            await apiClient.post(`/api/v1/profiles/refresh-avatar/${profileId}`);
            fetchProfiles(); // Success
        } catch (e: any) {
            let errorMessage = e?.data?.detail || "Falha na comunicação com o TikTok";

            // Friendly error mapping
            if (errorMessage.includes("Session Expired")) {
                errorMessage = "Sessão Expirada. Renove os cookies.";
            } else if (errorMessage.includes("Target page, context or browser has been closed")) {
                errorMessage = "Navegador fechou. Tente novamente.";
            }

            setRefreshErrors(prev => ({ ...prev, [profileId]: errorMessage }));
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


    const handleBulkDelete = async () => {
        if (selectedIds.size === 0) return;
        const msg = selectedIds.size === 1 ? 'Excluir 1 perfil selecionado?' : `Excluir ${selectedIds.size} perfis selecionados?`;
        setConfirmModal({
            isOpen: true,
            title: msg,
            type: 'delete',
            isLoading: false,
            onConfirm: async () => {
                setConfirmModal(prev => ({ ...prev, isLoading: true }));
                try {
                    await apiClient.post('/api/v1/profiles/bulk-delete', { profile_ids: Array.from(selectedIds) });
                    toast.success(`${selectedIds.size} perfis excluídos.`);
                    setProfiles(prev => prev.filter(p => !selectedIds.has(p.id)));
                    setSelectedIds(new Set());
                } catch (e: any) {
                    toast.error('Erro na exclusão em lote', { description: e?.data?.detail || 'Erro de conexão' });
                } finally {
                    setConfirmModal(prev => ({ ...prev, isOpen: false, isLoading: false }));
                }
            }
        });
    };

    const handleBulkRefresh = async () => {
        if (selectedIds.size === 0) return;
        setConfirmModal({
            isOpen: true,
            title: `Atualizar ${selectedIds.size} perfis selecionados?`,
            type: 'success',
            isLoading: false,
            onConfirm: async () => {
                setConfirmModal(prev => ({ ...prev, isLoading: true }));
                try {
                    await apiClient.post('/api/v1/profiles/bulk-refresh', { profile_ids: Array.from(selectedIds) });
                    toast.success(`Atualização em lote iniciada para ${selectedIds.size} perfis.`);
                    setSelectedIds(new Set());
                    fetchProfiles(); // reload to get new states
                } catch (e: any) {
                    toast.error('Erro na atualização em lote', { description: e?.data?.detail || 'Erro de conexão' });
                } finally {
                    setConfirmModal(prev => ({ ...prev, isOpen: false, isLoading: false }));
                }
            }
        });
    };

    return (
        <>

            {/* FLOATING BULK ACTION BAR */}
            {selectedIds.size > 0 && (
                <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-8 duration-300">
                    <div className="bg-[#161b22]/90 backdrop-blur-xl border border-synapse-primary/30 px-6 py-4 rounded-2xl shadow-[0_0_40px_rgba(7,182,213,0.15)] flex items-center gap-6">
                        <div className="text-white font-bold tracking-widest text-sm flex items-center gap-2">
                            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-synapse-primary/20 text-synapse-primary text-xs">
                                {selectedIds.size}
                            </span>
                            Selecionados
                        </div>
                        <div className="w-px h-6 bg-white/10"></div>
                        <div className="flex gap-3">
                            <button
                                onClick={handleBulkRefresh}
                                className="px-4 py-2 bg-synapse-primary/10 hover:bg-synapse-primary/20 text-synapse-primary text-xs font-bold uppercase tracking-wider rounded-lg transition-colors border border-synapse-primary/20 flex items-center gap-2"
                            >
                                <ArrowPathIcon className="w-4 h-4" />
                                Sync Selecionados
                            </button>
                            <button
                                onClick={handleBulkDelete}
                                className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 text-xs font-bold uppercase tracking-wider rounded-lg transition-colors border border-red-500/20 flex items-center gap-2"
                            >
                                <TrashIcon className="w-4 h-4" />
                                Excluir Selecionados
                            </button>
                            <button
                                onClick={() => setSelectedIds(new Set())}
                                className="px-3 py-2 text-gray-400 hover:text-white uppercase text-[10px] font-bold tracking-widest"
                            >
                                Cancelar
                            </button>
                        </div>
                    </div>
                </div>
            )}

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

            {/* ═══ TERMINAL MATRIX HEADER ═══ */}
            <div className="mb-16">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <Link href="/">
                            <div className="w-10 h-10 rounded-lg bg-[#1c2128] border border-white/10 flex items-center justify-center cursor-pointer hover:border-synapse-primary/50 transition-colors group">
                                <ArrowLeftIcon className="w-5 h-5 text-gray-400 group-hover:text-synapse-primary" />
                            </div>
                        </Link>
                        <div>
                            <h1 className="text-4xl font-black text-white tracking-tighter uppercase">Terminal Matrix</h1>
                            <p className="text-synapse-primary font-mono text-xs tracking-widest uppercase opacity-60">Continuous Chronological Stream Node Grid</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <NeonButton
                            variant="ghost"
                            onClick={handleSelectAll}
                            className="text-xs"
                        >
                            {selectedIds.size === profiles.length && profiles.length > 0 ? 'Desmarcar Todos' : 'Selecionar Todos'}
                        </NeonButton>
                        <NeonButton
                            variant="primary"
                            onClick={() => { setFactoryStep(1); setShowFactoryModal(true); }}
                            disabled={remoteSession?.active === true}
                            className="text-xs flex items-center gap-1.5"
                            title={remoteSession?.active ? 'Encerre a sessão VNC ativa antes de criar um novo perfil' : 'Criar novo perfil via VNC Fábrica'}
                        >
                            <PlusIcon className="w-3.5 h-3.5" />
                            Criar via VNC
                        </NeonButton>
                    </div>
                </div>
            </div>

            {error && (
                <StitchCard className="p-4 mb-6 !bg-red-500/10 !border-red-500/30 text-red-400">
                    {error}
                </StitchCard>
            )}

            {/* ═══ VNC REMOTE SESSION BANNER ═══ */}
            {remoteSession?.active && remoteSession.novnc_url && (
                <div className="mb-6 rounded-lg border border-violet-500/30 bg-violet-500/5 backdrop-blur-sm overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 bg-violet-500/10 border-b border-violet-500/20">
                        <div className="flex items-center gap-3">
                            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-[0_0_8px_#34d399]"></span>
                            <span className="text-violet-300 font-mono text-xs font-bold uppercase tracking-widest">
                                Sessão Remota Ativa
                            </span>
                            <span className="text-violet-400/60 font-mono text-[10px]">
                                {remoteSession.profile_slug}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <a
                                href={remoteSession.novnc_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-3 py-1 bg-violet-500/20 hover:bg-violet-500/30 text-violet-300 text-[10px] font-bold uppercase rounded border border-violet-500/30 flex items-center gap-1.5 transition-all"
                            >
                                <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                                Abrir em Nova Aba
                            </a>
                            <button
                                onClick={handleStopRemoteSession}
                                className="px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 text-[10px] font-bold uppercase rounded border border-red-500/30 flex items-center gap-1.5 transition-all"
                            >
                                <span className="material-symbols-outlined text-[14px]">stop_circle</span>
                                Encerrar
                            </button>
                        </div>
                    </div>
                    <div className="relative w-full" style={{ height: '600px' }}>
                        <iframe
                            src={remoteSession.novnc_url}
                            className="w-full h-full border-0"
                            title="VNC Remote Session"
                            allow="clipboard-read; clipboard-write"
                        />
                    </div>
                </div>
            )}

            {/* ═══ TERMINAL GRID ═══ */}
            {loading ? (
                <p className="text-gray-500 text-center py-12 font-mono">Carregando nós...</p>
            ) : profiles.length > 0 ? (
                <div className="terminal-grid pb-24">
                    {profiles.map((profile) => {
                        if (pendingDeletes.has(profile.id)) return null;
                        const health = getHealthStatus(profile);
                        const isSelected = selectedIds.has(profile.id);
                        const isRefreshing = refreshingProfiles[profile.id];

                        // Status color mapping
                        const statusColor = health === 'healthy' ? 'success' : health === 'error' ? 'error' : 'warn';
                        const statusLabel = health === 'healthy' ? 'IDEAL' : health === 'error' ? 'FAILED' : 'INACTIVE';
                        const statusDot = health === 'healthy' ? 'bg-[#00ff9d]' : health === 'error' ? 'bg-[#ff2a2a]' : 'bg-[#ffb02a]';
                        const statusText = health === 'healthy' ? 'text-[#00ff9d]' : health === 'error' ? 'text-[#ff2a2a]' : 'text-[#ffb02a]';

                        // Map real logs to the profile
                        const profileLogs = realLogs.filter(l => {
                            if (!l || !l.message) return false;
                            const msg = l.message.toLowerCase();
                            // Filter logic: match profile label, username, or id
                            return msg.includes(profile.label.toLowerCase()) ||
                                (profile.username && msg.includes(profile.username.toLowerCase())) ||
                                msg.includes(profile.id.toLowerCase());
                        });

                        // Fallback to global logs if no specific logs are found
                        const displayLogs = profileLogs.length > 0 ? profileLogs.slice(-10) : realLogs.slice(-10);

                        const fakeLogs = displayLogs.length > 0 ? displayLogs.map(l => {
                            let date = new Date(l.timestamp);
                            if (isNaN(date.getTime())) {
                                date = new Date();
                            }
                            const time = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
                            const isErr = l.level?.toLowerCase() === 'error';
                            const isWarn = l.level?.toLowerCase() === 'warning';

                            return {
                                time,
                                type: isErr ? 'ERR ' : isWarn ? 'WARN' : 'INFO',
                                typeColor: isErr ? 'text-[#ff2a2a] font-bold' : isWarn ? 'text-[#ffb02a]' : 'text-synapse-primary font-bold',
                                msg: l.message
                            };
                        }) : (health === 'healthy' ? [
                            { time: '14:22:01', type: 'INIT', typeColor: 'text-synapse-primary font-bold', msg: 'SYNC Sequence started...' },
                            { time: '14:22:10', type: 'DATA', typeColor: 'text-[#00ff9d]/80', msg: 'Table update: records synced.' },
                            { time: '14:26:12', type: 'OKAY', typeColor: 'text-[#00ff9d]/80', msg: 'Heartbeat active. Node stable.' },
                        ] : health === 'error' ? [
                            { time: '10:00:15', type: 'INIT', typeColor: 'text-synapse-primary', msg: 'Booting node...' },
                            { time: '10:00:17', type: 'WARN', typeColor: 'text-[#ffb02a]', msg: 'Slow response from gateway.' },
                        ] : [
                            { time: '08:30:00', type: 'INIT', typeColor: 'text-synapse-primary', msg: 'Session persistence check...' },
                            { time: '09:12:00', type: 'WARN', typeColor: 'text-[#ffb02a]', msg: '429: Too Many Requests.' },
                            { time: '10:12:01', type: 'WAIT', typeColor: 'text-slate-400', msg: 'Cooldown active.' },
                        ]);

                        return (
                            <div
                                key={profile.id}
                                className={clsx(
                                    "holographic-card",
                                    statusColor === 'error' && 'card-error',
                                    statusColor === 'warn' && 'card-warn',
                                    isSelected && 'card-selected',
                                )}
                                role="article"
                                aria-label={`Perfil ${profile.label}`}
                                onClick={(e) => {
                                    const target = e.target as HTMLElement;
                                    if (!target.closest('button') && !target.closest('select') && !target.closest('input') && !target.closest('[data-edit-zone]')) {
                                        handleSelect(profile.id);
                                    }
                                }}
                            >
                                {/* Scanline Overlay */}
                                <div className={clsx("glitch-overlay", statusColor === 'error' && 'opacity-80')}></div>

                                {/* ═══ FLOATING HEADER ═══ */}
                                <div className={clsx(
                                    "holographic-header",
                                    statusColor === 'error' && 'header-error',
                                    statusColor === 'warn' && 'header-warn',
                                )}>
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            {/* Profile Avatar (Circle - TikTok Standard) */}
                                            <div className={clsx(
                                                "size-12 rounded-full border flex items-center justify-center relative overflow-hidden shrink-0",
                                                statusColor === 'error' ? "bg-[#ff2a2a]/10 border-[#ff2a2a]/30" :
                                                    statusColor === 'warn' ? "bg-[#ffb02a]/5 border-[#ffb02a]/20" :
                                                        "bg-synapse-primary/10 border-synapse-primary/30"
                                            )}>
                                                {profile.avatar_url ? (
                                                    <img
                                                        src={profile.avatar_url}
                                                        alt={profile.label}
                                                        className="w-full h-full object-cover relative z-10"
                                                        onError={(e) => {
                                                            (e.target as HTMLImageElement).style.display = 'none';
                                                            const fallback = (e.target as HTMLElement).nextElementSibling as HTMLElement;
                                                            if (fallback) fallback.style.display = 'flex';
                                                        }}
                                                    />
                                                ) : null}
                                                <span className={clsx("text-2xl absolute inset-0 flex items-center justify-center", profile.avatar_url && "hidden")}>{getProfileIcon(profile.id, profile.icon)}</span>
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <span className={clsx(
                                                        "font-mono text-[9px] px-1.5 py-0.5 rounded leading-none",
                                                        statusColor === 'error' ? "text-[#ff2a2a] bg-[#ff2a2a]/20" :
                                                            statusColor === 'warn' ? "text-[#ffb02a] bg-[#ffb02a]/20" :
                                                                "text-synapse-primary bg-synapse-primary/20"
                                                    )}>
                                                        ND-{profile.id.slice(0, 4).toUpperCase()}
                                                    </span>
                                                    <button
                                                        data-edit-zone="true"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setEditingProfileId(profile.id);
                                                            setEditLabel(profile.label);
                                                            setEditUsername(profile.username || '');
                                                        }}
                                                        className="cursor-pointer hover:text-white transition-colors"
                                                        aria-label={`Editar ${profile.label}`}
                                                    >
                                                        <span className="material-symbols-outlined text-[14px] text-synapse-primary/60">edit</span>
                                                    </button>
                                                </div>
                                                {editingProfileId === profile.id ? (
                                                    <div className="flex flex-col gap-1" data-edit-zone="true">
                                                        <input
                                                            className="bg-black/60 border border-synapse-primary/50 focus:border-synapse-primary text-white text-xs px-2 py-1 rounded uppercase w-[160px] outline-none"
                                                            value={editLabel}
                                                            onChange={(e) => setEditLabel(e.target.value)}
                                                            onClick={(e) => e.stopPropagation()}
                                                            onKeyDown={(e) => {
                                                                if (e.key === 'Enter') handleEditSave(profile.id);
                                                                if (e.key === 'Escape') setEditingProfileId(null);
                                                            }}
                                                            autoFocus
                                                        />
                                                        <input
                                                            className="bg-black/60 border border-slate-700 text-synapse-primary text-[10px] font-mono px-2 py-1 rounded w-[160px] outline-none"
                                                            value={editUsername}
                                                            onChange={(e) => setEditUsername(e.target.value)}
                                                            onClick={(e) => e.stopPropagation()}
                                                            onKeyDown={(e) => {
                                                                if (e.key === 'Enter') handleEditSave(profile.id);
                                                                if (e.key === 'Escape') setEditingProfileId(null);
                                                            }}
                                                            placeholder="@username"
                                                        />
                                                        <div className="flex gap-1">
                                                            <button onClick={(e) => { e.stopPropagation(); handleEditSave(profile.id); }} className="text-[#00ff9d] text-[9px] font-bold bg-[#00ff9d]/10 px-2 py-1 rounded border border-[#00ff9d]/30 hover:bg-[#00ff9d]/30 transition-colors uppercase">OK</button>
                                                            <button onClick={(e) => { e.stopPropagation(); setEditingProfileId(null); }} className="text-red-400 text-[9px] font-bold bg-red-400/10 px-2 py-1 rounded border border-red-400/30 hover:bg-red-400/30 transition-colors">X</button>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <h3 className="font-bold text-sm text-white tracking-wide truncate max-w-[160px]" title={profile.label}>{profile.label}</h3>
                                                        <p className={clsx(
                                                            "font-mono text-[10px] leading-none",
                                                            statusColor === 'error' ? "text-[#ff2a2a]/60" :
                                                                statusColor === 'warn' ? "text-[#ffb02a]/60" :
                                                                    "text-synapse-primary/40"
                                                        )}>
                                                            {profile.username ? `@${profile.username}` : health === 'error' ? 'TOKEN_EXPIRED' : health === 'inactive' ? 'RATE_LIMITED' : profile.username || 'CONNECTED'}
                                                        </p>
                                                    </>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="flex items-center gap-1.5 justify-end">
                                                {profile.proxy_id && (
                                                    <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-synapse-primary/10 border border-synapse-primary/20 mr-1" title={`Proxy Node Linked (ID: ${profile.proxy_id})`}>
                                                        <span className="material-symbols-outlined text-[11px] text-synapse-primary glow-text">security</span>
                                                        <span className="text-[8px] tracking-widest uppercase font-mono text-synapse-primary font-bold">SECURE</span>
                                                    </div>
                                                )}
                                                <span className={clsx("w-1.5 h-1.5 rounded-full", statusDot, health === 'error' && 'shadow-[0_0_8px_#ff2a2a]')}></span>
                                                <span className={clsx("text-[10px] font-mono font-bold uppercase tracking-widest", statusText)}>{statusLabel}</span>
                                            </div>
                                            <label className="flex justify-end mt-2 cursor-pointer" aria-label={`Selecionar ${profile.label}`}>
                                                <input
                                                    type="checkbox"
                                                    checked={isSelected}
                                                    onChange={(e) => { e.stopPropagation(); handleSelect(profile.id); }}
                                                    className={clsx(
                                                        "size-3.5 rounded bg-black/50 cursor-pointer",
                                                        statusColor === 'error' ? "border-[#ff2a2a]/30 text-[#ff2a2a] focus:ring-[#ff2a2a]/50" :
                                                            statusColor === 'warn' ? "border-[#ffb02a]/30 text-[#ffb02a] focus:ring-[#ffb02a]/50" :
                                                                "border-synapse-primary/30 text-synapse-primary focus:ring-synapse-primary/50"
                                                    )}
                                                    onClick={(e) => e.stopPropagation()}
                                                />
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                {/* ═══ LOG STREAM BACKGROUND ═══ */}
                                <div className="log-stream-background">
                                    <div className={clsx("space-y-2", statusColor === 'success' && 'opacity-60', statusColor === 'warn' && 'opacity-70')}>
                                        {fakeLogs.map((log, idx) => (
                                            <div key={idx} className="text-slate-500">
                                                <span className={clsx(
                                                    statusColor === 'error' ? "text-[#ff2a2a]/50" :
                                                        statusColor === 'warn' ? "text-[#ffb02a]/50" :
                                                            "text-synapse-primary/70"
                                                )}>[{log.time}]</span>{' '}
                                                <span className={log.typeColor}>{log.type}</span>{' '}
                                                {log.msg}
                                            </div>
                                        ))}
                                        {/* Critical exception block for error state */}
                                        {health === 'error' && (
                                            <>
                                                <div className="p-3 my-4 bg-[#ff2a2a]/10 border-l-2 border-[#ff2a2a] backdrop-blur-sm relative group">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <span className="text-[#ff2a2a] font-bold text-[9px] uppercase tracking-tighter">CRITICAL_EXCEPTION</span>
                                                        {profile.last_error_screenshot && (
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); setViewerImage(profile.last_error_screenshot!); }}
                                                                className="cursor-pointer hover:text-white transition-all"
                                                            >
                                                                <span className="material-symbols-outlined text-[16px] text-synapse-primary">visibility</span>
                                                            </button>
                                                        )}
                                                    </div>
                                                    <div className="text-[#ff2a2a] text-[10px] leading-relaxed font-mono">
                                                        [10:00:18] AuthFailure: OAuth token revoked by provider. System session terminated by upstream host.
                                                    </div>
                                                    <div className="absolute inset-0 bg-[#ff2a2a]/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
                                                </div>
                                                <div className="text-slate-500"><span className="text-[#ff2a2a]/50">[10:00:19]</span> <span className="text-[#ff2a2a]">FAIL</span> Auto-retry limit exceeded.</div>
                                                <div className="text-slate-500 italic text-slate-400 border-t border-white/5 pt-2 mt-4 text-center">SYSTEM HALTED. WAITING FOR REPAIR.</div>
                                            </>
                                        )}
                                        {health === 'inactive' && (
                                            <div className="text-slate-600 border-t border-white/5 pt-2 mt-4">... [Awaiting system command]</div>
                                        )}
                                        {health === 'healthy' && (
                                            <div className="text-slate-500 italic text-synapse-primary animate-pulse">_ EXEC_WAIT</div>
                                        )}
                                    </div>
                                </div>

                                {/* ═══ FOOTER — Proxy + Actions ═══ */}
                                <div className="holographic-footer">
                                    <div className="flex items-center gap-2 flex-1">
                                        <span className={clsx(
                                            "material-symbols-outlined text-[16px]",
                                            health === 'healthy' ? "text-[#00ff9d]/80" :
                                                health === 'error' ? "text-slate-500" :
                                                    "text-[#00ff9d]/60"
                                        )}>
                                            {profile.proxy_id ? 'verified_user' : 'public'}
                                        </span>
                                        <label className="sr-only" htmlFor={`proxy-tm-${profile.id}`}>Selecionar Proxy</label>
                                        <select
                                            id={`proxy-tm-${profile.id}`}
                                            value={profile.proxy_id || ""}
                                            onChange={(e) => updateProxy(profile.id, e.target.value ? parseInt(e.target.value) : null)}
                                            onClick={(e) => e.stopPropagation()}
                                            className={clsx(
                                                "terminal-proxy-select",
                                                statusColor === 'error' ? "border-slate-700" :
                                                    statusColor === 'warn' ? "border-[#ffb02a]/10" :
                                                        "border-synapse-primary/20 hover:border-synapse-primary/50 transition-colors"
                                            )}
                                            aria-label={`Proxy para ${profile.label}`}
                                        >
                                            <option value="">DIRECT_CON</option>
                                            {proxies.map(proxy => (
                                                <option key={proxy.id} value={proxy.id} title={proxy.name}>
                                                    {proxy.nickname ? `${proxy.nickname} (${proxy.name})` : proxy.name}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="flex gap-1.5">
                                        {(health === 'error' || health === 'expired') && (
                                            <button
                                                onClick={(e) => { e.stopPropagation(); setRepairProfile(profile); }}
                                                className="px-3 py-1 bg-[#ffb02a]/10 hover:bg-[#ffb02a]/20 text-[#ffb02a] text-[9px] font-bold uppercase rounded border border-[#ffb02a]/30 flex items-center gap-1 transition-all"
                                                aria-label={`Reparar perfil ${profile.label}`}
                                            >
                                                <span className="material-symbols-outlined text-[14px]">build</span> REPAIR
                                            </button>
                                        )}
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handleRefreshAvatar(profile.id); }}
                                            disabled={isRefreshing}
                                            className="px-3 py-1 bg-synapse-primary/10 hover:bg-synapse-primary/20 text-synapse-primary text-[9px] font-bold uppercase rounded border border-synapse-primary/30 flex items-center gap-1 transition-all disabled:opacity-50"
                                            aria-label={isRefreshing ? 'Sincronizando nó' : 'Sincronizar nó'}
                                        >
                                            <span className={clsx("material-symbols-outlined text-[14px]", isRefreshing && "animate-spin")}>sync</span> {isRefreshing ? '...' : 'SYNC'}
                                        </button>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (remoteSession?.active && remoteSession.profile_slug === profile.id) {
                                                    handleStopRemoteSession();
                                                } else {
                                                    handleStartRemoteSession(profile.id);
                                                }
                                            }}
                                            disabled={startingRemote || (remoteSession?.active && remoteSession.profile_slug !== profile.id)}
                                            className={clsx(
                                                "px-3 py-1 text-[9px] font-bold uppercase rounded border flex items-center gap-1 transition-all disabled:opacity-50",
                                                remoteSession?.active && remoteSession.profile_slug === profile.id
                                                    ? "bg-emerald-500/20 hover:bg-red-500/20 text-emerald-400 hover:text-red-400 border-emerald-500/30 hover:border-red-500/30"
                                                    : "bg-violet-500/10 hover:bg-violet-500/20 text-violet-400 border-violet-500/30"
                                            )}
                                            title={
                                                remoteSession?.active && remoteSession.profile_slug === profile.id
                                                    ? "Encerrar sessão VNC"
                                                    : remoteSession?.active
                                                        ? `Sessão VNC ativa para outro perfil (${remoteSession.profile_slug})`
                                                        : "Abrir browser remoto via VNC (resolver CAPTCHA)"
                                            }
                                        >
                                            <span className="material-symbols-outlined text-[14px]">
                                                {startingRemote ? 'hourglass_empty' : remoteSession?.active && remoteSession.profile_slug === profile.id ? 'stop_circle' : 'desktop_windows'}
                                            </span>
                                            {startingRemote ? '...' : remoteSession?.active && remoteSession.profile_slug === profile.id ? 'STOP' : 'VNC'}
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); promptDelete(profile.id); }}
                                            className="px-3 py-1 bg-[#ff2a2a]/5 hover:bg-[#ff2a2a]/15 text-[#ff2a2a] text-[9px] font-bold uppercase rounded border border-[#ff2a2a]/20 flex items-center gap-1 transition-all"
                                            aria-label={`Remover perfil ${profile.label}`}
                                        >
                                            <span className="material-symbols-outlined text-[14px]">delete</span> DROP
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}

                    {/* ═══ NEW NODE CARD ═══ */}
                    <div
                        className="holographic-card !border-dashed !border-synapse-primary/20 !bg-transparent flex items-center justify-center cursor-pointer group hover:!bg-synapse-primary/5 transition-all duration-500 overflow-hidden"
                        role="button"
                        aria-label="Adicionar novo perfil"
                        tabIndex={0}
                        onClick={() => {
                            setImportLabel('');
                            setImportCookies('');
                            setImportUsername('');
                            setImportAvatar('');
                            setImportProxyId(null);
                            setImportProxyServer('');
                            setImportProxyUser('');
                            setImportProxyPass('');
                            setProxyMode('existing');
                            setShowImportModal(true);
                        }}
                        onKeyDown={(e) => { if (e.key === 'Enter') setShowImportModal(true); }}
                    >
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(7,182,213,0.1)_0%,transparent_70%)] opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div className="text-center p-8 z-20">
                            <div className="size-24 rounded-full border border-synapse-primary/20 flex items-center justify-center mb-6 mx-auto group-hover:scale-110 group-hover:border-synapse-primary/50 group-hover:shadow-[0_0_30px_rgba(7,182,213,0.2)] transition-all duration-500 relative">
                                <span className="material-symbols-outlined text-4xl text-synapse-primary/40 group-hover:text-synapse-primary transition-colors tracking-widest">add</span>
                                <div className="absolute inset-0 rounded-full border border-synapse-primary/10 animate-ping opacity-20"></div>
                            </div>
                            <h3 className="font-outline text-2xl text-synapse-primary/30 group-hover:text-synapse-primary transition-colors tracking-[0.3em]">NEW_NODE</h3>
                            <p className="font-mono text-[9px] text-synapse-primary/20 tracking-widest mt-4 uppercase group-hover:text-synapse-primary/40 transition-colors">Initialize deployment sequence</p>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="w-full flex flex-col items-center justify-center py-20">
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

            <div className="fixed bottom-0 left-0 right-0 bg-[#030608]/90 backdrop-blur-xl border-t border-white/5 py-3 px-8 flex justify-between items-center text-[10px] font-mono text-slate-500 uppercase z-[100]">
                <div className="flex gap-12">
                    <span className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-synapse-primary rounded-full animate-pulse shadow-[0_0_8px_#07b6d5]"></span> UPLINK: {systemVitals ? systemVitals.uptime : 'SECURE'}</span>
                    <span>NODES_ONLINE: {profiles.filter(p => !pendingDeletes.has(p.id) && getHealthStatus(p) === 'healthy').length.toString().padStart(2, '0')}</span>
                    <span>TOTAL_NODES: {profiles.filter(p => !pendingDeletes.has(p.id)).length.toString().padStart(2, '0')}</span>
                </div>
                <div className="flex gap-8 items-center">
                    <div className="flex items-center gap-2">
                        <span className="text-synapse-primary/70">CORE_SYNC:</span>
                        <span className="text-white bg-synapse-primary/20 px-2 py-0.5 rounded tracking-widest border border-synapse-primary/10">{systemVitals ? `CPU ${systemVitals.cpu_percent}%` : 'STABLE'}</span>
                    </div>
                    <span className="text-synapse-primary flex items-center gap-1.5"><span className="w-1 h-1 bg-synapse-primary rounded-full"></span> {systemVitals ? `MEM ${systemVitals.mem_percent}%` : 'System Operational'}</span>
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

            {/* Delete Confirmation Modal — SYN-52 */}
            <Modal
                isOpen={!!deleteConfirmationId}
                onClose={() => setDeleteConfirmationId(null)}
                title="Confirmar Exclusão"
            >
                <div className="text-center py-4">
                    <div className="mb-4 flex justify-center">
                        <div className="size-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
                            <TrashIcon className="size-8 text-red-400" />
                        </div>
                    </div>
                    <p className="text-slate-300 mb-2">
                        Tem certeza que deseja excluir o perfil
                        <span className="text-white font-bold ml-1">
                            {profiles.find(p => p.id === deleteConfirmationId)?.label || deleteConfirmationId}
                        </span>
                        ?
                    </p>
                    <p className="text-slate-500 text-xs">
                        O perfil será removido do sistema após 8 segundos. Você poderá desfazer via toast.
                    </p>
                </div>
                <div className="flex justify-center gap-3 pt-2">
                    <NeonButton variant="ghost" onClick={() => setDeleteConfirmationId(null)}>
                        Cancelar
                    </NeonButton>
                    <button
                        onClick={confirmDelete}
                        className="px-6 py-2 bg-red-500/20 border border-red-500/40 text-red-400 hover:bg-red-500/30 hover:text-red-300 text-xs font-bold uppercase tracking-widest transition-all"
                    >
                        Confirmar Exclusão
                    </button>
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

                <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">Avatar URL <span className="text-xs opacity-50 lowercase float-right">(opcional)</span></label>
                        <input
                            type="text"
                            value={importAvatar}
                            onChange={(e) => setImportAvatar(e.target.value)}
                            placeholder="https://..."
                            className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all"
                        />
                    </div>
                    <div>
                        <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">Fingerprint UA <span className="text-xs opacity-50 lowercase float-right">(opcional)</span></label>
                        <select
                            value={importFingerprint}
                            onChange={(e) => setImportFingerprint(e.target.value)}
                            className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all"
                        >
                            <option value="">[ DEFAULT ] (Windows Chrome 122)</option>
                            <option value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36">Windows Desktop (Chrome 125)</option>
                            <option value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0">Windows Desktop (Edge 125)</option>
                            <option value="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15">Mac OS X (Safari 17.4)</option>
                            <option value="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36">Mac OS X (Chrome 125)</option>
                        </select>
                    </div>
                    <div className="col-span-2">
                        <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">Sub-Rede Proxy <span className="text-xs opacity-50 lowercase float-right">(opcional)</span></label>
                        {/* Mode Toggle */}
                        <div className="flex gap-2 mb-3">
                            <button
                                type="button"
                                onClick={() => setProxyMode('existing')}
                                className={clsx(
                                    "px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider border transition-all",
                                    proxyMode === 'existing'
                                        ? "bg-synapse-primary/20 border-synapse-primary/50 text-synapse-primary"
                                        : "bg-black/30 border-white/10 text-gray-500 hover:text-gray-300"
                                )}
                            >
                                Selecionar Existente
                            </button>
                            <button
                                type="button"
                                onClick={() => setProxyMode('new')}
                                className={clsx(
                                    "px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider border transition-all",
                                    proxyMode === 'new'
                                        ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400"
                                        : "bg-black/30 border-white/10 text-gray-500 hover:text-gray-300"
                                )}
                            >
                                + Novo Proxy
                            </button>
                        </div>

                        {proxyMode === 'existing' ? (
                            <select
                                value={importProxyId || ""}
                                onChange={(e) => setImportProxyId(e.target.value ? parseInt(e.target.value) : null)}
                                className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all"
                            >
                                <option value="">[ DIRECT ] (IP Local)</option>
                                {proxies.map(proxy => (
                                    <option key={proxy.id} value={proxy.id}>
                                        {proxy.name} — {proxy.server}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <div className="grid grid-cols-3 gap-2">
                                <input
                                    type="text"
                                    value={importProxyServer}
                                    onChange={(e) => setImportProxyServer(e.target.value)}
                                    placeholder="IP:Porta (200.234.150.63:50100)"
                                    className="col-span-3 px-4 py-3 rounded-lg bg-black/50 border border-emerald-500/20 text-white font-mono text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all placeholder:text-gray-600"
                                />
                                <input
                                    type="text"
                                    value={importProxyUser}
                                    onChange={(e) => setImportProxyUser(e.target.value)}
                                    placeholder="Usuário"
                                    className="px-3 py-2 rounded-lg bg-black/50 border border-white/10 text-white text-xs focus:border-emerald-500 outline-none transition-all placeholder:text-gray-600"
                                />
                                <input
                                    type="password"
                                    value={importProxyPass}
                                    onChange={(e) => setImportProxyPass(e.target.value)}
                                    placeholder="Senha"
                                    className="col-span-1 px-3 py-2 rounded-lg bg-black/50 border border-white/10 text-white text-xs focus:border-emerald-500 outline-none transition-all placeholder:text-gray-600"
                                />
                                <input
                                    type="text"
                                    value={importProxyNickname}
                                    onChange={(e) => setImportProxyNickname(e.target.value)}
                                    placeholder="Nickname (opcional)"
                                    className="col-span-1 px-3 py-2 rounded-lg bg-black/50 border border-white/10 text-white text-xs focus:border-emerald-500 outline-none transition-all placeholder:text-gray-600"
                                />
                                <div className="col-span-3 flex items-center justify-between mt-1">
                                    <div className="flex items-center text-[9px] text-emerald-500/50 font-mono">
                                        <span className="material-symbols-outlined text-[14px] mr-1">shield_lock</span>
                                        TUNNEL
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {proxyLocation && (
                                            <span className="text-[10px] text-emerald-400 font-bold px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded">
                                                ✓ {proxyLocation.city}, {proxyLocation.region} ({proxyLocation.country})
                                            </span>
                                        )}
                                        {proxyError && (
                                            <span className="text-[10px] text-red-400 font-bold px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded">
                                                ❌ {proxyError}
                                            </span>
                                        )}
                                        <button
                                            type="button"
                                            onClick={handleValidateProxy}
                                            disabled={!importProxyServer || validatingProxy}
                                            className="text-[10px] font-bold text-emerald-500 hover:text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 rounded transition-colors disabled:opacity-50"
                                        >
                                            {validatingProxy ? "TESTANDO CONEXÃO..." : "TESTAR PROXY ✨"}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
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
            </Modal >

            {/* ═══ VNC FÁBRICA MODAL ═══ */}
            <Modal
                isOpen={showFactoryModal}
                onClose={resetFactoryModal}
                title="VNC Fábrica — Criar Novo Perfil"
            >
                {/* Step indicator */}
                <div className="flex items-center gap-2 mb-6">
                    {([{ n: 1, label: 'Proxy' }, { n: 2, label: 'Login' }, { n: 3, label: 'Sucesso' }] as { n: 1 | 2 | 3; label: string }[]).map(({ n, label }) => (
                        <div key={n} className="flex items-center gap-2">
                            <div className={clsx(
                                'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border transition-colors',
                                factoryStep >= n
                                    ? 'bg-synapse-primary/20 border-synapse-primary text-synapse-primary'
                                    : 'bg-white/5 border-white/10 text-gray-600'
                            )}>
                                {factoryStep > n ? '✓' : n}
                            </div>
                            <span className={clsx(
                                'text-xs font-mono uppercase tracking-wider transition-colors',
                                factoryStep >= n ? 'text-synapse-primary' : 'text-gray-600'
                            )}>{label}</span>
                            {n < 3 && <div className={clsx('w-6 h-px', factoryStep > n ? 'bg-synapse-primary/50' : 'bg-white/10')} />}
                        </div>
                    ))}
                </div>

                {/* ETAPA 1: Seleção de Proxy */}
                {factoryStep === 1 && (
                    <div className="space-y-4">
                        <p className="text-sm text-gray-400">
                            Selecione o proxy ISP fixo para este perfil. A sessão VNC será iniciada com esse proxy desde o início — garantindo que o TikTok associe a conta ao IP correto.
                        </p>
                        <div>
                            <label className="block text-xs text-gray-400 mb-2 uppercase font-bold tracking-wider">
                                Proxy <span className="text-red-400">*</span>
                            </label>
                            <select
                                value={factoryProxyId ?? ''}
                                onChange={(e) => setFactoryProxyId(e.target.value ? parseInt(e.target.value) : null)}
                                className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary outline-none"
                            >
                                <option value="">-- Selecione um proxy --</option>
                                {proxies.filter((p: any) => p.active).map((proxy: any) => (
                                    <option key={proxy.id} value={proxy.id}>
                                        {proxy.nickname ? `${proxy.nickname} — ${proxy.server}` : `${proxy.name} — ${proxy.server}`}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-gray-400 mb-2 uppercase font-bold tracking-wider">
                                Label do Perfil <span className="text-gray-600 normal-case font-normal">(opcional)</span>
                            </label>
                            <input
                                type="text"
                                value={factoryLabel}
                                onChange={(e) => setFactoryLabel(e.target.value)}
                                placeholder="Ex: Canal Principal BR"
                                className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary outline-none"
                            />
                        </div>
                        <div className="flex justify-end gap-3 pt-2">
                            <NeonButton variant="ghost" onClick={resetFactoryModal}>Cancelar</NeonButton>
                            <NeonButton
                                variant="primary"
                                onClick={handleStartFactorySession}
                                disabled={!factoryProxyId || startingFactory}
                            >
                                {startingFactory
                                    ? <><ArrowPathIcon className="w-4 h-4 animate-spin mr-2 inline" />Iniciando...</>
                                    : 'Iniciar Sessão VNC'}
                            </NeonButton>
                        </div>
                    </div>
                )}

                {/* ETAPA 2: VNC ativo + Capturar */}
                {factoryStep === 2 && factorySession?.novnc_url && (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between bg-violet-500/10 border border-violet-500/20 rounded-lg px-4 py-2">
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-[0_0_8px_#34d399]" />
                                <span className="text-violet-300 font-mono text-xs font-bold uppercase tracking-widest">Sessão Fábrica Ativa</span>
                            </div>
                            <button
                                onClick={handleStopFactorySession}
                                className="text-xs text-red-400 hover:text-red-300 font-mono uppercase border border-red-500/30 px-3 py-1 rounded hover:bg-red-500/10 transition-all"
                            >
                                Encerrar
                            </button>
                        </div>

                        <div className="rounded-lg overflow-hidden border border-violet-500/20" style={{ height: '480px' }}>
                            <iframe
                                src={factorySession.novnc_url}
                                className="w-full h-full border-0"
                                title="VNC Fábrica — Login TikTok"
                                allow="clipboard-read; clipboard-write"
                            />
                        </div>

                        <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-lg px-4 py-3 text-xs text-yellow-300/80 font-mono space-y-1">
                            <p>1. Faça login no TikTok via VNC acima.</p>
                            <p>2. Aguarde a página inicial carregar (confirma login bem-sucedido).</p>
                            <p>3. Clique em <strong>"Capturar Perfil"</strong> abaixo.</p>
                        </div>

                        <div className="flex justify-end">
                            <NeonButton
                                variant="primary"
                                onClick={handleCaptureFactoryProfile}
                                disabled={factoryCapturing}
                                className="flex items-center gap-2"
                            >
                                {factoryCapturing
                                    ? <><ArrowPathIcon className="w-4 h-4 animate-spin mr-1 inline" />Capturando...</>
                                    : 'Capturar Perfil'}
                            </NeonButton>
                        </div>
                    </div>
                )}

                {/* ETAPA 3: Sucesso */}
                {factoryStep === 3 && factoryResult && (
                    <div className="text-center py-6 space-y-4">
                        <div className="size-20 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto">
                            <CheckCircleIcon className="size-10 text-emerald-400" />
                        </div>
                        <h3 className="text-xl font-bold text-white">Perfil Capturado!</h3>
                        <p className="text-gray-400 text-sm">
                            {factoryResult.username ? `@${factoryResult.username}` : factoryResult.label} foi adicionado ao sistema com proxy vinculado.
                        </p>
                        <p className="text-xs text-gray-600 font-mono">{factoryResult.profile_id}</p>
                        <div className="flex justify-center pt-2">
                            <NeonButton variant="primary" onClick={resetFactoryModal}>Fechar</NeonButton>
                        </div>
                    </div>
                )}
            </Modal>
        </>
    );
}
