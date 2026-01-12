'use client';

import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { TikTokProfile } from '../types';
import { NeonButton } from './NeonButton';
import { XMarkIcon, CalendarDaysIcon, ClockIcon, UserGroupIcon, SparklesIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format, addDays, setHours, setMinutes, parseISO, getDay } from 'date-fns';

interface SchedulingModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (data: SchedulingData) => void;
    initialDate: Date;
    profiles: TikTokProfile[];
    initialViralBoost?: boolean;
}

export interface SchedulingData {
    scheduled_time: string; // ISO string
    profile_ids: string[];
    description?: string;
    viral_music_enabled: boolean;
    music_volume?: number;
    trend_category?: string;
}

export default function SchedulingModal({
    isOpen,
    onClose,
    onSubmit,
    initialDate,
    profiles,
    initialViralBoost = false
}: SchedulingModalProps) {
    const [selectedDate, setSelectedDate] = useState('');
    const [selectedTime, setSelectedTime] = useState('10:00');
    const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
    const [viralBoost, setViralBoost] = useState(initialViralBoost);
    const [musicVolume, setMusicVolume] = useState<number>(0); // Default 0 (Silent)
    const [trendCategory, setTrendCategory] = useState('General');
    const [isAutoScheduling, setIsAutoScheduling] = useState(false);

    // Hyper-Caption State
    const [description, setDescription] = useState('');
    const [isRewriting, setIsRewriting] = useState(false);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [generatedHashtags, setGeneratedHashtags] = useState<string[]>([]);

    const handleMagicRewrite = async () => {
        if (!description) return;
        setIsRewriting(true);
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_URL}/api/v1/oracle/rewrite_caption`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ draft: description, tone: "Viral/Clickbait" }) // Hardcoded tone for now or add UI
            });

            if (res.ok) {
                const data = await res.json();
                if (data.options) setSuggestions(data.options);
                if (data.hashtags) setGeneratedHashtags(data.hashtags);
            }
        } catch (e) {
            console.error("Rewrite failed", e);
        } finally {
            setIsRewriting(false);
        }
    };

    const handleAutoSchedule = async () => {
        if (selectedProfiles.length === 0) return;
        setIsAutoScheduling(true);
        const profileId = selectedProfiles[0];

        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_URL}/api/v1/scheduler/suggestion/${profileId}`);
            const data = await res.json();

            if (data.best_times && data.best_times.length > 0) {
                // Find next occurrence
                // Format: { day: "Monday", hour: 18 }
                const today = new Date();
                const dayMap: { [key: string]: number } = {
                    "Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3,
                    "Thursday": 4, "Friday": 5, "Saturday": 6
                };

                // Sort by nearest future slot
                let bestSlot: Date | null = null;

                for (const slot of data.best_times) {
                    const targetDayIndex = dayMap[slot.day];
                    if (targetDayIndex === undefined) continue;

                    let nextDate = new Date();
                    nextDate.setHours(slot.hour, 0, 0, 0);

                    // Logic to find next 'Monday' (e.g.)
                    const currentDayIndex = getDay(nextDate);
                    let daysUntil = (targetDayIndex + 7 - currentDayIndex) % 7;

                    // If today is the day but hour passed, add 7 days
                    if (daysUntil === 0 && nextDate < new Date()) {
                        daysUntil = 7;
                    }

                    nextDate = addDays(nextDate, daysUntil);

                    if (!bestSlot || nextDate < bestSlot) {
                        bestSlot = nextDate;
                    }
                }

                if (bestSlot) {
                    setSelectedDate(format(bestSlot, 'yyyy-MM-dd'));
                    setSelectedTime(format(bestSlot, 'HH:mm'));
                }
            } else {
                // Fallback or Toast?
                console.log("No suggestions available");
            }
        } catch (e) {
            console.error("Auto-schedule failed", e);
        } finally {
            setIsAutoScheduling(false);
        }
    };

    useEffect(() => {
        if (isOpen && initialDate) {
            setSelectedDate(format(initialDate, 'yyyy-MM-dd'));
            setViralBoost(initialViralBoost);
            // Reset profiles if needed, or keep selected if implementing sticky selection
        }
    }, [isOpen, initialDate, initialViralBoost]);

    const toggleProfile = (id: string) => {
        setSelectedProfiles(prev =>
            prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
        );
    };

    const [conflict, setConflict] = useState<{ message: string; suggested_time?: string } | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setConflict(null);

        try {
            const dateTime = new Date(`${selectedDate}T${selectedTime}`);

            await onSubmit({
                scheduled_time: dateTime.toISOString(),
                profile_ids: selectedProfiles,
                description: description,
                viral_music_enabled: viralBoost,
                music_volume: viralBoost ? musicVolume : undefined,
                trend_category: viralBoost ? trendCategory : undefined
            });
            onClose();
        } catch (error: any) {
            if (error.status === 409 && error.response?.suggested_time) {
                // Parse suggestion to update local state
                const suggestion = new Date(error.response.suggested_time);
                setConflict({
                    message: "Conflito de horário detectado!",
                    suggested_time: error.response.suggested_time
                });
            } else {
                console.error("Scheduling error", error);
            }
        }
    };

    const applySuggestion = () => {
        if (conflict?.suggested_time) {
            const dt = new Date(conflict.suggested_time);
            setSelectedDate(format(dt, 'yyyy-MM-dd'));
            setSelectedTime(format(dt, 'HH:mm'));
            setConflict(null);
        }
    };

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4 text-center">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-[#0f0a15] border border-white/10 p-6 text-left align-middle shadow-xl transition-all">
                                <Dialog.Title
                                    as="h3"
                                    className="text-lg font-bold text-white flex justify-between items-center mb-6"
                                >
                                    <span>Agendar Publicação</span>
                                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                                        <XMarkIcon className="w-5 h-5" />
                                    </button>
                                </Dialog.Title>

                                {conflict && (
                                    <div className="mb-6 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-200">
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

                                <form onSubmit={handleSubmit} className="space-y-6">
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
                                                    value={selectedTime}
                                                    onChange={(e) => setSelectedTime(e.target.value)}
                                                    className="w-full bg-black/30 border border-white/10 rounded-lg py-2 pl-9 pr-3 text-sm text-white focus:border-synapse-purple focus:ring-1 focus:ring-synapse-purple outline-none"
                                                />
                                            </div>
                                        </div>
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
                                                        {/* Avatar helper */}
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
                                                        <p className="text-[10px] text-gray-500 truncate">@{profile.username || 'unknown'}</p>
                                                    </div>
                                                    <div className={clsx("w-4 h-4 rounded-full border flex items-center justify-center", selectedProfiles.includes(profile.id) ? "border-synapse-purple bg-synapse-purple" : "border-gray-500")}>
                                                        {selectedProfiles.includes(profile.id) && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        {selectedProfiles.length === 0 && <p className="text-xs text-red-500 mt-1">* Selecione pelo menos um perfil</p>}
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
                                                    <div className="flex justify-between text-[10px] text-gray-500 font-mono uppercase">
                                                        <span>Silent</span>
                                                        <span>Mix</span>
                                                        <span>Loud</span>
                                                    </div>
                                                </div>

                                                {/* Trend Category */}
                                                <div className="space-y-3">
                                                    <label className="text-xs font-mono text-gray-400 tracking-wider">TREND CATEGORY</label>
                                                    <select
                                                        value={trendCategory}
                                                        onChange={(e) => setTrendCategory(e.target.value)}
                                                        className="w-full bg-black/40 border border-gray-800 rounded px-3 py-2 text-sm text-gray-300 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/20 transition-all"
                                                    >
                                                        <option value="General">🌎 General Trending</option>
                                                        <option value="Dance">💃 Dance & Challenges</option>
                                                        <option value="Tech">🤖 Tech & AI</option>
                                                        <option value="Meme">😂 Meme & Comedy</option>
                                                        <option value="Lipsync">🎤 Lip Sync</option>
                                                    </select>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="pt-4 flex gap-3">
                                        <button
                                            type="button"
                                            onClick={onClose}
                                            className="flex-1 px-4 py-2 rounded-lg border border-white/10 text-gray-400 hover:bg-white/5 hover:text-white transition-colors text-sm"
                                        >
                                            Cancelar
                                        </button>
                                        <NeonButton
                                            type="submit"
                                            variant="primary"
                                            className="flex-1"
                                            disabled={selectedProfiles.length === 0}
                                        >
                                            Confirmar Agendamento
                                        </NeonButton>
                                    </div>

                                </form>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
