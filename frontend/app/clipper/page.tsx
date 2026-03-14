'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { apiClient } from '../lib/api';
import { toast } from '../utils/toast';
import { ClipJobStatus } from '../types';
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors, DragEndEvent } from '@dnd-kit/core';
import { arrayMove, SortableContext, sortableKeyboardCoordinates, verticalListSortingStrategy, useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    status: ClipJobStatus;
    current_step: string;
    progress_pct: number;
    error_message?: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    channel_name?: string;
    priority?: number;
}

interface ProfileOption {
    slug: string;
    username: string;
    label: string;
    avatar_url: string | null;
}

interface ClipDetail {
    index: number;
    title: string | null;
    duration: number | null;
    views: number | null;
    creator: string | null;
    game: string | null;
}

interface PendingVideo {
    id: number;
    clip_job_id: number | null;
    video_path: string;
    thumbnail_path: string | null;
    streamer_name: string | null;
    title: string | null;
    duration_seconds: number | null;
    file_size_bytes: number | null;
    caption: string | null;
    hashtags: string[] | null;
    caption_generated: boolean;
    transcript: string | null;
    clips?: ClipDetail[] | null;
    status: string;
    created_at: string;
    target_army_id: number | null;
    available_profiles: ProfileOption[] | null;
}

type Tab = 'targets' | 'queue' | 'armies' | 'approval';

function SortableClip({ clip }: { clip: ClipDetail }) {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: clip.index });
    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            className="flex items-center gap-2 bg-black/40 border border-white/10 hover:border-cyan-500/30 rounded p-2 cursor-grab active:cursor-grabbing transition-colors mb-1.5"
        >
            <span className="material-symbols-outlined text-slate-500 text-[14px]">drag_indicator</span>
            <div className="flex-1 min-w-0">
                <p className="text-[10px] text-white font-mono truncate">{clip.title || `Clip #${clip.index + 1}`}</p>
                <div className="flex gap-2 mt-0.5">
                    <span className="text-[9px] text-emerald-400 font-mono flex items-center gap-0.5">
                        <span className="material-symbols-outlined text-[10px]">timer</span>
                        {clip.duration ? Math.floor(clip.duration) : '--'}s
                    </span>
                    <span className="text-[9px] text-cyan-400 font-mono flex items-center gap-0.5">
                        <span className="material-symbols-outlined text-[10px]">visibility</span>
                        {clip.views || '--'}
                    </span>
                </div>
            </div>
        </div>
    );
}

function ClipReorderList({ initialClips, onReorder }: { initialClips: ClipDetail[], onReorder: (newOrder: number[]) => Promise<void> }) {
    const [clips, setClips] = useState(initialClips);
    const [isSaving, setIsSaving] = useState(false);
    
    useEffect(() => { setClips(initialClips); }, [initialClips]);

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        if (active.id !== over?.id) {
            setClips((items) => {
                const oldIndex = items.findIndex((i) => i.index === active.id);
                const newIndex = items.findIndex((i) => i.index === over?.id);
                return arrayMove(items, oldIndex, newIndex);
            });
        }
    };

    const hasChanges = JSON.stringify(clips.map(c => c.index)) !== JSON.stringify(initialClips.map(c => c.index));

    const handleSave = async () => {
        setIsSaving(true);
        await onReorder(clips.map(c => c.index));
        setIsSaving(false);
    };

    return (
        <div className="border-t border-white/5 pt-2 mt-2">
            <h4 className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5 px-1">
                <span className="material-symbols-outlined text-[14px]">reorder</span>
                ORDEM DOS CLIPES ({clips.length})
            </h4>
            <div className="max-h-[150px] overflow-y-auto custom-scrollbar pr-1">
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                    <SortableContext items={clips.map(c => c.index)} strategy={verticalListSortingStrategy}>
                        {clips.map(clip => (
                            <SortableClip key={clip.index} clip={clip} />
                        ))}
                    </SortableContext>
                </DndContext>
            </div>
            {hasChanges && (
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="w-full mt-2 flex items-center justify-center gap-1.5 py-1.5 text-[9px] font-mono uppercase tracking-wider border border-cyan-500/30 text-cyan-400 rounded bg-cyan-500/10 hover:bg-cyan-500/20 transition-colors disabled:opacity-50"
                >
                    <span className="material-symbols-outlined text-[12px]">save</span>
                    {isSaving ? 'SALVANDO...' : 'SALVAR E RE-AGENDAR'}
                </button>
            )}
        </div>
    );
}

