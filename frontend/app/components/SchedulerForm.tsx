'use client';

import React, { useState, useEffect, useCallback, Fragment } from 'react';
import { TikTokProfile } from '../types';
import { NeonButton } from './NeonButton';
import { XMarkIcon, CalendarDaysIcon, ClockIcon, UserGroupIcon, SparklesIcon, MusicalNoteIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format, addDays, getDay } from 'date-fns';
import { toast } from 'sonner';
import { getApiUrl } from '../utils/apiClient';
import { ViralSound } from './ViralSoundPicker';

export interface SchedulingData {
    scheduled_time: string; // ISO string
    profile_ids: string[];
    description?: string;
    video_path: string;
    viral_music_enabled: boolean;
    music_volume?: number;
    sound_id?: string;
    sound_title?: string;
    trend_category?: string;
}

export interface SchedulerFormProps {
    onSubmit: (data: SchedulingData) => void;
    onCancel: () => void;
    initialDate: Date;
    profiles: TikTokProfile[];
    initialViralBoost?: boolean;
    initialData?: Partial<SchedulingData>;
    className?: string; // Added className
}

export default function SchedulerForm({
    onSubmit,
    onCancel,
    initialDate,
    profiles,
    initialViralBoost = false,
    initialData,
    className
}: SchedulerFormProps) {
    // 🧠 State Initialization
    const dt = initialData?.scheduled_time ? new Date(initialData.scheduled_time) : initialDate;

    const [selectedDate, setSelectedDate] = useState(initialData?.scheduled_time ? format(dt, 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd'));
    const [selectedTime, setSelectedTime] = useState(initialData?.scheduled_time ? format(dt, 'HH:mm') : '10:00');

    const [selectedProfiles, setSelectedProfiles] = useState<string[]>(initialData?.profile_ids || []);
    const [viralBoost, setViralBoost] = useState(initialData?.viral_music_enabled ?? initialViralBoost);

    const [musicVolume, setMusicVolume] = useState<number>(initialData?.music_volume ?? 0);
    const [selectedSound, setSelectedSound] = useState<ViralSound | null>(initialData?.sound_id ? {
        id: initialData.sound_id,
        title: initialData.sound_title || 'Música Selecionada',
        author: 'Desconhecido',
        category: 'General',
        usage_count: 0
    } as any : null);

    const [isAutoScheduling, setIsAutoScheduling] = useState(false);
    const [aiAutoSelect, setAiAutoSelect] = useState(true);
    const [isAutoSelecting, setIsAutoSelecting] = useState(false);

    // Upload State (Can be passed in or handled here. For now, handled here for standalone usage)
    const [videoPath, setVideoPath] = useState<string>(initialData?.video_path || "");
    const [isUploading, setIsUploading] = useState(false);

    // 🧠 Validation State
    const [validation, setValidation] = useState<{
        isValid: boolean;
        canProceed: boolean;
        issues: Array<{ severity: string; code: string; message: string; suggested_fix?: string }>;
        suggestedTime?: string;
    } | null>(null);
    const [isValidating, setIsValidating] = useState(false);
    const [conflict, setConflict] = useState<{ message: string; suggested_time?: string } | null>(null);

    // Hyper-Caption State
    const [description, setDescription] = useState(initialData?.description || '');
    const [isRewriting, setIsRewriting] = useState(false);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [generatedHashtags, setGeneratedHashtags] = useState<string[]>([]);

    // Effects
    useEffect(() => {
        if (initialDate) {
            setSelectedDate(format(initialDate, 'yyyy-MM-dd'));
            // Optionally update time if initialDate includes it, but usually standard initialDate has 00:00
        }
    }, [initialDate]);

    useEffect(() => {
        if (initialData?.scheduled_time) {
            const d = new Date(initialData.scheduled_time);
            setSelectedDate(format(d, 'yyyy-MM-dd'));
            setSelectedTime(format(d, 'HH:mm'));
        }
        if (initialData?.profile_ids) setSelectedProfiles(initialData.profile_ids);
        if (initialData?.description) setDescription(initialData.description);
        if (initialData?.video_path) setVideoPath(initialData.video_path);
    }, [initialData]);

    const handleFileUpload = async (file: File) => {
        if (!selectedProfiles[0]) {
            toast.error("Selecione um perfil primeiro!");
            return;
        }
        setIsUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('profile_id', selectedProfiles[0]);

        try {
            const API_URL = getApiUrl();
            const res = await fetch(`${API_URL}/api/v1/ingest/upload`, {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                setVideoPath(`d:\\APPS - ANTIGRAVITY\\Synapse\\data\\pending\\${data.filename}`);
            } else {
                toast.error("Upload failed");
            }
        } catch (e) {
            console.error("Upload error", e);
            toast.error("Erro no upload");
        } finally {
            setIsUploading(false);
        }
    };

    const handleMagicRewrite = async () => {
        if (!description) return;
        setIsRewriting(true);
        try {
            const API_URL = getApiUrl();
            const res = await fetch(`${API_URL}/api/v1/oracle/rewrite_caption`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ draft: description, tone: "Viral/Clickbait" })
            });

            if (res.ok) {
                const data = await res.json();
                if (data.options) setSuggestions(data.options);
                if (data.hashtags) setGeneratedHashtags(data.hashtags);
            } else {
                toast.error("IA Ocupada. Tente novamente.");
            }
        } catch (e) {
            console.error(e);
            toast.error("Falha ao reescrever.");
        } finally {
            setIsRewriting(false);
        }
    };

    const handleAutoSchedule = async () => {
        if (selectedProfiles.length === 0) return;
        setIsAutoScheduling(true);
        const profileId = selectedProfiles[0];

        try {
            const API_URL = getApiUrl();
            const res = await fetch(`${API_URL}/api/v1/scheduler/suggestion/${profileId}`);
            const data = await res.json();

            if (data.best_times && data.best_times.length > 0) {
                const dayMap: { [key: string]: number } = {
                    "Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3,
                    "Thursday": 4, "Friday": 5, "Saturday": 6
                };

                let bestSlot: Date | null = null;
                let reason = "";

                for (const slot of data.best_times) {
                    const targetDayIndex = dayMap[slot.day];
                    if (targetDayIndex === undefined) continue;

                    let nextDate = new Date();
                    nextDate.setHours(slot.hour, 0, 0, 0);
                    const currentDayIndex = getDay(nextDate);
                    let daysUntil = (targetDayIndex + 7 - currentDayIndex) % 7;

                    if (daysUntil === 0 && nextDate < new Date()) daysUntil = 7;
                    nextDate = addDays(nextDate, daysUntil);

                    if (!bestSlot || nextDate < bestSlot) {
                        bestSlot = nextDate;
                        reason = slot.reason || "Horário de pico";
                    }
                }

                if (bestSlot) {
                    setSelectedDate(format(bestSlot, 'yyyy-MM-dd'));
                    setSelectedTime(format(bestSlot, 'HH:mm'));
                    toast.success("Horário Otimizado! 🚀", {
                        description: `Sugerido: ${format(bestSlot, "eeee 'às' HH:mm")} (${reason})`
                    });
                }
            } else {
                toast.warning("Sem dados de inteligência suficiente.");
            }
        } catch (e) {
            console.error(e);
            toast.error("Erro ao consultar Oráculo.");
        } finally {
            setIsAutoScheduling(false);
        }
    };

    const validateScheduleTime = useCallback(async (date: string, time: string, profileId: string) => {
        if (!date || !time || !profileId) {
            setValidation(null);
            return;
        }

        setIsValidating(true);
        try {
            const API_URL = getApiUrl();
            const proposedTime = new Date(`${date}T${time}`).toISOString();

            const res = await fetch(`${API_URL}/api/v1/logic/check-conflict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile_id: profileId,
                    proposed_time: proposedTime
                })
            });

            if (res.ok) {
                const data = await res.json();
                setValidation({
                    isValid: data.is_valid,
                    canProceed: data.can_proceed,
                    issues: data.issues || [],
                    suggestedTime: data.suggested_time
                });
            }
        } catch (e) {
            console.error('Validation error:', e);
        } finally {
            setIsValidating(false);
        }
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => {
            if (selectedDate && selectedTime && selectedProfiles[0]) {
                validateScheduleTime(selectedDate, selectedTime, selectedProfiles[0]);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [selectedDate, selectedTime, selectedProfiles, validateScheduleTime]);

    const handleAiAutoSelect = async () => {
        setIsAutoSelecting(true);
        try {
            const API_URL = getApiUrl();
            const res = await fetch(`${API_URL}/api/v1/viral-sounds/auto-select`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_description: description || undefined,
                    prefer_exploding: true,
                    min_viral_score: 60.0
                })
            });

            if (res.ok) {
                const data = await res.json();
                if (data.success) {
                    const autoSelected: ViralSound = {
                        id: data.sound_id,
                        title: data.sound_title,
                        author: data.sound_author || 'Artista',
                        cover_url: '',
                        preview_url: '',
                        duration: 30,
                        usage_count: 0,
                        category: 'General',
                        viral_score: data.viral_score || 0,
                        status: data.status || 'normal',
                        niche: data.niche || 'general',
                        growth_rate: 0
                    };
                    setSelectedSound(autoSelected);
                    toast.success(`🤖 IA selecionou: "${data.sound_title}"`);
                } else {
                    toast.error(data.reason || 'IA não encontrou música adequada');
                }
            }
        } catch (e) {
            console.error(e);
            toast.error('Erro ao conectar com IA');
        } finally {
            setIsAutoSelecting(false);
        }
    };

    const handleFormSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setConflict(null);

        try {
            const dateTime = new Date(`${selectedDate}T${selectedTime}`);
            await onSubmit({
                scheduled_time: dateTime.toISOString(),
                profile_ids: selectedProfiles,
                description: description,
                video_path: videoPath,
                viral_music_enabled: viralBoost,
                music_volume: viralBoost ? musicVolume : undefined,
                sound_id: viralBoost && selectedSound ? selectedSound.id : undefined,
                sound_title: viralBoost && selectedSound ? selectedSound.title : undefined
            });
        } catch (error: any) {
            if (error.status === 409 && error.response?.suggested_time) {
                const suggestion = new Date(error.response.suggested_time);
                setConflict({
                    message: "Conflito de horário detectado!",
                    suggested_time: error.response.suggested_time
                });
            } else {
                console.error("Scheduling error", error);

                // If it's not a conflict, we might want to let the parent handle it or show generic error
                // But typically onSubmit prop is void, so we rely on parent to catch if it throws?
                // Actually the parent onSubmit is usually async.
            }
        }
    };

    const toggleProfile = (id: string) => {
        setSelectedProfiles(prev =>
            prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
        );
    };

    const applySuggestion = () => {
        if (conflict?.suggested_time) {
            const d = new Date(conflict.suggested_time);
            setSelectedDate(format(d, 'yyyy-MM-dd'));
            setSelectedTime(format(d, 'HH:mm'));
            setConflict(null);
        }
    };

    return (
        <form onSubmit={handleFormSubmit} className={clsx("space-y-6", className)}>

            {/* Conflict Alert */}
            {conflict && (
                <div className="mb-6 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-200 animate-in fade-in slide-in-from-top-2">
                    <div className="flex items-start gap-3">
                        <div className="flex-1">
                            <h4 className="font-bold text-sm mb-1">⚠️ {conflict.message}</h4>
                            <p className="text-xs opacity-80 mb-3">
                                Este horário já está ocupado. Sugerimos agendar para:
                                <span className="font-mono ml-1 font-bold text-white">
                                    {conflict.suggested_time && format(new Date(conflict.suggested_time), "HH:mm")}
                                </span>
                            </p>
                            <button
                                type="button"
                                onClick={applySuggestion}
                                className="text-xs bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-200 px-3 py-1.5 rounded-md border border-yellow-500/30 transition-colors"
                            >
                                Aceitar Sugestão e Atualizar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Date & Time */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Data</label>
                    <div className="relative">
                        <CalendarDaysIcon className="absolute left-3 top-2.5 w-4 h-4 text-synapse-purple pointer-events-none" />
                        <input
                            type="date"
                            required
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="w-full bg-black/30 border border-white/10 rounded-lg py-2 pl-9 pr-3 text-sm text-white focus:border-synapse-purple focus:ring-1 focus:ring-synapse-purple outline-none"
                        />
                    </div>
                </div>
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Horário</label>
                        <button
                            type="button"
                            onClick={handleAutoSchedule}
                            disabled={isAutoScheduling || selectedProfiles.length === 0}
                            className="flex items-center gap-1 text-[10px] text-synapse-purple hover:text-synapse-purple/80 transition-colors disabled:opacity-50"
                        >
                            {isAutoScheduling ? (
                                <span className="animate-pulse">Consulting Oracle...</span>
                            ) : (
                                <>
                                    <SparklesIcon className="w-3 h-3" />
                                    Auto-Schedule
                                </>
                            )}
                        </button>
                    </div>
                    <div className="relative">
                        <ClockIcon className="absolute left-3 top-2.5 w-4 h-4 text-synapse-purple pointer-events-none" />
                        <input
                            type="time"
                            required
                            step="300"
                            value={selectedTime}
                            onChange={(e) => setSelectedTime(e.target.value)}
                            className={clsx(
                                "w-full bg-black/30 rounded-lg py-2 pl-9 pr-3 text-sm text-white focus:ring-1 outline-none transition-all",
                                validation && !validation.canProceed
                                    ? "border-2 border-red-500 focus:border-red-500 focus:ring-red-500"
                                    : validation && validation.issues?.some(i => i.severity === 'warning')
                                        ? "border-2 border-yellow-500 focus:border-yellow-500 focus:ring-yellow-500"
                                        : validation && validation.issues?.some(i => i.code === 'PRIME_TIME')
                                            ? "border-2 border-green-500 focus:border-green-500 focus:ring-green-500"
                                            : "border border-white/10 focus:border-synapse-purple focus:ring-synapse-purple"
                            )}
                        />
                        {isValidating && (
                            <div className="absolute right-3 top-2.5">
                                <div className="w-4 h-4 border-2 border-synapse-purple border-t-transparent rounded-full animate-spin" />
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Validation Feedback */}
            {validation && validation.issues && validation.issues.length > 0 && (
                <div className={clsx(
                    "p-3 rounded-lg border transition-all animate-in fade-in slide-in-from-top-2",
                    !validation.canProceed
                        ? "bg-red-500/10 border-red-500/30"
                        : validation.issues.some(i => i.severity === 'warning')
                            ? "bg-yellow-500/10 border-yellow-500/30"
                            : "bg-green-500/10 border-green-500/30"
                )}>
                    <div className="flex items-start gap-2">
                        {!validation.canProceed ? (
                            <ExclamationTriangleIcon className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                        ) : validation.issues.some(i => i.severity === 'warning') ? (
                            <ExclamationTriangleIcon className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                        ) : (
                            <CheckCircleIcon className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                        )}
                        <div className="flex-1 space-y-1">
                            {validation.issues.map((issue, idx) => (
                                <p key={idx} className={clsx(
                                    "text-xs",
                                    issue.severity === 'error' ? "text-red-300" :
                                        issue.severity === 'warning' ? "text-yellow-300" :
                                            "text-green-300"
                                )}>
                                    {issue.message}
                                    {issue.suggested_fix && (
                                        <span className="block text-gray-400 mt-0.5">{issue.suggested_fix}</span>
                                    )}
                                </p>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Video Upload Logic */}
            <div className="space-y-2">
                <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Vídeo</label>
                {!videoPath ? (
                    <div
                        onClick={() => !isUploading && document.getElementById('scheduler-upload')?.click()}
                        className={`border-2 border-dashed border-white/10 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all ${isUploading ? 'opacity-50 cursor-wait' : 'hover:bg-white/5 hover:border-synapse-purple/50'}`}
                    >
                        <input
                            id="scheduler-upload"
                            type="file"
                            accept=".mp4,.mov,.avi"
                            className="hidden"
                            disabled={isUploading || selectedProfiles.length === 0}
                            onChange={(e) => {
                                if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                            }}
                        />
                        {selectedProfiles.length === 0 ? (
                            <p className="text-xs text-gray-500">Selecione um perfil primeiro</p>
                        ) : isUploading ? (
                            <div className="flex flex-col items-center gap-2">
                                <div className="w-5 h-5 border-2 border-synapse-purple border-t-transparent rounded-full animate-spin" />
                                <span className="text-xs text-synapse-purple">Enviando para o cofre...</span>
                            </div>
                        ) : (
                            <>
                                <p className="text-xs text-gray-300 font-bold">Clique para enviar vídeo</p>
                                <p className="text-[10px] text-gray-500">MP4, MOV (Max 500MB)</p>
                            </>
                        )}
                    </div>
                ) : (
                    <div className="flex items-center justify-between p-3 bg-synapse-emerald/10 border border-synapse-emerald/30 rounded-xl">
                        <div className="flex items-center gap-3 overflow-hidden">
                            <div className="w-8 h-8 rounded bg-synapse-emerald/20 flex items-center justify-center text-synapse-emerald">
                                <span className="text-xs">VID</span>
                            </div>
                            <span className="text-xs text-synapse-emerald font-mono truncate">{videoPath.split('\\').pop()?.split('/').pop()}</span>
                        </div>
                        <button onClick={() => setVideoPath("")} type="button" className="text-gray-500 hover:text-white transition-colors">
                            <XMarkIcon className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>

            {/* Profiles Selection */}
            <div className="space-y-2">
                <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block flex items-center gap-2">
                    <UserGroupIcon className="w-3 h-3" />
                    Selecionar Perfis
                </label>
                <div className="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto custom-scrollbar p-1">
                    {profiles.map(profile => (
                        <div
                            key={profile.id}
                            onClick={() => toggleProfile(profile.id)}
                            className={clsx(
                                "flex items-center gap-3 p-2 rounded-lg cursor-pointer border transition-all",
                                selectedProfiles.includes(profile.id)
                                    ? "bg-synapse-purple/20 border-synapse-purple"
                                    : "bg-white/5 border-transparent hover:bg-white/10 hover:border-white/10"
                            )}
                        >
                            <div className="w-8 h-8 rounded-full bg-gray-700 overflow-hidden flex-shrink-0">
                                {profile.avatar_url ? (
                                    <img src={profile.avatar_url} alt={profile.label} className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-[10px] font-bold">
                                        {profile.label.substring(0, 2).toUpperCase()}
                                    </div>
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className={clsx("text-sm font-medium truncate", selectedProfiles.includes(profile.id) ? "text-synapse-purple" : "text-white")}>
                                    {profile.label}
                                </p>
                            </div>
                            <div className={clsx("w-4 h-4 rounded-full border flex items-center justify-center", selectedProfiles.includes(profile.id) ? "border-synapse-purple bg-synapse-purple" : "border-gray-500")}>
                                {selectedProfiles.includes(profile.id) && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Description & Hyper-Caption */}
            <div className="space-y-2">
                <div className="flex justify-between items-center">
                    <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Legenda (Caption)</label>
                    <button
                        type="button"
                        onClick={handleMagicRewrite}
                        disabled={!description || isRewriting}
                        className="flex items-center gap-1 text-[10px] text-synapse-cyan hover:text-synapse-cyan/80 transition-colors disabled:opacity-50"
                    >
                        {isRewriting ? (
                            <span className="animate-pulse">Rewriting...</span>
                        ) : (
                            <>
                                <SparklesIcon className="w-3 h-3 text-synapse-cyan" />
                                Magic Rewrite
                            </>
                        )}
                    </button>
                </div>
                <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Digite sua legenda inicial aqui..."
                    rows={3}
                    className="w-full bg-black/30 border border-white/10 rounded-lg py-2 px-3 text-sm text-white focus:border-synapse-purple focus:ring-1 focus:ring-synapse-purple outline-none resize-none"
                />
                {/* Rewrite Suggestions */}
                {suggestions.length > 0 && (
                    <div className="bg-synapse-cyan/5 border border-synapse-cyan/20 rounded-lg p-3 space-y-2 animate-in fade-in slide-in-from-top-2">
                        <p className="text-[10px] font-mono text-synapse-cyan uppercase">Sugestões Virais:</p>
                        {suggestions.map((opt, idx) => (
                            <div
                                key={idx}
                                onClick={() => {
                                    setDescription(opt);
                                    setSuggestions([]);
                                }}
                                className="p-2 bg-black/40 hover:bg-synapse-cyan/10 border border-transparent hover:border-synapse-cyan/30 rounded cursor-pointer transition-all text-xs text-gray-300 hover:text-white"
                            >
                                "{opt}"
                            </div>
                        ))}
                        <div className="flex gap-2 flex-wrap pt-1">
                            {generatedHashtags.map(tag => (
                                <span key={tag} onClick={() => setDescription(prev => prev + " " + tag)} className="cursor-pointer text-[10px] text-blue-400 hover:underline">{tag}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Viral Boost Controls */}
            <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-synapse-purple/10 border border-synapse-purple/20">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${viralBoost ? 'bg-synapse-purple animate-pulse' : 'bg-gray-600'}`} />
                        <span className="text-sm text-white font-medium">Viral Audio Boost</span>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            checked={viralBoost}
                            onChange={(e) => setViralBoost(e.target.checked)}
                            className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-synapse-purple"></div>
                    </label>
                </div>

                {viralBoost && (
                    <div className="space-y-6 animate-in slide-in-from-top-2 duration-300">
                        {/* Volume Control */}
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-xs font-mono text-blue-400 tracking-wider">VIRAL VOLUME</span>
                                <span className="text-xs font-mono text-cyan-300">
                                    {musicVolume === 0 ? 'MUTE (ALGO ONLY)' : `${musicVolume}%`}
                                </span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                step="5"
                                value={musicVolume}
                                onChange={(e) => setMusicVolume(parseInt(e.target.value))}
                                className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 hover:accent-cyan-400 transition-all"
                            />
                        </div>

                        {/* Viral Sound Selection */}
                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <label className="text-xs font-mono text-gray-400 tracking-wider">SOM VIRAL</label>
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] text-gray-500">Manual</span>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={aiAutoSelect}
                                            onChange={(e) => {
                                                setAiAutoSelect(e.target.checked);
                                                if (e.target.checked) setSelectedSound(null);
                                            }}
                                            className="sr-only peer"
                                        />
                                        <div className="w-7 h-4 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-cyan-500 peer-checked:to-emerald-500"></div>
                                    </label>
                                    <span className="text-[10px] text-cyan-400 font-bold">🤖 IA</span>
                                </div>
                            </div>

                            {aiAutoSelect ? (
                                <div className="space-y-2">
                                    {selectedSound ? (
                                        <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-cyan-500/10 to-emerald-500/10 border border-cyan-500/30">
                                            <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 flex items-center justify-center">
                                                <span className="text-lg">🤖</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium text-white truncate">{selectedSound.title}</p>
                                                <p className="text-xs text-gray-400 truncate">
                                                    {selectedSound.author} • Score: {selectedSound.viral_score?.toFixed(0) || '?'}
                                                </p>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400 font-bold">
                                                    IA PICK
                                                </span>
                                                <button
                                                    type="button"
                                                    onClick={handleAiAutoSelect}
                                                    className="text-[10px] text-gray-500 hover:text-cyan-400 transition-colors"
                                                >
                                                    Trocar
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={handleAiAutoSelect}
                                            disabled={isAutoSelecting}
                                            className="w-full py-4 border border-dashed border-cyan-500/30 rounded-xl flex flex-col items-center justify-center bg-cyan-500/5 hover:bg-cyan-500/10 transition-all group"
                                        >
                                            {isAutoSelecting ? (
                                                <div className="flex items-center gap-2 text-cyan-400">
                                                    <div className="w-4 h-4 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                                                    <span className="text-xs font-bold">Analisando tendências...</span>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                                                        <SparklesIcon className="w-4 h-4 text-cyan-400" />
                                                    </div>
                                                    <p className="text-xs font-bold text-cyan-300">Ativar IA Selector</p>
                                                    <p className="text-[10px] text-cyan-500/60">Encontra o melhor áudio para seu nicho</p>
                                                </>
                                            )}
                                        </button>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-4 border border-dashed border-white/10 rounded-xl">
                                    <p className="text-xs text-gray-500">Seletor Manual (TODO)</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
                <button
                    type="button"
                    onClick={onCancel}
                    className="flex-1 py-2.5 rounded-lg border border-white/10 text-sm font-medium hover:bg-white/5 transition-colors"
                >
                    Cancelar
                </button>
                <NeonButton
                    type="submit"
                    className="flex-1 py-2.5 justify-center font-bold"
                >
                    Confirmar Agendamento
                </NeonButton>
            </div>
        </form>
    );
}
