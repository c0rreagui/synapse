import React, { useEffect, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, CalendarIcon, MusicalNoteIcon, PlayCircleIcon, TrashIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'; // [SYN-UX] Added ExclamationTriangleIcon
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import clsx from 'clsx';
import { ScheduleEvent, TikTokProfile } from '../types';
import ProfileRepairModal from './ProfileRepairModal'; // [SYN-UX] Import Repair Modal

interface ScheduledVideosModalProps {
    isOpen: boolean;
    onClose: () => void;
    profiles: TikTokProfile[];
    onDelete?: (id: string) => void;
    onUpdate?: () => void; // Sync trigger
}

export default function ScheduledVideosModal({ isOpen, onClose, profiles, onDelete, onUpdate }: ScheduledVideosModalProps) {
    const [events, setEvents] = useState<ScheduleEvent[]>([]);
    const [loading, setLoading] = useState(false);

    // [SYN-UX] Repair Logic
    const [repairProfile, setRepairProfile] = useState<TikTokProfile | null>(null);

    // Use centralized API Client for robust local connections
    // Note: requires import { getApiUrl } from '../utils/apiClient'; - please ensure import is added.
    const API_URL = (typeof window !== 'undefined' && window.location.hostname === 'localhost')
        ? 'http://127.0.0.1:8000'
        : (process.env.NEXT_PUBLIC_API_URL || '');

    const fetchEvents = async () => {
        setLoading(true);
        try {
            // Direct fetch to backend to avoid proxy 500s
            const res = await fetch(`${API_URL}/api/v1/scheduler/list`);

            if (res.ok) {
                const data = await res.json();
                const sorted = data.sort((a: any, b: any) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime());
                setEvents(sorted);
            } else {
                console.error("Failed to load events:", res.status);
                toast.error("Erro de conexão com servidor (500)");
            }
        } catch (error) {
            console.error("Failed to load schedule", error);
            toast.error("Erro ao carregar agendamentos");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) {
            fetchEvents();
            setEditingId(null);
        }
    }, [isOpen]);

    const [deletingConfirmationId, setDeletingConfirmationId] = useState<string | null>(null);

    const handleDelete = async (id: string) => {
        if (deletingConfirmationId === id) {
            try {
                const res = await fetch(`${API_URL}/api/v1/scheduler/${id}`, { method: 'DELETE' });
                if (res.ok) {
                    setEvents(prev => prev.filter(e => e.id !== id));
                    toast.success("Agendamento cancelado");
                    if (onDelete) onDelete(id);
                    if (onUpdate) onUpdate();
                    setDeletingConfirmationId(null);
                } else {
                    toast.error("Erro ao cancelar");
                }
            } catch (e) {
                toast.error("Erro ao conectar");
            }
        } else {
            setDeletingConfirmationId(id);
            // Reset after 3s
            setTimeout(() => setDeletingConfirmationId(curr => curr === id ? null : curr), 3000);
        }
    };

    const getProfileName = (id: string) => {
        const p = profiles.find(pr => pr.id === id || pr.username === id);
        return p?.username || p?.label || id;
    };

    const getProfileImage = (id: string) => {
        const p = profiles.find(pr => pr.id === id || pr.username === id);
        return p?.avatar_url || null;
    };

    const handleEditTime = async (id: string, newTimeStr: string) => {
        if (!newTimeStr) {
            toast.error("Por favor, selecione um horário válido.");
            return;
        }

        try {
            const date = new Date(newTimeStr);
            if (isNaN(date.getTime())) {
                toast.error("Data inválida.");
                return;
            }

            console.log("Updating event", id, "to", date.toISOString());

            const url = `${API_URL}/api/v1/scheduler/${id}`;
            console.log("Fetching URL:", url);
            const res = await fetch(url, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scheduled_time: date.toISOString() })
            });

            if (res.ok) {
                const updatedEvent = await res.json();
                setEvents(prev => prev.map(e => e.id === id ? updatedEvent : e));
                toast.success("Horário atualizado com sucesso!");
                setEditingId(null);
                if (onUpdate) onUpdate(); // Trigger parent refresh
            } else {
                console.error("Update failed status:", res.status, res.statusText);
                const text = await res.text();
                console.error("Update failed body:", text);

                let detail = "Falha ao atualizar horário";
                try {
                    const json = JSON.parse(text);
                    if (json.detail) detail = typeof json.detail === 'string' ? json.detail : JSON.stringify(json.detail);
                } catch (e) {
                    // Ignore json parse error
                }
                toast.error(detail);
            }
        } catch (error: any) {
            console.error("Error saving time:", error);
            toast.error(`Erro ao salvar: ${error.message || "Desconhecido"}`);
        }
    };

    const [editingId, setEditingId] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'upcoming' | 'history'>('upcoming');

    // Filter events based on active tab
    const filteredEvents = events.filter(event => {
        const scheduledDate = new Date(event.scheduled_time);
        const now = new Date();
        const isPast = scheduledDate < now;
        // Also consider status: 'pending' is usually upcoming, others are history
        // BUT strict time split is often better for "History".
        // Let's use: 
        // Upcoming = Future OR (Past < 1h AND Pending) -> basically "Active"
        // History = (Past > 1h) OR (Status != Pending)

        if (activeTab === 'upcoming') {
            // Show if it's in the future OR if it's pending and not too old (tolerance)
            // But cleanup_missed_schedules handles the "too old" part on backend.
            // So we can simpler: Status == 'pending' AND (Time > now - 1h)
            // Or just check if status is pending.
            return event.status === 'pending' || event.status === 'paused_login_required'; // [SYN-UX] Show paused items in pending
        } else {
            // History: Completed, Failed, or Expired
            return event.status !== 'pending' && event.status !== 'paused_login_required';
        }
    });

    // Sort logic: Upcoming = Ascending (Next first), History = Descending (Recent first)
    const displayEvents = [...filteredEvents].sort((a, b) => {
        const timeA = new Date(a.scheduled_time).getTime();
        const timeB = new Date(b.scheduled_time).getTime();
        return activeTab === 'upcoming' ? timeA - timeB : timeB - timeA;
    });

    // [SYN-UX] Open Repair Modal for Specific Event
    const handleReconnect = (profileId: string) => {
        const p = profiles.find(pr => pr.id === profileId);
        if (p) {
            setRepairProfile(p);
        } else {
            toast.error("Perfil não encontrado localmente");
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
                            <Dialog.Panel className="w-full max-w-5xl transform overflow-hidden rounded-2xl bg-[#09090b] border border-white/10 p-0 text-left align-middle shadow-2xl transition-all">
                                <div className="flex justify-between items-center p-6 border-b border-white/5 bg-gradient-to-r from-synapse-purple/5 to-transparent">
                                    <div>
                                        <Dialog.Title as="h3" className="text-xl font-bold text-white flex items-center gap-3">
                                            <CalendarIcon className="w-6 h-6 text-synapse-purple" />
                                            Fila de Agendamentos
                                        </Dialog.Title>
                                        <p className="text-sm text-gray-500 mt-1">Gerenciamento inteligente da Grade de Conteúdo.</p>
                                    </div>
                                    <button
                                        onClick={onClose}
                                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                                    >
                                        <XMarkIcon className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Tabs */}
                                <div className="flex border-b border-white/5 px-6">
                                    <button
                                        onClick={() => setActiveTab('upcoming')}
                                        className={clsx(
                                            "px-6 py-3 text-sm font-medium border-b-2 transition-colors",
                                            activeTab === 'upcoming'
                                                ? "border-synapse-purple text-synapse-purple"
                                                : "border-transparent text-gray-400 hover:text-white"
                                        )}
                                    >
                                        Próximos Posts
                                        <span className={clsx("ml-2 px-2 py-0.5 rounded-full text-xs", activeTab === 'upcoming' ? "bg-synapse-purple/20" : "bg-white/5")}>
                                            {events.filter(e => e.status === 'pending' || e.status === 'paused_login_required').length}
                                        </span>
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('history')}
                                        className={clsx(
                                            "px-6 py-3 text-sm font-medium border-b-2 transition-colors",
                                            activeTab === 'history'
                                                ? "border-synapse-purple text-synapse-purple"
                                                : "border-transparent text-gray-400 hover:text-white"
                                        )}
                                    >
                                        Histórico
                                    </button>
                                </div>

                                {/* Content */}
                                <div className="h-[550px] overflow-y-auto custom-scrollbar p-6 space-y-6 bg-[#0c0c0e] scroll-smooth">
                                    {loading ? (
                                        <div className="flex items-center justify-center h-full text-gray-500">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-synapse-purple mr-3"></div>
                                            Carregando...
                                        </div>
                                    ) : displayEvents.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-4">
                                            <CalendarIcon className="w-16 h-16 opacity-20" />
                                            <p>{activeTab === 'upcoming' ? "Nenhum post agendado." : "Histórico vazio."}</p>
                                        </div>
                                    ) : (
                                        // [SYN-UX] Date Grouping for High Density
                                        Object.entries(
                                            displayEvents.reduce((groups, event) => {
                                                const dateKey = format(new Date(event.scheduled_time), 'yyyy-MM-dd');
                                                if (!groups[dateKey]) groups[dateKey] = [];
                                                groups[dateKey].push(event);
                                                return groups;
                                            }, {} as Record<string, ScheduleEvent[]>)
                                        )
                                            .sort((a, b) => activeTab === 'upcoming'
                                                ? a[0].localeCompare(b[0])
                                                : b[0].localeCompare(a[0]) // History: Newest dates first
                                            )
                                            .map(([dateKey, groupEvents]) => {
                                                const dateObj = new Date(dateKey + 'T12:00:00'); // Force noon to avoid timezone shift on simple date parse
                                                return (
                                                    <div key={dateKey} className="relative">
                                                        <div className="sticky top-0 z-10 bg-[#0c0c0e]/95 backdrop-blur-sm border-b border-white/5 py-2 mb-3 flex items-center justify-between">
                                                            <h4 className="text-sm font-bold text-gray-400 font-mono flex items-center gap-2">
                                                                <CalendarIcon className="w-4 h-4 text-synapse-purple" />
                                                                {format(new Date(groupEvents[0].scheduled_time), "EEEE, d 'de' MMMM", { locale: ptBR })}
                                                            </h4>
                                                            <span className="text-xs bg-white/5 px-2 py-0.5 rounded text-gray-500 font-mono">
                                                                {groupEvents.length} posts
                                                            </span>
                                                        </div>

                                                        <div className="grid grid-cols-1 gap-3">
                                                            {groupEvents.map((event) => {
                                                                const isEditing = editingId === event.id;
                                                                const isFailed = event.status === 'failed' || event.status === 'error';
                                                                const isPaused = event.status === 'paused_login_required';
                                                                const isDone = event.status === 'completed' || event.status === 'done';
                                                                const isToday = format(new Date(), 'yyyy-MM-dd') === dateKey;

                                                                return (
                                                                    <div
                                                                        key={event.id}
                                                                        className={clsx(
                                                                            "group relative flex items-center gap-4 p-4 rounded-xl border transition-all hover:shadow-lg hover:shadow-black/50 ml-4",
                                                                            isFailed ? "bg-red-500/5 border-red-500/20 hover:bg-red-500/10" :
                                                                                isPaused ? "bg-amber-500/5 border-amber-500/20 hover:bg-amber-500/10" :
                                                                                    isDone ? "bg-green-500/5 border-green-500/20 hover:bg-green-500/10" :
                                                                                        "bg-white/[0.02] border-white/5 hover:bg-white/[0.05] hover:border-synapse-purple/20"
                                                                        )}
                                                                    >
                                                                        {/* Timeline Connector */}
                                                                        <div className="absolute -left-4 top-1/2 -translate-y-1/2 w-4 h-px bg-white/5" />
                                                                        <div className={clsx(
                                                                            "absolute -left-[19px] top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full border-2 transition-colors z-20",
                                                                            isFailed ? "bg-[#0c0c0e] border-red-500" :
                                                                                isPaused ? "bg-[#0c0c0e] border-amber-500 animate-pulse" :
                                                                                    isDone ? "bg-green-500 border-green-500" :
                                                                                        "bg-[#0c0c0e] border-white/10 group-hover:border-synapse-purple"
                                                                        )} />

                                                                        {/* Simulated Thumbnail / File Icon */}
                                                                        <div className="w-16 h-20 bg-black/40 rounded-lg flex items-center justify-center border border-white/5 shrink-0 overflow-hidden relative">
                                                                            <PlayCircleIcon className="w-6 h-6 text-gray-600 group-hover:text-synapse-purple transition-colors z-10" />
                                                                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                                                                        </div>

                                                                        {/* Info */}
                                                                        <div className="flex-1 min-w-0">
                                                                            <div className="flex items-start justify-between">
                                                                                <div>
                                                                                    <div className="flex items-center gap-2 mb-1">
                                                                                        <span className="text-white font-medium truncate max-w-[300px] text-base" title={event.video_path}>
                                                                                            {event.video_path.split('\\').pop()?.split('/').pop()}
                                                                                        </span>
                                                                                        {event.viral_music_enabled && (
                                                                                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-synapse-purple/20 text-synapse-purple border border-synapse-purple/20 uppercase tracking-wider flex items-center gap-1 shadow-[0_0_10px_rgba(139,92,246,0.2)]">
                                                                                                <MusicalNoteIcon className="w-2.5 h-2.5" />
                                                                                                Viral
                                                                                            </span>
                                                                                        )}
                                                                                        {isFailed && (
                                                                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/20 uppercase tracking-wider">
                                                                                                FALHA
                                                                                            </span>
                                                                                        )}
                                                                                        {isPaused && (
                                                                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/20 uppercase tracking-wider flex items-center gap-1">
                                                                                                <ExclamationTriangleIcon className="w-3 h-3" />
                                                                                                SESSÃO EXPIRADA
                                                                                            </span>
                                                                                        )}
                                                                                    </div>
                                                                                    <div className="flex items-center gap-2">
                                                                                        {/* Profile Badge */}
                                                                                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/40 border border-white/5 w-fit">
                                                                                            <div className="w-3.5 h-3.5 rounded-full bg-gray-700 overflow-hidden ring-1 ring-white/10">
                                                                                                {getProfileImage(event.profile_id) ? (
                                                                                                    <img src={getProfileImage(event.profile_id)!} alt="" className="w-full h-full object-cover" />
                                                                                                ) : (
                                                                                                    <div className="w-full h-full bg-gradient-to-br from-gray-600 to-gray-800" />
                                                                                                )}
                                                                                            </div>
                                                                                            <span className="text-[10px] font-bold text-gray-300">
                                                                                                @{getProfileName(event.profile_id)}
                                                                                            </span>
                                                                                        </div>
                                                                                        <span className="text-[10px] text-gray-600">•</span>
                                                                                        <p className="text-[10px] text-gray-500 font-mono truncate max-w-[200px] opacity-60">
                                                                                            {event.video_path}
                                                                                        </p>
                                                                                    </div>

                                                                                    {/* [SYN-UI] Explicit Error Display */}
                                                                                    {(isFailed && (event.error_message || event.metadata?.error)) && (
                                                                                        <div className="mt-1.5 p-1.5 rounded bg-red-950/30 border border-red-500/30 text-[11px] text-red-200 font-mono max-w-[400px]">
                                                                                            <span className="font-bold text-red-400 mr-1">⛔ ERRO:</span>
                                                                                            {event.error_message || event.metadata?.error}
                                                                                        </div>
                                                                                    )}

                                                                                    {/* [SYN-UX] Reconnect Button for Paused Items */}
                                                                                    {isPaused && (
                                                                                        <div className="mt-2 flex items-center gap-2">
                                                                                            <button
                                                                                                onClick={() => handleReconnect(event.profile_id)}
                                                                                                className="px-3 py-1.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold hover:bg-amber-500/30 transition-all flex items-center gap-1.5 shadow-[0_0_15px_rgba(245,158,11,0.1)]"
                                                                                            >
                                                                                                <ExclamationTriangleIcon className="w-3.5 h-3.5" />
                                                                                                Reconectar Perfil
                                                                                            </button>
                                                                                            <span className="text-[10px] text-gray-500">Faça login novamente para retomar.</span>
                                                                                        </div>
                                                                                    )}
                                                                                </div>

                                                                                {isEditing ? (
                                                                                    <div className="flex items-center gap-2">
                                                                                        <input
                                                                                            type="datetime-local"
                                                                                            defaultValue={format(new Date(event.scheduled_time), "yyyy-MM-dd'T'HH:mm")}
                                                                                            className="bg-black/50 border border-synapse-purple rounded-lg px-2 py-1 text-white text-xs outline-none focus:ring-2 ring-synapse-purple/50 w-40"
                                                                                            onKeyDown={(e) => {
                                                                                                if (e.key === 'Enter') handleEditTime(event.id, e.currentTarget.value);
                                                                                            }}
                                                                                        />
                                                                                        <button
                                                                                            onClick={(e) => {
                                                                                                const input = (e.currentTarget.previousElementSibling as HTMLInputElement);
                                                                                                handleEditTime(event.id, input.value);
                                                                                            }}
                                                                                            className="px-2 py-1 bg-synapse-purple/20 hover:bg-synapse-purple/30 text-synapse-purple rounded text-xs"
                                                                                        >
                                                                                            Salvar
                                                                                        </button>
                                                                                        <button onClick={() => setEditingId(null)} className="text-xs text-red-400 hover:text-red-300">Cancelar</button>
                                                                                    </div>
                                                                                ) : (
                                                                                    <div
                                                                                        className={clsx(
                                                                                            "text-right group/time",
                                                                                            activeTab === 'upcoming' ? "cursor-pointer" : "cursor-default opacity-80"
                                                                                        )}
                                                                                        onClick={() => activeTab === 'upcoming' && setEditingId(event.id)}
                                                                                        title={activeTab === 'upcoming' ? "Clique para editar" : ""}
                                                                                    >
                                                                                        <div className={clsx("text-xl font-bold font-mono tracking-tight transition-colors",
                                                                                            isFailed ? "text-red-400" : isPaused ? "text-amber-400" : "text-white group-hover/time:text-synapse-purple")}>
                                                                                            {format(new Date(event.scheduled_time), 'HH:mm')}
                                                                                        </div>
                                                                                    </div>
                                                                                )}
                                                                            </div>

                                                                            <div className="mt-3 flex items-center justify-end">
                                                                                {/* Actions */}
                                                                                <button
                                                                                    onClick={() => handleDelete(event.id)}
                                                                                    className={clsx(
                                                                                        "p-1.5 rounded-lg transition-colors opacity-0 group-hover:opacity-100 flex items-center gap-2",
                                                                                        deletingConfirmationId === event.id
                                                                                            ? "bg-red-500 text-white hover:bg-red-600"
                                                                                            : "text-gray-600 hover:text-red-500 hover:bg-red-500/10"
                                                                                    )}
                                                                                    title={deletingConfirmationId === event.id ? "Clique para confirmar" : "Remover"}
                                                                                >
                                                                                    {deletingConfirmationId === event.id ? (
                                                                                        <span className="text-[10px] font-bold pr-1">Confirmar?</span>
                                                                                    ) : (
                                                                                        <TrashIcon className="w-4 h-4" />
                                                                                    )}
                                                                                </button>
                                                                            </div>

                                                                            {/* Progress bar simulation / Status line */}
                                                                            <div className={clsx("absolute bottom-0 left-0 h-[2px] w-full transition-opacity rounded-b-xl overflow-hidden",
                                                                                isFailed ? "bg-red-500 opacity-50" :
                                                                                    isPaused ? "bg-amber-500 opacity-50" :
                                                                                        "bg-gradient-to-r from-synapse-purple to-transparent opacity-0 group-hover:opacity-50")} />
                                                                        </div>
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    </div>
                                                );
                                            })
                                    )}
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>

                {/* [SYN-UX] New Repair Modal */}
                <ProfileRepairModal
                    isOpen={!!repairProfile}
                    onClose={() => setRepairProfile(null)}
                    profile={repairProfile}
                    onSuccess={() => {
                        fetchEvents(); // Refresh list to see if statuses update (backend might need polling but good for now)
                        if (onUpdate) onUpdate();
                    }}
                />
            </Dialog>
        </Transition >
    );
}