export default function ClipperPage() {
    const [activeTab, setActiveTab] = useState<'targets' | 'queue' | 'armies' | 'approval'>('targets');
    const [targets, setTargets] = useState<Target[]>([]);
    const [urlInput, setUrlInput] = useState("");
    const [selectedArmyId, setSelectedArmyId] = useState<number | "">("");
    const [isLoading, setIsLoading] = useState(false);
    const [profiles, setProfiles] = useState<Profile[]>([]);
    const [armies, setArmies] = useState<Army[]>([]);

    // Queue state (moved from home page)
    const [items, setItems] = useState<ClipJobResponse[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [queueLoading, setQueueLoading] = useState(true);
    const [vitals, setVitals] = useState<{ cpu_percent: number; uptime: string } | null>(null);

    // Approval Queue Data
    const [pendingVideos, setPendingVideos] = useState<PendingVideo[]>([]);
    const [approvalLoading, setApprovalLoading] = useState(true);
    const [refreshingList, setRefreshingList] = useState(false);
    const [selectedVideo, setSelectedVideo] = useState<PendingVideo | null>(null);
    const [showApprovalModal, setShowApprovalModal] = useState(false);
    const [postType, setPostType] = useState<'smart' | 'specific' | 'now'>('smart');
    const [selectedDate, setSelectedDate] = useState('');
    const [selectedTime, setSelectedTime] = useState('12:00');
    const [submittingApproval, setSubmittingApproval] = useState(false);
    const [confirmReject, setConfirmReject] = useState<number | null>(null);
    const [selectedProfileSlug, setSelectedProfileSlug] = useState<string>('');

    // Caption Accordion State
    const [expandedCaptionId, setExpandedCaptionId] = useState<number | null>(null);
    const [captionDrafts, setCaptionDrafts] = useState<Record<number, { caption: string; hashtags: string[] }>>({});
    const [generatingCaption, setGeneratingCaption] = useState<number | null>(null);
    const [captionTone, setCaptionTone] = useState<string>('Viral');
    const [savingCaption, setSavingCaption] = useState<number | null>(null);

    const [targetToDelete, setTargetToDelete] = useState<number | null>(null);
    const [armyToDelete, setArmyToDelete] = useState<number | null>(null);
    const [newArmy, setNewArmy] = useState({ name: '', color: '#00f0ff', icon: 'swords', profile_ids: [] as number[] });

    // Pipeline accordion state — active sections auto-expand
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['processing', 'waiting']));
    const toggleSection = (key: string) => {
        setExpandedSections(prev => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });
    };

    // ── Targets logic ──
    const fetchTargets = async () => {
        try {
            const data = await apiClient.get<Target[]>('/api/clipper/targets');
            setTargets(data);
        } catch (error) {
            console.warn("Failed to fetch targets (API might be down)");
        }
    };

    const fetchProfiles = async () => {
        try {
            const data = await apiClient.get<Profile[]>('/api/v1/profiles/list');
            setProfiles(data || []);
        } catch (err) {
            console.warn("Failed to fetch profiles (API might be down)");
        }
    };

    const fetchArmies = async () => {
        try {
            const data = await apiClient.get<Army[]>('/api/v1/armies/');
            setArmies(data || []);
        } catch (err) {
            console.warn("Failed to fetch armies (API might be down)");
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
                payload.army_id = selectedArmyId;
            }

            await apiClient.post('/api/clipper/targets', payload);
            setUrlInput("");
            toast.success("Novo alvo detectado e adicionado à órbita.");
            await fetchTargets();
        } catch (error: any) {
            toast.error(`Erro: ${error?.data?.detail || "Erro de conexão com o painel orbital."}`);
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
            await apiClient.delete(`/api/clipper/targets/${id}`);
            toast.success("Alvo removido da órbita.");
            await fetchTargets();
        } catch (error) {
            toast.error("Falha ao remover o alvo.");
        }
    };

    const handleCreateArmy = async () => {
        if (!newArmy.name.trim()) {
            toast.error("O Exército precisa de um nome.");
            return;
        }
        setIsLoading(true);
        try {
            await apiClient.post('/api/v1/armies/', newArmy);
            toast.success("Exército formado com sucesso!");
            setNewArmy({ name: '', color: '#00f0ff', icon: 'swords', profile_ids: [] });
            await fetchArmies();
        } catch (error) {
            toast.error("Falha ao criar o Exército.");
        } finally {
            setIsLoading(false);
        }
    };

    const requestDeleteArmy = (id: number) => {
        setArmyToDelete(id);
    };

    const confirmDeleteArmy = async () => {
        if (!armyToDelete) return;
        const id = armyToDelete;
        setArmyToDelete(null);

        try {
            await apiClient.delete(`/api/v1/armies/${id}`);
            toast.success("Exército dissolvido.");
            await fetchArmies();
            await fetchTargets();
        } catch (error) {
            toast.error("Falha ao dissolver Exército.");
        }
    };

    const cancelDeleteArmy = () => {
        setArmyToDelete(null);
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
            await apiClient.put(`/api/v1/armies/${armyId}`, { profile_ids: newProfileIds });
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
            await apiClient.patch(`/api/clipper/targets/${id}`, { active: !currentActive });
            toast.success(`Alvo ${!currentActive ? 'ativado' : 'desativado'} com sucesso.`);
            await fetchTargets();
        } catch (error) {
            toast.error("Falha ao modificar o status do alvo.");
        }
    };

    const handleForceCheckTarget = async (id: number) => {
        setIsLoading(true);
        toast.info("Iniciando varredura manual do radar...", { id: `force-${id}` });
        try {
            const data = await apiClient.post<any>(`/api/clipper/targets/${id}/check`);
            toast.success(data.message, { id: `force-${id}`, duration: 5000 });
            await fetchTargets();
        } catch (error: any) {
            toast.error(`Falha: ${error?.data?.detail || "Erro de conexão ao forçar varredura."}`, { id: `force-${id}` });
        } finally {
            setIsLoading(false);
        }
    };

    // ── Queue / Esteira logic ──
    const fetchPending = useCallback(async () => {
        try {
            const data = await apiClient.get<ClipJobResponse[]>('/api/clipper/pipeline');
            setItems(data || []);
            setCurrentIndex(0);
        } catch (err) {
            console.error('Fetch pending error:', err);
        } finally {
            setQueueLoading(false);
        }
    }, []);

    // ── Approval Queue Logic ──
    const fetchPendingVideos = useCallback(async (manual = false) => {
        if (manual) setRefreshingList(true);
        try {
            const data = await apiClient.get<PendingVideo[]>('/api/v1/factory/pending');
            setPendingVideos(data);
        } catch (error) {
            console.error('Error fetching pending videos:', error);
        } finally {
            setApprovalLoading(false);
            if (manual) setRefreshingList(false);
        }
    }, []);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (activeTab === 'queue') {
            fetchPending();
            interval = setInterval(() => {
                fetchPending();
            }, 3000);
        } else if (activeTab === 'approval') {
            setApprovalLoading(true);
            fetchPendingVideos();
            interval = setInterval(() => {
                fetchPendingVideos();
            }, 10000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [activeTab, fetchPending, fetchPendingVideos]);

    const handleApprove = (video: PendingVideo) => {
        setSelectedVideo(video);
        setSelectedProfileSlug('');
        setShowApprovalModal(true);
    };

    const handleReject = async (videoId: number) => {
        setConfirmReject(videoId);
    };

    const confirmRejectVideo = async () => {
        if (!confirmReject) return;
        try {
            await apiClient.delete(`/api/v1/factory/reject/${confirmReject}`);
            await fetchPendingVideos();
            toast.info('Vídeo rejeitado e removido.');
        } catch (error) {
            toast.error('Erro ao rejeitar vídeo');
        } finally {
            setConfirmReject(null);
        }
    };

    const handleReorderClips = async (videoId: number, newOrder: number[]) => {
        const toastId = toast.loading('Re-agendando job com nova ordem...');
        try {
            const response = await apiClient.post(`/api/v1/factory/reorder/${videoId}`, { order: newOrder });
            await fetchPendingVideos();
            toast.success((response as any).data?.message || 'Ordem dos clipes atualizada!', { id: toastId });
        } catch (error: any) {
            toast.error(error?.data?.detail || 'Erro ao reordenar clipes', { id: toastId });
        }
    };

    // ── Caption Generation & Save ──
    const handleGenerateCaption = async (videoId: number) => {
        setGeneratingCaption(videoId);
        try {
            const result = await apiClient.post(`/api/v1/factory/generate-caption/${videoId}`, {
                tone: captionTone,
                length: 'short',
                include_hashtags: true,
                instruction: '',
            });
            const data = result as any;
            setCaptionDrafts(prev => ({
                ...prev,
                [videoId]: { caption: data.caption || '', hashtags: data.hashtags || [] }
            }));
            toast.success('Descrição gerada pelo Oracle!');
        } catch (error: any) {
            toast.error(error?.data?.detail || 'Erro ao gerar descrição');
        } finally {
            setGeneratingCaption(null);
        }
    };

    const handleSaveCaption = async (videoId: number) => {
        const draft = captionDrafts[videoId];
        if (!draft) return;
        setSavingCaption(videoId);
        try {
            await apiClient.patch(`/api/v1/factory/caption/${videoId}`, {
                caption: draft.caption,
                hashtags: draft.hashtags,
            });
            toast.success('Descrição salva!');
            await fetchPendingVideos();
        } catch (error: any) {
            toast.error(error?.data?.detail || 'Erro ao salvar descrição');
        } finally {
            setSavingCaption(null);
        }
    };

    const toggleCaptionAccordion = (videoId: number) => {
        if (expandedCaptionId === videoId) {
            setExpandedCaptionId(null);
        } else {
            setExpandedCaptionId(videoId);
            // Inicializar draft com caption existente se houver
            const video = pendingVideos.find(v => v.id === videoId);
            if (video && !captionDrafts[videoId]) {
                setCaptionDrafts(prev => ({
                    ...prev,
                    [videoId]: {
                        caption: video.caption || '',
                        hashtags: video.hashtags || [],
                    }
                }));
            }
        }
    };

    const handleConfirmVideo = async () => {
        if (!selectedVideo) return;

        // Validação: modo específico requer data
        if (postType === 'specific' && !selectedDate) {
            toast.error('Selecione uma data para agendamento específico.');
            return;
        }

        setSubmittingApproval(true);

        try {
            // Salvar caption pendente antes de aprovar (se editada)
            const draft = captionDrafts[selectedVideo.id];
            if (draft && (draft.caption || draft.hashtags.length > 0)) {
                await apiClient.patch(`/api/v1/factory/caption/${selectedVideo.id}`, {
                    caption: draft.caption,
                    hashtags: draft.hashtags,
                });
            }

            const approveBody: Record<string, any> = {
                schedule_mode: postType,
            };
            if (selectedProfileSlug) {
                approveBody.profile_slug = selectedProfileSlug;
            }
            if (postType === 'specific') {
                approveBody.schedule_date = selectedDate;
                approveBody.schedule_time = selectedTime || '12:00';
            }

            const result = await apiClient.post(`/api/v1/factory/approve/${selectedVideo.id}`, approveBody);

            setShowApprovalModal(false);
            setSelectedVideo(null);
            setPostType('smart');
            setSelectedDate('');
            setSelectedTime('12:00');
            await fetchPendingVideos();

            const res = result as any;
            const profileName = res?.profile || selectedProfileSlug || 'auto';
            const scheduledTime = res?.scheduled_time;
            const failedCount = res?.failed || 0;
            const scheduledCount = res?.scheduled || 0;
            const timeStr = scheduledTime
                ? ` para ${new Date(scheduledTime).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}`
                : '';

            if (failedCount > 0 && scheduledCount === 0) {
                toast.error(`Aprovado mas falhou ao agendar no perfil @${profileName}. Verifique o scheduler.`);
            } else if (failedCount > 0) {
                toast.success(`Vídeo aprovado no perfil @${profileName}${timeStr}, mas ${failedCount} tentativa(s) falharam.`);
            } else {
                toast.success(`Vídeo aprovado e agendado no perfil @${profileName}${timeStr}!`);
            }
        } catch (error: any) {
            toast.error(error?.data?.detail || 'Erro ao aprovar vídeo. Tente novamente.');
        } finally {
            setSubmittingApproval(false);
        }
    };

    const timeOptions = [];
    for (let h = 0; h < 24; h++) {
        for (let m = 0; m < 60; m += 5) {
            const hour = h.toString().padStart(2, '0');
            const minute = m.toString().padStart(2, '0');
            timeOptions.push(`${hour}:${minute}`);
        }
    }

    // Fetch vitals for header
    useEffect(() => {
        const fetchVitals = async () => {
            try {
                const data = await apiClient.get<any>('/api/v1/telemetry/vitals');
                setVitals(data);
            } catch (err) {
                // Ignore silent telemetry errors in UI
            }
        };
        fetchVitals();
        const interval = setInterval(fetchVitals, 5000);
        return () => clearInterval(interval);
    }, []);


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
                    {items.filter(job => job.status !== 'completed').length > 0 && (
                        <span className="bg-amber-500/20 text-amber-400 text-[10px] px-1.5 py-0.5 rounded-md">{items.filter(job => job.status !== 'completed').length}</span>
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
                <div className="w-px h-6 bg-white/10 mx-2"></div>
                <button
                    onClick={() => setActiveTab('approval')}
                    className={`px-5 py-2.5 text-xs font-mono font-bold uppercase tracking-widest rounded-lg transition-all duration-200 flex items-center gap-2 ${activeTab === 'approval'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-[0_0_15px_-3px_rgba(16,185,129,0.3)]'
                        : 'text-slate-500 hover:text-white hover:bg-white/5 border border-transparent'
                        }`}
                >
                    <span className="material-symbols-outlined text-[18px]">done_all</span>
                    Aprovação
                    {pendingVideos.length > 0 && (
                        <span className="bg-emerald-500/20 text-emerald-400 text-[10px] px-1.5 py-0.5 rounded-md">{pendingVideos.length}</span>
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
                                            onChange={(e) => setSelectedArmyId(e.target.value ? parseInt(e.target.value) : "")}
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
                                        <div className="p-4 bg-gradient-to-b from-cyan-900/10 to-transparent border-b border-white/5">
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
                                                <div key={target.id} className={`group relative bg-cosmic-hull border border-cosmic-border hover:border-cosmic-glowBorder transition-all duration-300 overflow-hidden rounded-xl shadow-lg ${!target.active ? 'opacity-60 hover:opacity-100 grayscale contrast-125' : 'hover:shadow-[0_0_20px_rgba(0,240,255,0.15)]'}`}>
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

                                                    <div className="h-32 bg-cosmic-void border-b border-cosmic-border relative flex items-center justify-center overflow-hidden">
                                                        {/* Banner / Capa do Canal */}
                                                        {target.offline_image_url || target.profile_image_url ? (
                                                            <>
                                                                <img
                                                                    src={target.offline_image_url || target.profile_image_url}
                                                                    alt="Cover"
                                                                    className="absolute inset-0 w-full h-full object-cover opacity-40 scale-105 transition-transform duration-700 group-hover:scale-110"
                                                                />
                                                                <div className="absolute inset-0 bg-gradient-to-t from-cosmic-hull via-cosmic-hull/60 to-transparent" />
                                                            </>
                                                        ) : (
                                                            <div className="absolute inset-0 bg-gradient-to-br from-cosmic-hull to-cosmic-void" />
                                                        )}

                                                        {/* Avatar / Box Art */}
                                                        <div className={`relative z-10 ${target.target_type === 'category' ? 'w-16 h-20 rounded-md' : 'w-16 h-16 rounded-full'} border-2 ${target.active ? 'border-cyan-400/70 shadow-[0_0_18px_rgba(0,240,255,0.4)]' : 'border-slate-700'} bg-black overflow-hidden flex items-center justify-center mt-4 ring-2 ring-black`}>
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
                                <span className="material-symbols-outlined text-4xl text-slate-600">movie_filter</span>
                            </div>
                            <h2 className="text-white text-2xl font-display font-bold mb-2">Esteira Ociosa</h2>
                            <p className="text-slate-500 font-mono text-sm leading-relaxed">
                                Nenhum clip em processamento agora. O radar detecta clipes automaticamente — eles aparecerão aqui ao entrar na fila.
                            </p>
                            {/* Pipeline steps preview */}
                            <div className="mt-8 flex items-center justify-center gap-1">
                                {[
                                    { icon: 'download', label: 'Download' },
                                    { icon: 'mic', label: 'Whisper' },
                                    { icon: 'closed_caption', label: 'Legendas' },
                                    { icon: 'movie_edit', label: 'FFmpeg' },
                                    { icon: 'join_inner', label: 'Stitch' },
                                ].map((step, i, arr) => (
                                    <React.Fragment key={step.icon}>
                                        <div className="flex flex-col items-center gap-1">
                                            <div className="w-8 h-8 rounded-full bg-slate-800/60 border border-white/5 flex items-center justify-center">
                                                <span className="material-symbols-outlined text-[14px] text-slate-600">{step.icon}</span>
                                            </div>
                                            <span className="text-[8px] font-mono text-slate-700 uppercase">{step.label}</span>
                                        </div>
                                        {i < arr.length - 1 && <span className="w-5 h-px bg-white/5 mb-3 shrink-0" />}
                                    </React.Fragment>
                                ))}
                            </div>
                            <div className="mt-4 flex items-center justify-center gap-2 text-[10px] font-mono text-cyan-500/40">
                                <span className="w-1.5 h-1.5 bg-cyan-500/40 rounded-full animate-pulse"></span>
                                AGUARDANDO NOVOS EVENTOS
                            </div>
                        </div>
                    ) : (() => {
                        // ═══ Definição das Seções de Status ═══
                        const PIPELINE_SECTIONS = [
                            {
                                key: 'processing',
                                label: 'PROCESSANDO',
                                icon: 'sync',
                                statuses: ['downloading', 'transcribing', 'editing', 'stitching'],
                                borderColor: 'border-cyan-500/30',
                                bgColor: 'bg-cyan-500/5',
                                textColor: 'text-cyan-400',
                                badgeBg: 'bg-cyan-500/10',
                                glowColor: 'shadow-[0_0_15px_rgba(0,240,255,0.05)]',
                                animate: true,
                            },
                            {
                                key: 'waiting',
                                label: 'AGUARDANDO CLIPS',
                                icon: 'hourglass_top',
                                statuses: ['waiting_clips'],
                                borderColor: 'border-amber-500/20',
                                bgColor: 'bg-amber-500/5',
                                textColor: 'text-amber-400',
                                badgeBg: 'bg-amber-500/10',
                                glowColor: '',
                                animate: false,
                            },
                            {
                                key: 'queue',
                                label: 'NA FILA',
                                icon: 'schedule',
                                statuses: ['pending'],
                                borderColor: 'border-slate-500/20',
                                bgColor: 'bg-slate-500/5',
                                textColor: 'text-slate-400',
                                badgeBg: 'bg-slate-500/10',
                                glowColor: '',
                                animate: false,
                            },
                            {
                                key: 'completed',
                                label: 'CONCLUÍDOS',
                                icon: 'check_circle',
                                statuses: ['completed'],
                                borderColor: 'border-emerald-500/20',
                                bgColor: 'bg-emerald-500/5',
                                textColor: 'text-emerald-400',
                                badgeBg: 'bg-emerald-500/10',
                                glowColor: '',
                                animate: false,
                            },
                            {
                                key: 'failed',
                                label: 'FALHAS',
                                icon: 'error',
                                statuses: ['failed'],
                                borderColor: 'border-red-500/20',
                                bgColor: 'bg-red-500/5',
                                textColor: 'text-red-400',
                                badgeBg: 'bg-red-500/10',
                                glowColor: '',
                                animate: false,
                            },
                        ];

                        // Mapa de step → ícone + rótulo amigável (hoisted para reusar)
                        const PIPELINE_STEPS = [
                            { key: 'waiting_clips', icon: 'hourglass_top', label: 'Aguardando mais clips', color: 'text-amber-400',   pct: 0  },
                            { key: 'pending',     icon: 'schedule',       label: 'Aguardando na fila',   color: 'text-slate-400',   pct: 0  },
                            { key: 'downloading', icon: 'download',       label: 'Baixando clipes',      color: 'text-blue-400',    pct: 10 },
                            { key: 'transcribing',icon: 'mic',            label: 'Transcrevendo (Whisper)', color: 'text-violet-400', pct: 30 },
                            { key: 'editing',     icon: 'movie_edit',     label: 'Editando com FFmpeg',  color: 'text-amber-400',   pct: 50 },
                            { key: 'stitching',   icon: 'join_inner',     label: 'Costurando clipes',    color: 'text-orange-400',  pct: 90 },
                            { key: 'completed',   icon: 'check_circle',   label: 'Concluído',            color: 'text-emerald-400', pct: 100 },
                            { key: 'failed',      icon: 'error',          label: 'Falha no pipeline',    color: 'text-red-400',     pct: 0  },
                        ];

                        return (
                        <div className="w-full max-w-5xl mx-auto flex flex-col gap-6 overflow-y-auto max-h-[80vh] pr-2 custom-scrollbar pb-10">
                            {/* Header Section */}
                            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                                <div className="flex items-center gap-3">
                                    <span className="material-symbols-outlined text-cyan-500/50 text-[20px]">movie_filter</span>
                                    <h3 className="text-xl font-display font-bold text-white tracking-widest">
                                        PIPELINE DE RENDERIZAÇÃO
                                    </h3>
                                </div>
                                <span className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] font-mono px-3 py-1 rounded">
                                    {items.filter(job => job.status !== 'completed' && job.status !== 'failed').length} JOB{items.filter(job => job.status !== 'completed' && job.status !== 'failed').length !== 1 ? 'S' : ''} ATIVO{items.filter(job => job.status !== 'completed' && job.status !== 'failed').length !== 1 ? 'S' : ''}
                                </span>
                            </div>

                            {/* ═══ Mini Status Summary ═══ */}
                            <div className="flex flex-wrap gap-2">
                                {PIPELINE_SECTIONS.map((section) => {
                                    const count = items.filter(job => section.statuses.includes(job.status)).length;
                                    if (count === 0) return null;
                                    return (
                                        <button
                                            key={section.key}
                                            onClick={() => toggleSection(section.key)}
                                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[10px] font-mono transition-all ${
                                                expandedSections.has(section.key)
                                                    ? `${section.borderColor} ${section.badgeBg} ${section.textColor}`
                                                    : 'border-white/5 bg-white/[0.02] text-slate-500 hover:text-slate-300'
                                            }`}
                                        >
                                            <span className={`material-symbols-outlined text-[12px] ${section.animate && expandedSections.has(section.key) ? 'animate-spin' : ''}`} style={section.animate ? { animationDuration: '3s' } : undefined}>{section.icon}</span>
                                            {count}
                                        </button>
                                    );
                                })}
                            </div>

                            {/* ═══ Seções Agrupadas por Status (Accordion) ═══ */}
                            <div className="space-y-3">
                                {PIPELINE_SECTIONS.map((section) => {
                                    const sectionJobs = items
                                        .filter(job => section.statuses.includes(job.status))
                                        .sort((a, b) => (b.priority || 0) - (a.priority || 0) || a.id - b.id);

                                    if (sectionJobs.length === 0) return null;

                                    const isExpanded = expandedSections.has(section.key);

                                    return (
                                        <div key={section.key} className={`rounded-xl border ${section.borderColor} ${section.bgColor} ${section.glowColor} overflow-hidden transition-all`}>
                                            {/* Section Header — Clickable */}
                                            <button
                                                onClick={() => toggleSection(section.key)}
                                                className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.02] transition-colors cursor-pointer"
                                            >
                                                <div className="flex items-center gap-2.5">
                                                    <span className={`material-symbols-outlined text-[16px] ${section.textColor} ${section.animate && isExpanded ? 'animate-spin' : ''}`} style={section.animate ? { animationDuration: '3s' } : undefined}>
                                                        {section.icon}
                                                    </span>
                                                    <span className={`font-display font-bold text-sm tracking-widest ${section.textColor}`}>
                                                        {section.label}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`${section.badgeBg} border ${section.borderColor} ${section.textColor} text-[10px] font-mono px-2.5 py-0.5 rounded-full`}>
                                                        {sectionJobs.length}
                                                    </span>
                                                    <span className={`material-symbols-outlined text-[14px] text-slate-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}>
                                                        expand_more
                                                    </span>
                                                </div>
                                            </button>

                                            {/* Section Jobs — Collapsible */}
                                            <div className={`transition-all duration-300 ease-in-out overflow-hidden ${isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}>
                                            <div className="p-3 space-y-3 border-t border-white/5">
                                                {sectionJobs.map((job) => {
                                                    const stepInfo = PIPELINE_STEPS.find(s => s.key === job.status) || PIPELINE_STEPS[0];
                                                    const activeStepIdx = PIPELINE_STEPS.findIndex(s => s.key === job.status);

                                                    return (
                                        <div key={job.id} className={`bg-cosmic-void border rounded-xl p-5 group hover:border-cosmic-glowBorder hover:bg-cosmic-hull transition-colors ${(job.priority || 0) >= 1 ? 'border-amber-500/40 shadow-[0_0_20px_rgba(245,158,11,0.1)]' : 'border-cosmic-border shadow-[0_4px_20px_rgba(0,0,0,0.3)]'}`}>
                                            {/* Top row: canal + job id + status badge */}
                                            <div className="flex items-center justify-between mb-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="flex items-center gap-2">
                                                        <span className={`material-symbols-outlined text-[18px] ${stepInfo.color}`}>{stepInfo.icon}</span>
                                                        <div>
                                                            {job.channel_name && (
                                                                <div className="text-white font-mono font-bold text-sm leading-tight">{job.channel_name}</div>
                                                            )}
                                                            <div className="text-slate-600 font-mono text-[10px]">
                                                                JOB #{job.id} · TARGET #{job.target_id}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>

                                                {job.status === 'completed' ? (
                                                    <span className="text-[10px] font-mono px-2.5 py-1 border border-emerald-500/30 text-emerald-400 rounded-full bg-emerald-500/10 flex items-center gap-1.5">
                                                        <span className="material-symbols-outlined text-[11px]">check_circle</span>CONCLUÍDO
                                                    </span>
                                                ) : job.status === 'failed' ? (
                                                    <span className="text-[10px] font-mono px-2.5 py-1 border border-red-500/30 text-red-400 rounded-full bg-red-500/10 flex items-center gap-1.5">
                                                        <span className="material-symbols-outlined text-[11px]">error</span>FALHA
                                                    </span>
                                                ) : (job.status as any) === 'waiting_clips' ? (
                                                    <span className="text-[10px] font-mono px-2.5 py-1 border border-amber-500/30 text-amber-400 rounded-full bg-amber-500/10 flex items-center gap-1.5">
                                                        <span className="material-symbols-outlined text-[11px] animate-spin" style={{animationDuration: '3s'}}>hourglass_top</span>AGUARDANDO CLIPS
                                                    </span>
                                                ) : job.status === 'pending' && (job.priority || 0) >= 1 ? (
                                                    <span className="text-[10px] font-mono px-2.5 py-1 border border-amber-500/40 text-amber-400 rounded-full bg-amber-500/15 flex items-center gap-1.5 shadow-[0_0_10px_rgba(245,158,11,0.15)]">
                                                        <span className="material-symbols-outlined text-[11px] animate-pulse">priority_high</span>PRIORIZADO
                                                    </span>
                                                ) : job.status === 'pending' ? (
                                                    <span className="text-[10px] font-mono px-2.5 py-1 border border-slate-500/30 text-slate-400 rounded-full bg-slate-500/10 flex items-center gap-1.5">
                                                        <span className="material-symbols-outlined text-[11px]">schedule</span>QUEUE
                                                    </span>
                                                ) : (
                                                    <span className="text-[10px] font-mono px-2.5 py-1 border border-cyan-500/30 text-cyan-400 rounded-full bg-cyan-500/10 flex items-center gap-1.5 shadow-[0_0_10px_rgba(0,240,255,0.1)]">
                                                        <span className="size-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                                                        PROCESSANDO
                                                    </span>
                                                )}
                                            </div>

                                            {/* Pipeline step timeline */}
                                            <div className="flex items-center gap-1 mb-4">
                                                {['pending','downloading','transcribing','editing','stitching','completed'].map((s, i) => {
                                                    const si = PIPELINE_STEPS.find(x => x.key === s)!;
                                                    const isDone = activeStepIdx > i;
                                                    const isCurrent = activeStepIdx === i && job.status !== ClipJobStatus.FAILED;
                                                    return (
                                                        <div
                                                            key={s}
                                                            title={si.label}
                                                            className={`flex flex-col items-center gap-0.5 flex-1 group/step cursor-default`}
                                                        >
                                                            <div className={`w-full h-1 rounded-full transition-all duration-500 ${
                                                                job.status === ClipJobStatus.FAILED ? 'bg-red-800/40'
                                                                : isDone ? 'bg-emerald-500/70'
                                                                : isCurrent ? 'bg-cyan-500 shadow-[0_0_6px_rgba(0,240,255,0.5)]'
                                                                : 'bg-white/5'
                                                            }`} />
                                                            <span className={`text-[8px] font-mono uppercase hidden md:block transition-colors ${
                                                                isDone ? 'text-emerald-600' : isCurrent ? 'text-cyan-400' : 'text-slate-700'
                                                            }`}>{si.label.split(' ')[0]}</span>
                                                        </div>
                                                    );
                                                })}
                                            </div>

                                            {/* Step label + progress bar */}
                                            <div className="flex justify-between items-center mb-1.5">
                                                <span className={`font-mono text-[11px] uppercase tracking-wider ${stepInfo.color}`}>
                                                    {job.current_step || stepInfo.label}
                                                </span>
                                                <span className="text-xs font-mono text-slate-500">{job.progress_pct}%</span>
                                            </div>
                                            <div className="w-full bg-cosmic-hull rounded-full h-1.5 border border-white/10">
                                                <div
                                                    className={`h-full rounded-full transition-all duration-1000 ${
                                                        job.status === ClipJobStatus.FAILED ? 'bg-red-500 shadow-[0_0_6px_#ef4444]'
                                                        : job.status === ClipJobStatus.COMPLETED ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]'
                                                        : 'bg-cyan-500 shadow-[0_0_6px_#06b6d4]'
                                                    }`}
                                                    style={{ width: `${job.progress_pct}%` }}
                                                />
                                            </div>

                                            {job.error_message && (
                                                <div className="mt-3 text-[10px] font-mono text-red-400 bg-red-500/5 border border-red-500/20 p-2.5 rounded break-all whitespace-pre-wrap">
                                                    <span className="flex items-center gap-1.5 mb-1 text-red-500 font-bold">
                                                        <span className="material-symbols-outlined text-[12px]">error</span>ERRO DO PIPELINE
                                                    </span>
                                                    {job.error_message}
                                                </div>
                                            )}

                                            {/* Timestamps + Actions */}
                                            <div className="mt-3 flex justify-between items-center border-t border-white/5 pt-3">
                                                <div className="flex gap-4 text-[9px] font-mono text-slate-700">
                                                    <span>Criado: <span className="text-slate-500">{new Date(job.created_at).toLocaleString('pt-BR')}</span></span>
                                                    {job.completed_at && (
                                                        <span>Concluído: <span className="text-emerald-700">{new Date(job.completed_at).toLocaleString('pt-BR')}</span></span>
                                                    )}
                                                </div>
                                                {job.status === 'pending' && (
                                                    <div className="flex gap-1.5">
                                                        {!(job.priority && job.priority >= 1) && (
                                                        <button
                                                            onClick={async (e) => {
                                                                e.stopPropagation();
                                                                try {
                                                                    await apiClient.post(`/api/clipper/jobs/${job.id}/prioritize`);
                                                                    toast.success(`Job #${job.id} priorizado!`);
                                                                    fetchPending();
                                                                } catch (err: any) {
                                                                    toast.error(err?.data?.detail || 'Erro ao priorizar');
                                                                }
                                                            }}
                                                            className="text-[9px] font-mono px-2 py-1 border border-amber-500/30 text-amber-400 rounded bg-amber-500/10 hover:bg-amber-500/20 flex items-center gap-1 transition-colors"
                                                            title="Priorizar este job"
                                                        >
                                                            <span className="material-symbols-outlined text-[11px]">priority_high</span>
                                                            PRIORIZAR
                                                        </button>
                                                        )}
                                                        <button
                                                            onClick={async (e) => {
                                                                e.stopPropagation();
                                                                try {
                                                                    await apiClient.post(`/api/clipper/jobs/${job.id}/cancel`);
                                                                    toast.info(`Job #${job.id} cancelado`);
                                                                    fetchPending();
                                                                } catch (err: any) {
                                                                    toast.error(err?.data?.detail || 'Erro ao cancelar');
                                                                }
                                                            }}
                                                            className="text-[9px] font-mono px-2 py-1 border border-red-500/30 text-red-400 rounded bg-red-500/10 hover:bg-red-500/20 flex items-center gap-1 transition-colors"
                                                            title="Cancelar este job"
                                                        >
                                                            <span className="material-symbols-outlined text-[11px]">close</span>
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                                    );
                                                })}
                                            </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                        );
                    })()}
                </div>
            )}

            {/* ═══ TAB: EXÉRCITOS ═══ */}
            {activeTab === 'armies' && (
                <div className="flex-1 flex flex-col gap-8 px-4 md:px-8 py-8 overflow-y-auto custom-scrollbar w-full max-w-7xl mx-auto z-10">

                    {/* Header / Intro */}
                    <div className="glass-card p-6 relative flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,240,255,0.1),transparent_70%)] pointer-events-none"></div>
                        <div className="relative z-10 flex-1">
                            <h2 className="text-2xl font-display font-bold text-white tracking-widest flex items-center gap-3 mb-2">
                                <span className="material-symbols-outlined text-cyan-400">swords</span>
                                QUARTEL GENERAL
                            </h2>
                            <p className="text-slate-400 font-mono text-sm max-w-2xl">
                                Agrupe seus alvos da Twitch em &quot;Exércitos&quot;. Mapeie e delegue as contas do TikTok/YouTube (Perfis) que receberão as edições processadas de um determinado Exército.
                            </p>
                        </div>
                    </div>

                    {/* Dashboard Grid */}
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

                        {/* Column 1: Create Army Form */}
                        <div className="glass-card p-6 flex flex-col gap-4 transition-all">
                            <h3 className="font-display font-bold text-white text-lg tracking-widest flex items-center gap-2 mb-2">
                                <span className="material-symbols-outlined text-cyan-400 text-xl">add_circle</span>
                                Criar Exército
                            </h3>
                            <div className="space-y-3">
                                <div>
                                    <label className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 block">Nome do Exército</label>
                                    <input
                                        type="text"
                                        value={newArmy.name}
                                        onChange={e => setNewArmy({ ...newArmy, name: e.target.value })}
                                        placeholder="Ex: Louders BR"
                                        className="w-full bg-black/60 border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500/50 transition-colors placeholder:text-slate-600"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 block">Cor</label>
                                        <input
                                            type="color"
                                            value={newArmy.color}
                                            onChange={e => setNewArmy({ ...newArmy, color: e.target.value })}
                                            className="w-full h-10 bg-black/60 border border-white/10 rounded-lg cursor-pointer"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1 block">Ícone</label>
                                        <select
                                            value={newArmy.icon}
                                            onChange={e => setNewArmy({ ...newArmy, icon: e.target.value })}
                                            className="w-full bg-black/60 border border-white/10 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-cyan-500/50 transition-colors"
                                        >
                                            <option value="swords">⚔️ Espadas</option>
                                            <option value="shield">🛡️ Escudo</option>
                                            <option value="rocket_launch">🚀 Foguete</option>
                                            <option value="flash_on">⚡ Raio</option>
                                            <option value="local_fire_department">🔥 Fogo</option>
                                            <option value="diamond">💎 Diamante</option>
                                            <option value="star">⭐ Estrela</option>
                                            <option value="pets">🐾 Patas</option>
                                        </select>
                                    </div>
                                </div>
                                <button
                                    onClick={handleCreateArmy}
                                    disabled={!newArmy.name.trim()}
                                    className="w-full mt-2 px-4 py-3 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-mono font-bold text-sm tracking-widest rounded-xl transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-[0_0_20px_-5px_rgba(0,240,255,0.3)]"
                                >
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
                                    <div key={army.id} className="glass-card overflow-hidden hover:border-white/10 transition-colors shadow-lg">
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
                                                onClick={() => requestDeleteArmy(army.id)}
                                                className="w-10 h-10 rounded-full bg-red-500/10 text-red-500 border border-transparent hover:border-red-500/30 flex items-center justify-center transition-all"
                                            >
                                                <span className="material-symbols-outlined text-xl">delete</span>
                                            </button>
                                        </div>

                                        {/* Profiles Section */}
                                        <div className="p-5">
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="text-sm font-mono text-slate-400 uppercase tracking-wider">Perfis Vinculados</h4>
                                            </div>
                                            {army.profiles.length === 0 ? (
                                                <p className="text-slate-600 text-xs font-mono italic">Nenhum perfil vinculado a este exército ainda.</p>
                                            ) : (
                                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                                    {army.profiles.map((profile) => (
                                                        <div key={profile.id} className="bg-black/40 border border-cyan-500/10 rounded-xl p-3 flex items-center gap-3 group hover:border-cyan-500/30 transition-colors">
                                                            {profile.avatar_url ? (
                                                                <img src={profile.avatar_url} alt={profile.username} className="w-8 h-8 rounded-full object-cover" />
                                                            ) : (
                                                                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center">
                                                                    <span className="material-symbols-outlined text-slate-500 text-sm">person</span>
                                                                </div>
                                                            )}
                                                            <div className="min-w-0 flex-1">
                                                                <div className="text-white text-sm font-bold truncate">{profile.username || profile.slug}</div>
                                                                <div className="text-slate-500 text-[10px] font-mono truncate">@{profile.slug}</div>
                                                            </div>
                                                            <button
                                                                onClick={() => handleToggleProfileInArmy(army.id, Number(profile.id), true)}
                                                                className="w-7 h-7 rounded-full bg-red-500/0 text-red-400/0 group-hover:bg-red-500/10 group-hover:text-red-400 flex items-center justify-center transition-all hover:!bg-red-500/20"
                                                                title="Desvincular perfil"
                                                            >
                                                                <span className="material-symbols-outlined text-sm">close</span>
                                                            </button>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Add Profile Toggle */}
                                            {profiles.filter(p => !army.profiles.some((ap: any) => ap.id === (p.db_id ?? p.id))).length > 0 && (
                                                <div className="mt-4 pt-4 border-t border-white/5">
                                                    <h5 className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2">Designar Perfis</h5>
                                                    <div className="flex flex-wrap gap-2">
                                                        {profiles
                                                            .filter(p => !army.profiles.some((ap: any) => ap.id === (p.db_id ?? p.id)))
                                                            .map((profile) => (
                                                                <button
                                                                    key={profile.id}
                                                                    onClick={() => handleToggleProfileInArmy(army.id, profile.db_id ?? Number(profile.id), false)}
                                                                    className="flex items-center gap-2 bg-black/40 border border-white/5 rounded-lg px-3 py-2 hover:border-cyan-500/30 hover:bg-cyan-500/5 transition-all group"
                                                                >
                                                                    {profile.avatar_url ? (
                                                                        <img src={profile.avatar_url} alt={profile.username} className="w-5 h-5 rounded-full object-cover" />
                                                                    ) : (
                                                                        <div className="w-5 h-5 rounded-full bg-slate-800 flex items-center justify-center">
                                                                            <span className="material-symbols-outlined text-slate-500 text-[10px]">person</span>
                                                                        </div>
                                                                    )}
                                                                    <span className="text-slate-400 text-xs font-mono group-hover:text-cyan-400 transition-colors">{profile.username || profile.slug}</span>
                                                                    <span className="material-symbols-outlined text-cyan-500/0 group-hover:text-cyan-400 text-sm transition-colors">add</span>
                                                                </button>
                                                            ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ═══ TAB: APROVAÇÃO (CURATION) ═══ */}
            {activeTab === 'approval' && (
                <div className="flex-1 w-full max-w-7xl mx-auto px-6 py-6 z-10 space-y-6 animate-in fade-in zoom-in-95 duration-500 overflow-y-auto custom-scrollbar pb-32">
                    <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                                <span className="material-symbols-outlined text-2xl">done_all</span>
                            </div>
                            <div>
                                <h2 className="text-xl font-display font-bold text-white tracking-widest uppercase">Fila de Aprovação</h2>
                                <p className="text-[10px] font-mono text-emerald-500/70 border border-emerald-500/20 bg-emerald-500/5 px-2 py-0.5 rounded mt-1 inline-block">VÍDEOS FINALIZADOS PELO CLIPPER</p>
                            </div>
                        </div>
                        {pendingVideos.length > 0 && (
                            <button
                                onClick={() => fetchPendingVideos(true)}
                                disabled={refreshingList}
                                className="text-xs font-mono text-cyan-400 hover:text-white border border-cyan-400/30 hover:border-cyan-400 bg-cyan-400/5 px-4 py-2 rounded-lg flex items-center gap-2 transition-all hover:bg-cyan-400/20 disabled:opacity-50"
                            >
                                <span className={`material-symbols-outlined text-[16px] ${refreshingList ? 'animate-spin' : ''}`}>sync</span>
                                {refreshingList ? 'ATUALIZANDO...' : 'ATT LISTA'}
                            </button>
                        )}
                    </div>

                    {/* Loading State */}
                    {approvalLoading ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="glass-card overflow-hidden animate-pulse">
                                    <div className="w-full aspect-video bg-white/5"></div>
                                    <div className="p-5 space-y-3">
                                        <div className="h-4 bg-white/5 rounded w-3/4"></div>
                                        <div className="h-3 bg-white/5 rounded w-1/2"></div>
                                        <div className="h-16 bg-white/5 rounded"></div>
                                        <div className="flex gap-2 pt-2">
                                            <div className="h-10 bg-emerald-500/5 rounded-lg flex-1"></div>
                                            <div className="h-10 bg-red-500/5 rounded-lg w-14"></div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : pendingVideos.length === 0 ? (
                        <div className="bg-black/40 border border-emerald-500/10 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
                            <span className="material-symbols-outlined text-5xl text-emerald-500/20 mb-4 animate-pulse">check_circle</span>
                            <h3 className="text-emerald-400 font-mono text-sm uppercase tracking-[0.2em] mb-2">Fila Vazia</h3>
                            <p className="text-slate-500 text-xs">O Clipper ainda está processando os próximos recortes na esteira.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {pendingVideos.map((video) => (
                                <div key={video.id} className="glass-card overflow-hidden group hover:border-emerald-500/30 transition-colors flex flex-col">
                                    {/* Video Preview */}
                                    <div className="relative w-full aspect-[9/16] max-h-[400px] bg-black border-b border-white/5 overflow-hidden flex items-center justify-center">
                                        <span className="material-symbols-outlined text-white/5 text-6xl">play_circle</span>
                                        <video
                                            src={`${API}/exports/${video.video_path.split('/').pop()}`}
                                            className="absolute inset-0 w-full h-full object-contain bg-black opacity-90 group-hover:opacity-100 transition-opacity z-20 cursor-pointer"
                                            controls
                                            preload="metadata"
                                        />
                                    </div>

                                    <div className="p-4 flex-1 flex flex-col gap-3">
                                        {/* Title + Status Badge */}
                                        <div className="flex justify-between items-start gap-2">
                                            <h3 className="text-white font-bold text-xs truncate uppercase tracking-wider flex-1" title={video.title || `Job #${video.clip_job_id}`}>
                                                {video.title || `Clip Job #${video.clip_job_id}`}
                                            </h3>
                                            <span className="text-[9px] font-mono text-amber-500 border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 rounded whitespace-nowrap">PENDENTE</span>
                                        </div>

                                        {/* Streamer */}
                                        <p className="text-[11px] text-slate-500 font-mono flex items-center gap-1.5">
                                            <span className="material-symbols-outlined text-[14px]">person</span>
                                            {video.streamer_name || 'Desconhecido'}
                                        </p>

                                        {/* Duration + Size */}
                                        <div className="flex items-center gap-3 text-[10px] text-slate-600 font-mono">
                                            {video.duration_seconds && (
                                                <span className="flex items-center gap-1">
                                                    <span className="material-symbols-outlined text-[12px]">timer</span>
                                                    {Math.floor(video.duration_seconds / 60)}:{String(video.duration_seconds % 60).padStart(2, '0')}
                                                </span>
                                            )}
                                            {video.file_size_bytes && (
                                                <span className="flex items-center gap-1">
                                                    <span className="material-symbols-outlined text-[12px]">hard_drive</span>
                                                    {(video.file_size_bytes / 1024 / 1024).toFixed(1)} MB
                                                </span>
                                            )}
                                        </div>

                                        {/* ═══ Caption Accordion ═══ */}
                                        <div className="border-t border-white/5 pt-2">
                                            <button
                                                onClick={() => toggleCaptionAccordion(video.id)}
                                                className="w-full flex items-center justify-between py-2 px-1 text-[10px] font-mono uppercase tracking-wider text-slate-400 hover:text-white transition-colors group/acc"
                                            >
                                                <div className="flex items-center gap-1.5">
                                                    <span className="material-symbols-outlined text-[14px]">description</span>
                                                    DESCRIÇÃO
                                                    {(video.caption || captionDrafts[video.id]?.caption) && (
                                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" title="Descrição definida"></span>
                                                    )}
                                                    {video.caption_generated && (
                                                        <span className="text-[8px] text-violet-400 border border-violet-500/30 bg-violet-500/10 px-1 rounded">IA</span>
                                                    )}
                                                </div>
                                                <span className={`material-symbols-outlined text-[14px] transition-transform duration-200 ${expandedCaptionId === video.id ? 'rotate-180' : ''}`}>
                                                    expand_more
                                                </span>
                                            </button>

                                            {expandedCaptionId === video.id && (
                                                <div className="space-y-3 pb-3 animate-in slide-in-from-top-2 duration-200">
                                                    {/* Tone Selector */}
                                                    <div className="flex gap-1.5 flex-wrap">
                                                        {['Viral', 'Polêmico', 'Engraçado', 'Profissional'].map(tone => (
                                                            <button
                                                                key={tone}
                                                                onClick={() => setCaptionTone(tone)}
                                                                className={`text-[9px] font-mono px-2 py-1 rounded-full border transition-colors ${
                                                                    captionTone === tone
                                                                        ? 'border-violet-500/50 bg-violet-500/20 text-violet-300'
                                                                        : 'border-white/10 text-slate-500 hover:border-white/20 hover:text-slate-300'
                                                                }`}
                                                            >
                                                                {tone === 'Viral' && '🔥'} {tone === 'Polêmico' && '💥'} {tone === 'Engraçado' && '😂'} {tone === 'Profissional' && '💼'} {tone}
                                                            </button>
                                                        ))}
                                                    </div>

                                                    {/* Generate Button */}
                                                    <button
                                                        onClick={() => handleGenerateCaption(video.id)}
                                                        disabled={generatingCaption === video.id}
                                                        className="w-full flex items-center justify-center gap-2 py-2 text-[10px] font-mono font-bold uppercase tracking-wider border border-violet-500/30 text-violet-400 rounded-lg bg-violet-500/5 hover:bg-violet-500/15 transition-colors disabled:opacity-50"
                                                    >
                                                        {generatingCaption === video.id ? (
                                                            <>
                                                                <span className="material-symbols-outlined text-[14px] animate-spin">progress_activity</span>
                                                                ORACLE GERANDO...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
                                                                GERAR COM IA
                                                            </>
                                                        )}
                                                    </button>

                                                    {/* Caption Textarea */}
                                                    <textarea
                                                        value={captionDrafts[video.id]?.caption || ''}
                                                        onChange={(e) => setCaptionDrafts(prev => ({
                                                            ...prev,
                                                            [video.id]: { ...prev[video.id], caption: e.target.value, hashtags: prev[video.id]?.hashtags || [] }
                                                        }))}
                                                        placeholder="Escreva a descrição do TikTok..."
                                                        className="w-full bg-black/40 border border-white/10 rounded-lg text-white text-xs font-mono p-3 resize-none focus:border-violet-500/50 focus:outline-none placeholder:text-slate-600 min-h-[80px]"
                                                        rows={3}
                                                    />

                                                    {/* Hashtags */}
                                                    {(captionDrafts[video.id]?.hashtags?.length ?? 0) > 0 && (
                                                        <div className="flex flex-wrap gap-1.5">
                                                            {captionDrafts[video.id]?.hashtags.map((tag, i) => (
                                                                <span key={i} className="text-[9px] font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                                                                    {tag.startsWith('#') ? tag : `#${tag}`}
                                                                    <button
                                                                        onClick={() => {
                                                                            setCaptionDrafts(prev => ({
                                                                                ...prev,
                                                                                [video.id]: {
                                                                                    ...prev[video.id],
                                                                                    hashtags: prev[video.id].hashtags.filter((_, idx) => idx !== i)
                                                                                }
                                                                            }));
                                                                        }}
                                                                        className="text-cyan-500/50 hover:text-red-400 transition-colors"
                                                                    >
                                                                        <span className="material-symbols-outlined text-[10px]">close</span>
                                                                    </button>
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}

                                                    {/* Transcript Preview (collapsed) */}
                                                    {video.transcript && (
                                                        <details className="text-[9px] font-mono text-slate-600">
                                                            <summary className="cursor-pointer hover:text-slate-400 transition-colors flex items-center gap-1">
                                                                <span className="material-symbols-outlined text-[12px]">mic</span>
                                                                TRANSCRIÇÃO WHISPER ({video.transcript.length} chars)
                                                            </summary>
                                                            <p className="mt-1.5 p-2 bg-black/30 rounded border border-white/5 text-slate-500 leading-relaxed max-h-[100px] overflow-y-auto custom-scrollbar">
                                                                {video.transcript}
                                                            </p>
                                                        </details>
                                                    )}

                                                    {/* Save Button */}
                                                    {captionDrafts[video.id]?.caption && (
                                                        <button
                                                            onClick={() => handleSaveCaption(video.id)}
                                                            disabled={savingCaption === video.id}
                                                            className="w-full flex items-center justify-center gap-1.5 py-1.5 text-[9px] font-mono uppercase tracking-wider border border-emerald-500/20 text-emerald-400 rounded bg-emerald-500/5 hover:bg-emerald-500/15 transition-colors disabled:opacity-50"
                                                        >
                                                            <span className="material-symbols-outlined text-[12px]">save</span>
                                                            {savingCaption === video.id ? 'SALVANDO...' : 'SALVAR DESCRIÇÃO'}
                                                        </button>
                                                    )}
                                                </div>
                                            )}
                                        </div>

                                        {/* Reorder Clipes UI */}
                                        {video.clips && video.clips.length > 1 && (
                                            <ClipReorderList 
                                                initialClips={video.clips} 
                                                onReorder={async (newOrder) => await handleReorderClips(video.id, newOrder)}
                                            />
                                        )}

                                        {/* Action Buttons */}
                                        <div className="flex gap-2 mt-auto pt-2 border-t border-white/5">
                                            <button
                                                onClick={() => handleApprove(video)}
                                                className="flex-1 bg-gradient-to-r from-emerald-500/20 to-emerald-600/20 hover:from-emerald-500 hover:to-emerald-400 hover:text-black border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold py-2.5 rounded-lg flex justify-center items-center gap-2 transition-all shadow-[0_0_15px_rgba(16,185,129,0.1)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)]"
                                                aria-label={`Aprovar vídeo ${video.title}`}
                                            >
                                                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                                                APROVAR
                                            </button>
                                            <button
                                                onClick={() => handleReject(video.id)}
                                                className="bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 text-xs py-2.5 px-4 rounded-lg flex justify-center items-center transition-colors"
                                                title="Rejeitar clipe (Deletar)"
                                                aria-label={`Rejeitar vídeo ${video.title}`}
                                            >
                                                <span className="material-symbols-outlined text-[18px]">delete</span>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Modal de Confirmação de Exclusão do Alvo */}
            {
                targetToDelete !== null && (
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
                )
            }
            {/* Delete Army Confirmation Modal */}
            {
                armyToDelete !== null && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                        <div className="bg-slate-900 border border-red-500/30 p-6 max-w-md w-full shadow-2xl relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-red-900"></div>
                            <div className="flex items-start gap-4 mb-6">
                                <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
                                    <span className="material-symbols-outlined text-red-400 text-xl">warning</span>
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white font-display mb-1">Dissolver Exército</h3>
                                    <p className="text-slate-400 text-sm">
                                        Atenção: Ao dissolver este exército, os alvos vinculados a ele se tornarão Órfãos. Deseja prosseguir?
                                    </p>
                                </div>
                            </div>
                            <div className="flex justify-end gap-3 font-mono text-xs uppercase tracking-wider">
                                <button
                                    onClick={cancelDeleteArmy}
                                    className="px-4 py-2 border border-white/10 text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={confirmDeleteArmy}
                                    className="px-4 py-2 bg-red-500/20 border border-red-500/50 text-red-400 hover:bg-red-500 hover:text-white transition-colors"
                                >
                                    Dissolver
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Modal Aprovação de Vídeo */}
            {showApprovalModal && selectedVideo && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-emerald-500/30 p-6 max-w-md w-full shadow-2xl relative overflow-hidden rounded-xl">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-emerald-900"></div>
                        <div className="mb-6">
                            <h3 className="text-xl font-bold text-white font-display mb-1 flex items-center gap-2">
                                <span className="material-symbols-outlined text-emerald-400">rocket_launch</span>
                                Aprovar e Agendar
                            </h3>
                            <p className="text-slate-400 text-sm font-mono truncate">
                                {selectedVideo.title || selectedVideo.video_path.split('/').pop()}
                            </p>
                            {selectedVideo.streamer_name && (
                                <p className="text-slate-500 text-xs font-mono mt-1">
                                    Streamer: {selectedVideo.streamer_name}
                                    {selectedVideo.duration_seconds && ` | ${Math.floor(selectedVideo.duration_seconds / 60)}:${String(selectedVideo.duration_seconds % 60).padStart(2, '0')}`}
                                </p>
                            )}
                        </div>

                        <div className="space-y-4 mb-6 max-h-[60vh] overflow-y-auto pr-1">
                            {/* Perfil Destino */}
                            <div>
                                <label className="text-[10px] uppercase font-mono text-slate-500 tracking-wider mb-2 block">
                                    Perfil Destino
                                </label>
                                {selectedVideo.available_profiles && selectedVideo.available_profiles.length > 0 ? (
                                    <div className="grid gap-2">
                                        <button
                                            onClick={() => setSelectedProfileSlug('')}
                                            className={`flex items-center gap-3 p-3 rounded-lg border text-left transition-all ${
                                                selectedProfileSlug === ''
                                                    ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400'
                                                    : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                                            }`}
                                        >
                                            <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
                                            <div>
                                                <div className="text-xs font-mono font-bold">AUTO</div>
                                                <div className="text-[10px] text-slate-500">Resolve via Army do alvo</div>
                                            </div>
                                        </button>
                                        {selectedVideo.available_profiles.map((p) => (
                                            <button
                                                key={p.slug}
                                                onClick={() => setSelectedProfileSlug(p.slug)}
                                                className={`flex items-center gap-3 p-3 rounded-lg border text-left transition-all ${
                                                    selectedProfileSlug === p.slug
                                                        ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-400'
                                                        : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                                                }`}
                                            >
                                                {p.avatar_url ? (
                                                    <img src={p.avatar_url} alt={p.username} className="w-6 h-6 rounded-full" />
                                                ) : (
                                                    <span className="material-symbols-outlined text-[20px]">account_circle</span>
                                                )}
                                                <div>
                                                    <div className="text-xs font-mono font-bold">@{p.username}</div>
                                                    {p.label && <div className="text-[10px] text-slate-500">{p.label}</div>}
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-xs text-slate-500 font-mono">Nenhum perfil ativo. Sera usado o perfil padrao.</p>
                                )}
                            </div>

                            {/* Modo de Agendamento */}
                            <div>
                                <label className="text-[10px] uppercase font-mono text-slate-500 tracking-wider mb-2 block">
                                    Agendamento
                                </label>
                                <div className="grid grid-cols-3 gap-2">
                                    {([
                                        { mode: 'smart' as const, icon: 'auto_awesome', label: 'Smart Queue', desc: 'Automático' },
                                        { mode: 'specific' as const, icon: 'calendar_month', label: 'Data Exata', desc: 'Escolher dia/hora' },
                                        { mode: 'now' as const, icon: 'bolt', label: 'Agora', desc: 'Próx. 1 min' },
                                    ]).map((opt) => (
                                        <button
                                            key={opt.mode}
                                            onClick={() => setPostType(opt.mode as any)}
                                            className={`flex flex-col items-center gap-1 p-3 rounded-lg border text-center transition-all ${
                                                postType === opt.mode
                                                    ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400'
                                                    : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                                            }`}
                                        >
                                            <span className="material-symbols-outlined text-[20px]">{opt.icon}</span>
                                            <div className="text-[10px] font-mono font-bold">{opt.label}</div>
                                            <div className="text-[9px] text-slate-500">{opt.desc}</div>
                                        </button>
                                    ))}
                                </div>

                                {/* Smart Queue info */}
                                {postType === 'smart' && (
                                    <div className="mt-3 bg-emerald-500/5 rounded-lg p-3 border border-emerald-500/10">
                                        <p className="text-[10px] text-emerald-400/70 font-mono">
                                            A Smart Queue distribuira automaticamente nos horarios configurados (12h e 18h), evitando conflitos com posts existentes.
                                        </p>
                                    </div>
                                )}

                                {/* Date/Time picker for specific mode */}
                                {postType === 'specific' && (
                                    <div className="mt-3 space-y-3">
                                        <div>
                                            <label className="text-[10px] uppercase font-mono text-slate-500 tracking-wider mb-1 block">Data</label>
                                            <input
                                                type="date"
                                                value={selectedDate}
                                                onChange={(e) => setSelectedDate(e.target.value)}
                                                min={new Date().toISOString().split('T')[0]}
                                                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono focus:border-emerald-500/50 focus:outline-none [color-scheme:dark]"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] uppercase font-mono text-slate-500 tracking-wider mb-1 block">Horario</label>
                                            <div className="grid grid-cols-4 gap-1.5">
                                                {[
                                                    { t: '09:00', label: '9h' },
                                                    { t: '12:00', label: '12h' },
                                                    { t: '15:00', label: '15h' },
                                                    { t: '18:00', label: '18h' },
                                                    { t: '20:00', label: '20h' },
                                                    { t: '21:00', label: '21h' },
                                                    { t: '22:00', label: '22h' },
                                                    { t: '23:00', label: '23h' },
                                                ].map((h) => (
                                                    <button
                                                        key={h.t}
                                                        onClick={() => setSelectedTime(h.t)}
                                                        className={`py-1.5 rounded text-xs font-mono transition-all ${
                                                            selectedTime === h.t
                                                                ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400'
                                                                : 'bg-white/5 border border-white/10 text-slate-400 hover:border-white/20'
                                                        }`}
                                                    >
                                                        {h.label}
                                                    </button>
                                                ))}
                                            </div>
                                            <div className="mt-2">
                                                <input
                                                    type="time"
                                                    value={selectedTime}
                                                    onChange={(e) => setSelectedTime(e.target.value)}
                                                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono focus:border-emerald-500/50 focus:outline-none [color-scheme:dark]"
                                                />
                                            </div>
                                            {selectedDate && selectedTime && (
                                                <p className="mt-2 text-[10px] text-emerald-400/70 font-mono">
                                                    Agendado para: {new Date(`${selectedDate}T${selectedTime}`).toLocaleString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long', hour: '2-digit', minute: '2-digit' })}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Now mode info */}
                                {postType === 'now' && (
                                    <div className="mt-3 bg-amber-500/5 rounded-lg p-3 border border-amber-500/10">
                                        <p className="text-[10px] text-amber-400/70 font-mono">
                                            O video sera agendado para daqui a 1 minuto. Ideal para testes rapidos.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 mt-8">
                            <button
                                onClick={() => { setShowApprovalModal(false); setSelectedVideo(null); }}
                                className="px-4 py-2 text-sm font-mono text-slate-400 hover:text-white transition-colors"
                            >
                                CANCELAR
                            </button>
                            <button
                                onClick={handleConfirmVideo}
                                disabled={submittingApproval}
                                className="px-6 py-2 bg-emerald-500/20 hover:bg-emerald-500/40 text-emerald-400 border border-emerald-500/50 hover:border-emerald-400 rounded text-sm font-bold font-mono transition-all disabled:opacity-50 flex items-center gap-2"
                            >
                                {submittingApproval ? (
                                    <span className="material-symbols-outlined animate-spin text-[18px]">autorenew</span>
                                ) : (
                                    <span className="material-symbols-outlined text-[18px]">send</span>
                                )}
                                APROVAR
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Modal Confirmação de Rejeição */}
            {confirmReject && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-red-500/30 p-6 max-w-sm w-full shadow-2xl relative overflow-hidden rounded-xl">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-red-900"></div>
                        <div className="flex items-start gap-4 mb-6">
                            <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center flex-shrink-0">
                                <span className="material-symbols-outlined text-red-500 text-xl">delete_forever</span>
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white font-display mb-1">Apagar Clipe?</h3>
                                <p className="text-slate-400 text-sm">
                                    O vídeo será excluído permanentemente do servidor e removido da esteira.
                                </p>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setConfirmReject(null)}
                                className="px-4 py-2 text-sm font-mono text-slate-400 hover:text-white transition-colors"
                            >
                                CANCELAR
                            </button>
                            <button
                                onClick={confirmRejectVideo}
                                className="px-6 py-2 bg-red-500/20 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/50 hover:border-red-500 rounded text-sm font-bold font-mono transition-all"
                            >
                                APAGAR
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
