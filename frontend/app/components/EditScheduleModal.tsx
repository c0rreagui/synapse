'use client';

import { Fragment, useState, useEffect, useRef } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { ScheduleEvent, TikTokProfile } from '../types';
import { getApiUrl } from '../utils/apiClient';
import {
    XMarkIcon,
    ClockIcon,
    UserCircleIcon,
    ChatBubbleBottomCenterTextIcon,
    ShieldCheckIcon,
    MusicalNoteIcon,
    FilmIcon,
    CheckIcon,
    ExclamationTriangleIcon,
    ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import clsx from 'clsx';
import { toast } from 'sonner';

interface EditScheduleModalProps {
    isOpen: boolean;
    onClose: () => void;
    event: ScheduleEvent | null;
    profiles: TikTokProfile[];
    onSave: (eventId: string, data: EditScheduleData) => Promise<void>;
}

export interface EditScheduleData {
    scheduled_time?: string;
    profile_id?: string;
    caption?: string;
    privacy_level?: string;
    viral_music_enabled?: boolean;
    music_volume?: number;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
    pending: { label: 'Pendente', color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-400/30' },
    posted: { label: 'Publicado', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' },
    completed: { label: 'Concluido', color: 'text-emerald-400', bg: 'bg-emerald-400/10 border-emerald-400/30' },
    failed: { label: 'Falhou', color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30' },
    processing: { label: 'Processando', color: 'text-blue-400', bg: 'bg-blue-400/10 border-blue-400/30' },
    ready: { label: 'Pronto', color: 'text-cyan-400', bg: 'bg-cyan-400/10 border-cyan-400/30' },
    paused_login_required: { label: 'Login Necessario', color: 'text-orange-400', bg: 'bg-orange-400/10 border-orange-400/30' },
};

export default function EditScheduleModal({
    isOpen,
    onClose,
    event,
    profiles,
    onSave
}: EditScheduleModalProps) {
    const API_URL = getApiUrl();
    const videoRef = useRef<HTMLVideoElement>(null);

    // Form State
    const [editTime, setEditTime] = useState('');
    const [editDate, setEditDate] = useState('');
    const [selectedProfile, setSelectedProfile] = useState('');
    const [caption, setCaption] = useState('');
    const [privacyLevel, setPrivacyLevel] = useState('public');
    const [viralMusic, setViralMusic] = useState(false);
    const [musicVolume, setMusicVolume] = useState(0.0);
    const [saving, setSaving] = useState(false);
    const [videoError, setVideoError] = useState(false);
    const [videoLoading, setVideoLoading] = useState(true);
    const [hasChanges, setHasChanges] = useState(false);
    const [videoPath, setVideoPath] = useState('');

    // Original values for diff tracking
    const [origValues, setOrigValues] = useState<Record<string, any>>({});

    // Populate form when event changes (Initial from props)
    useEffect(() => {
        if (event) {
            const dt = new Date(event.scheduled_time);
            const time = format(dt, 'HH:mm');
            const date = format(dt, 'yyyy-MM-dd');
            const profile = event.profile_id;
            const cap = event.caption || event.metadata?.caption || '';
            const priv = event.privacy_level || event.metadata?.privacy_level || 'public';
            const viral = event.viral_music_enabled || false;
            const vol = event.music_volume || 0.0;

            setEditTime(time);
            setEditDate(date);
            setSelectedProfile(profile);
            setCaption(cap);
            setPrivacyLevel(priv);
            setViralMusic(viral);
            setMusicVolume(vol);
            setVideoPath(event.video_path || '');
            setVideoError(false);
            setVideoLoading(true);
            setHasChanges(false);

            setOrigValues({ time, date, profile, caption: cap, privacyLevel: priv, viralMusic: viral, musicVolume: vol });
        }
    }, [event]);

    // [SYN-FIX] Fetch fresh data on open to handle stale props
    useEffect(() => {
        if (isOpen && event?.id) {
            const fetchFresh = async () => {
                try {
                    const res = await fetch(`${API_URL}/api/v1/scheduler/items/${event.id}`);
                    if (res.ok) {
                        const fresh = await res.json();
                        // Update state with fresh DB data
                        const dt = new Date(fresh.scheduled_time);
                        const time = format(dt, 'HH:mm');
                        const date = format(dt, 'yyyy-MM-dd');
                        
                        setEditTime(time);
                        setEditDate(date);
                        setSelectedProfile(fresh.profile_id);
                        setCaption(fresh.caption || fresh.metadata?.caption || '');
                        setPrivacyLevel(fresh.privacy_level || fresh.metadata?.privacy_level || 'public');
                        setViralMusic(fresh.viral_music_enabled || false);
                        setMusicVolume(fresh.music_volume || 0.0);
                        setVideoPath(fresh.video_path || '');
                        
                        // Update origins so "Changed" detection logic is accurate against DB state
                        setOrigValues({ 
                            time, 
                            date, 
                            profile: fresh.profile_id, 
                            caption: fresh.caption || fresh.metadata?.caption || '', 
                            privacyLevel: fresh.privacy_level || fresh.metadata?.privacy_level || 'public', 
                            viralMusic: fresh.viral_music_enabled || false, 
                            musicVolume: fresh.music_volume || 0.0 
                        });

                        // Force reload video player if it was errored
                        if (videoRef.current) {
                            videoRef.current.load();
                        }
                    }
                } catch (e) {
                    console.error("Failed to fetch fresh schedule item:", e);
                }
            };
            fetchFresh();
        }
    }, [isOpen, event?.id, API_URL]);

    // Track changes
    useEffect(() => {
        const changed =
            editTime !== origValues.time ||
            editDate !== origValues.date ||
            selectedProfile !== origValues.profile ||
            caption !== origValues.caption ||
            privacyLevel !== origValues.privacyLevel ||
            viralMusic !== origValues.viralMusic ||
            musicVolume !== origValues.musicVolume;
        setHasChanges(changed);
    }, [editTime, editDate, selectedProfile, caption, privacyLevel, viralMusic, musicVolume, origValues]);

    const handleSave = async () => {
        if (!event) return;
        setSaving(true);

        try {
            // Build new datetime from date + time
            const [hours, minutes] = editTime.split(':').map(Number);
            const newDate = new Date(editDate + 'T00:00:00');
            newDate.setHours(hours, minutes, 0, 0);

            const data: EditScheduleData = {
                scheduled_time: newDate.toISOString(),
                profile_id: selectedProfile,
                caption: caption,
                privacy_level: privacyLevel,
                viral_music_enabled: viralMusic,
                music_volume: musicVolume,
            };

            await onSave(event.id, data);
            toast.success('Agendamento atualizado!');
            onClose();
        } catch (err: any) {
            console.error('Save failed:', err);
            toast.error('Erro ao salvar: ' + (err.message || 'Erro desconhecido'));
        } finally {
            setSaving(false);
        }
    };

    const getProfileLabel = (id: string) => {
        const p = profiles.find(pr => pr.id === id);
        return p ? p.label : id;
    };

    const getProfileColor = (id: string) => {
        const p = profiles.find(pr => pr.id === id);
        if (!p) return '#8b5cf6';
        // Generate deterministic color from label
        let hash = 0;
        const name = p.label || p.id;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        const hue = Math.abs(hash) % 360;
        return `hsl(${hue}, 70%, 60%)`;
    };

    const videoPreviewUrl = event ? `${API_URL}/api/v1/scheduler/video-preview/${event.id}` : '';

    // Extract filename from path for display
    const videoFilename = videoPath ? videoPath.split(/[/\\]/).pop() : 'Video';

    const statusInfo = event ? (STATUS_CONFIG[event.status] || STATUS_CONFIG.pending) : STATUS_CONFIG.pending;

    if (!event) return null;

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-[60]" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/90 backdrop-blur-md" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-[#0f0a15] border border-white/10 shadow-[0_0_60px_rgba(139,92,246,0.15)] transition-all">

                                {/* Header */}
                                <div className="relative p-6 border-b border-white/5 bg-gradient-to-r from-synapse-purple/10 to-transparent">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                                <FilmIcon className="w-6 h-6 text-synapse-purple" />
                                                Editor de Agendamento
                                            </h3>
                                            <div className="flex items-center gap-3 mt-2">
                                                <p className="text-xs text-gray-500 font-mono">
                                                    ID: {event.id}
                                                </p>
                                                {/* Profile pill */}
                                                <div
                                                    className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-medium"
                                                    style={{
                                                        borderColor: getProfileColor(event.profile_id) + '40',
                                                        backgroundColor: getProfileColor(event.profile_id) + '15',
                                                        color: getProfileColor(event.profile_id),
                                                    }}
                                                >
                                                    <div
                                                        className="w-1.5 h-1.5 rounded-full"
                                                        style={{ backgroundColor: getProfileColor(event.profile_id) }}
                                                    />
                                                    {getProfileLabel(event.profile_id)}
                                                </div>
                                                {/* Status badge */}
                                                <span className={clsx(
                                                    'px-2.5 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider',
                                                    statusInfo.bg, statusInfo.color
                                                )}>
                                                    {statusInfo.label}
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={onClose}
                                            className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
                                        >
                                            <XMarkIcon className="w-6 h-6" />
                                        </button>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto custom-scrollbar">

                                    {/* Video Preview */}
                                    <div className="space-y-2">
                                        <label className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                            <FilmIcon className="w-4 h-4 text-synapse-purple" />
                                            Preview do Video
                                        </label>
                                        <div className="relative rounded-xl overflow-hidden border border-white/10 bg-black/60">
                                            {!videoError ? (
                                                <>
                                                    {videoLoading && (
                                                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 z-10">
                                                            <ArrowPathIcon className="w-8 h-8 text-synapse-purple animate-spin" />
                                                            <p className="text-xs text-gray-500 mt-2">Carregando video...</p>
                                                        </div>
                                                    )}
                                                    <video
                                                        ref={videoRef}
                                                        src={videoPreviewUrl}
                                                        controls
                                                        className="w-full max-h-[300px] object-contain bg-black"
                                                        onError={() => { setVideoError(true); setVideoLoading(false); }}
                                                        onLoadedData={() => setVideoLoading(false)}
                                                        onCanPlay={() => setVideoLoading(false)}
                                                        preload="metadata"
                                                    />
                                                </>
                                            ) : (
                                                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                                                    <ExclamationTriangleIcon className="w-10 h-10 mb-2 opacity-40" />
                                                    <p className="text-sm font-medium">Video indisponivel</p>
                                                    <p className="text-xs text-gray-600 mt-1">O arquivo pode ter sido movido ou deletado</p>
                                                </div>
                                            )}
                                            {/* Filename Badge */}
                                            <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/80 rounded-lg border border-white/10 text-[10px] text-gray-400 font-mono max-w-[80%] truncate backdrop-blur-sm">
                                                {videoFilename}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Date & Time (Side by Side) */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <label className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                                <ClockIcon className="w-4 h-4 text-synapse-purple" />
                                                Data
                                            </label>
                                            <input
                                                type="date"
                                                value={editDate}
                                                onChange={(e) => setEditDate(e.target.value)}
                                                className={clsx(
                                                    "w-full bg-black/40 border rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-synapse-purple/50 focus:ring-1 focus:ring-synapse-purple/20 transition-all font-mono",
                                                    editDate !== origValues.date
                                                        ? "border-synapse-purple/40 bg-synapse-purple/5"
                                                        : "border-white/10"
                                                )}
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                                <ClockIcon className="w-4 h-4 text-synapse-purple" />
                                                Horario
                                            </label>
                                            <input
                                                type="time"
                                                value={editTime}
                                                onChange={(e) => setEditTime(e.target.value)}
                                                className={clsx(
                                                    "w-full bg-black/40 border rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-synapse-purple/50 focus:ring-1 focus:ring-synapse-purple/20 transition-all font-mono",
                                                    editTime !== origValues.time
                                                        ? "border-synapse-purple/40 bg-synapse-purple/5"
                                                        : "border-white/10"
                                                )}
                                            />
                                        </div>
                                    </div>

                                    {/* Profile Selector */}
                                    <div className="space-y-2">
                                        <label className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                            <UserCircleIcon className="w-4 h-4 text-synapse-purple" />
                                            Perfil de Destino
                                        </label>
                                        <select
                                            value={selectedProfile}
                                            onChange={(e) => setSelectedProfile(e.target.value)}
                                            className={clsx(
                                                "w-full bg-black/40 border rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-synapse-purple/50 focus:ring-1 focus:ring-synapse-purple/20 transition-all appearance-none cursor-pointer",
                                                selectedProfile !== origValues.profile
                                                    ? "border-synapse-purple/40 bg-synapse-purple/5"
                                                    : "border-white/10"
                                            )}
                                        >
                                            {profiles.map((p) => (
                                                <option key={p.id} value={p.id} className="bg-[#0f0a15] text-white">
                                                    {p.label} {p.username ? `(@${p.username})` : ''}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* Caption */}
                                    <div className="space-y-2">
                                        <label className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                            <ChatBubbleBottomCenterTextIcon className="w-4 h-4 text-synapse-purple" />
                                            Legenda
                                        </label>
                                        <textarea
                                            value={caption}
                                            onChange={(e) => setCaption(e.target.value)}
                                            placeholder="Escreva a legenda do video..."
                                            rows={4}
                                            className={clsx(
                                                "w-full bg-black/40 border rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-synapse-purple/50 focus:ring-1 focus:ring-synapse-purple/20 transition-all resize-none placeholder:text-gray-600",
                                                caption !== origValues.caption
                                                    ? "border-synapse-purple/40 bg-synapse-purple/5"
                                                    : "border-white/10"
                                            )}
                                        />
                                        <div className="flex justify-between items-center">
                                            <p className={clsx(
                                                "text-[10px] font-mono",
                                                caption.length > 2000 ? "text-red-400" : "text-gray-600"
                                            )}>
                                                {caption.length} / 2200
                                            </p>
                                            {caption !== origValues.caption && (
                                                <p className="text-[10px] text-synapse-purple font-medium">Alterado</p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Privacy & Viral Music (Side by Side) */}
                                    <div className="grid grid-cols-2 gap-4">
                                        {/* Privacy */}
                                        <div className="space-y-2">
                                            <label className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                                <ShieldCheckIcon className="w-4 h-4 text-synapse-purple" />
                                                Privacidade
                                            </label>
                                            <select
                                                value={privacyLevel}
                                                onChange={(e) => setPrivacyLevel(e.target.value)}
                                                className={clsx(
                                                    "w-full bg-black/40 border rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-synapse-purple/50 focus:ring-1 focus:ring-synapse-purple/20 transition-all appearance-none cursor-pointer",
                                                    privacyLevel !== origValues.privacyLevel
                                                        ? "border-synapse-purple/40 bg-synapse-purple/5"
                                                        : "border-white/10"
                                                )}
                                            >
                                                <option value="public" className="bg-[#0f0a15]">Publico</option>
                                                <option value="friends" className="bg-[#0f0a15]">Amigos</option>
                                                <option value="private" className="bg-[#0f0a15]">Privado</option>
                                            </select>
                                        </div>

                                        {/* Viral Music Toggle */}
                                        <div className="space-y-2">
                                            <label className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
                                                <MusicalNoteIcon className="w-4 h-4 text-synapse-purple" />
                                                Viral Boost
                                            </label>
                                            <button
                                                type="button"
                                                onClick={() => setViralMusic(!viralMusic)}
                                                className={clsx(
                                                    "w-full rounded-xl px-4 py-3 text-sm font-bold transition-all border flex items-center justify-center gap-2",
                                                    viralMusic
                                                        ? "bg-synapse-purple/20 border-synapse-purple/50 text-synapse-purple shadow-[0_0_20px_rgba(139,92,246,0.15)]"
                                                        : "bg-black/40 border-white/10 text-gray-500 hover:border-white/20"
                                                )}
                                            >
                                                <MusicalNoteIcon className="w-4 h-4" />
                                                {viralMusic ? 'ATIVADO' : 'DESATIVADO'}
                                            </button>
                                        </div>
                                    </div>

                                    {/* Music Volume (only if viral music enabled) */}
                                    {viralMusic && (
                                        <div className="space-y-2 animate-in fade-in duration-200">
                                            <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                                                Volume da Musica: {Math.round(musicVolume * 100)}%
                                            </label>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.05"
                                                value={musicVolume}
                                                onChange={(e) => setMusicVolume(parseFloat(e.target.value))}
                                                className="w-full accent-synapse-purple h-2 bg-white/5 rounded-full"
                                            />
                                        </div>
                                    )}

                                    {/* Error Message (Read Only) */}
                                    {event.status === 'failed' && event.error_message && (
                                        <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/20">
                                            <span className="flex items-center gap-2 font-bold text-red-400 uppercase tracking-wider text-[10px] mb-2">
                                                <ExclamationTriangleIcon className="w-3.5 h-3.5" />
                                                Ultima Falha
                                            </span>
                                            <p className="text-xs text-red-300/80 font-mono leading-relaxed break-all max-h-24 overflow-y-auto custom-scrollbar">
                                                {event.error_message}
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {/* Footer */}
                                <div className="p-6 border-t border-white/5 bg-white/[0.02] flex items-center justify-between gap-4">
                                    <button
                                        onClick={onClose}
                                        className="px-6 py-3 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-all text-sm font-medium"
                                    >
                                        Cancelar
                                    </button>
                                    <div className="flex items-center gap-3">
                                        {hasChanges && (
                                            <span className="text-[10px] text-synapse-purple/70 font-medium animate-in fade-in">
                                                Alteracoes pendentes
                                            </span>
                                        )}
                                        <button
                                            onClick={handleSave}
                                            disabled={saving || !hasChanges}
                                            className={clsx(
                                                "px-8 py-3 rounded-xl text-sm font-bold transition-all flex items-center gap-2",
                                                saving || !hasChanges
                                                    ? "bg-gray-700/50 text-gray-500 cursor-not-allowed border border-white/5"
                                                    : "bg-synapse-purple text-white hover:bg-synapse-purple/80 shadow-[0_0_30px_rgba(139,92,246,0.3)] hover:shadow-[0_0_40px_rgba(139,92,246,0.4)]"
                                            )}
                                        >
                                            <CheckIcon className="w-5 h-5" />
                                            {saving ? 'Salvando...' : 'Salvar Alteracoes'}
                                        </button>
                                    </div>
                                </div>

                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
