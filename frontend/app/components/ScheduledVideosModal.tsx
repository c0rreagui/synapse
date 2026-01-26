import React, { useEffect, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, CalendarIcon, MusicalNoteIcon, PlayCircleIcon, TrashIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { ScheduleEvent, TikTokProfile } from '../types';

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

    const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

    const fetchEvents = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/v1/scheduler/list`);

            if (res.ok) {
                const data = await res.json();
                const sorted = data.sort((a: any, b: any) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime());
                setEvents(sorted);
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
        }
    }, [isOpen]);

    const handleDelete = async (id: string) => {
        if (!confirm("Tem certeza que deseja cancelar este agendamento?")) return;

        try {
            const res = await fetch(`${API_URL}/api/v1/scheduler/${id}`, { method: 'DELETE' });
            if (res.ok) {
                setEvents(prev => prev.filter(e => e.id !== id));
                toast.success("Agendamento cancelado");
                if (onDelete) onDelete(id);
                if (onUpdate) onUpdate(); // Trigger parent refresh
            } else {
                toast.error("Erro ao cancelar");
            }
        } catch (e) {
            toast.error("Erro ao conectar");
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
                setEvents(prev => prev.map(e => e.id === id ? { ...e, scheduled_time: date.toISOString() } : e));
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
                                            <span className="px-2 py-0.5 rounded-full bg-white/10 text-xs font-mono">{events.length}</span>
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

                                {/* Content */}
                                <div className="h-[600px] overflow-y-auto custom-scrollbar p-6 space-y-3 bg-[#0c0c0e]">
                                    {loading ? (
                                        <div className="flex items-center justify-center h-full text-gray-500">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-synapse-purple mr-3"></div>
                                            Carregando...
                                        </div>
                                    ) : events.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-4">
                                            <CalendarIcon className="w-16 h-16 opacity-20" />
                                            <p>Nenhum vídeo agendado.</p>
                                        </div>
                                    ) : (
                                        events.map((event) => {
                                            const isEditing = editingId === event.id;
                                            return (
                                                <div
                                                    key={event.id}
                                                    className="group relative flex items-center gap-4 p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.05] hover:border-synapse-purple/20 transition-all hover:shadow-lg hover:shadow-black/50"
                                                >
                                                    {/* Simulated Thumbnail / File Icon */}
                                                    <div className="w-20 h-28 bg-black/40 rounded-lg flex items-center justify-center border border-white/5 shrink-0 overflow-hidden relative">
                                                        <PlayCircleIcon className="w-8 h-8 text-gray-600 group-hover:text-synapse-purple transition-colors z-10" />
                                                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                                                    </div>

                                                    {/* Info */}
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-start justify-between">
                                                            <div>
                                                                <div className="flex items-center gap-2 mb-1">
                                                                    <span className="text-white font-medium truncate max-w-[300px] text-lg" title={event.video_path}>
                                                                        {event.video_path.split('\\').pop()?.split('/').pop()}
                                                                    </span>
                                                                    {event.viral_music_enabled && (
                                                                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-synapse-purple/20 text-synapse-purple border border-synapse-purple/20 uppercase tracking-wider flex items-center gap-1 shadow-[0_0_10px_rgba(139,92,246,0.2)]">
                                                                            <MusicalNoteIcon className="w-3 h-3" />
                                                                            Viral Boost
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                <p className="text-xs text-gray-500 font-mono truncate max-w-[400px] opacity-60">
                                                                    {event.video_path}
                                                                </p>
                                                            </div>

                                                            {isEditing ? (
                                                                <div className="flex items-center gap-2">
                                                                    <input
                                                                        type="datetime-local"
                                                                        // [FIX] Convert UTC ISO to Local time string for input
                                                                        defaultValue={format(new Date(event.scheduled_time), "yyyy-MM-dd'T'HH:mm")}
                                                                        className="bg-black/50 border border-synapse-purple rounded-lg px-3 py-1 text-white text-sm outline-none focus:ring-2 ring-synapse-purple/50"
                                                                        onKeyDown={(e) => {
                                                                            if (e.key === 'Enter') handleEditTime(event.id, e.currentTarget.value);
                                                                        }}
                                                                    />
                                                                    <button
                                                                        onClick={(e) => {
                                                                            // Trigger save on button click too, getting value from sibling input
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
                                                                    className="text-right cursor-pointer group/time"
                                                                    onClick={() => setEditingId(event.id)}
                                                                    title="Clique para editar"
                                                                >
                                                                    <div className="text-2xl font-bold text-white font-mono tracking-tight group-hover/time:text-synapse-purple transition-colors">
                                                                        {format(new Date(event.scheduled_time), 'HH:mm')}
                                                                    </div>
                                                                    <div className="text-xs text-gray-500 uppercase font-bold tracking-wider group-hover/time:text-gray-300">
                                                                        {format(new Date(event.scheduled_time), 'dd MMM yyyy', { locale: ptBR })}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>

                                                        <div className="mt-4 flex items-center justify-between">
                                                            {/* Profile info */}
                                                            <div className="flex items-center gap-3 p-1.5 pr-4 rounded-full bg-black/40 border border-white/5 w-fit hover:border-white/10 transition-colors">
                                                                <div className="w-6 h-6 rounded-full bg-gray-700 overflow-hidden ring-1 ring-white/10">
                                                                    {getProfileImage(event.profile_id) ? (
                                                                        <img src={getProfileImage(event.profile_id)!} alt="" className="w-full h-full object-cover" />
                                                                    ) : (
                                                                        <div className="w-full h-full bg-gradient-to-br from-gray-600 to-gray-800" />
                                                                    )}
                                                                </div>
                                                                <span className="text-xs font-bold text-gray-300">
                                                                    @{getProfileName(event.profile_id)}
                                                                </span>
                                                            </div>

                                                            {/* Actions */}
                                                            <button
                                                                onClick={() => handleDelete(event.id)}
                                                                className="p-2 text-gray-600 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                                                title="Cancelar Agendamento"
                                                            >
                                                                <TrashIcon className="w-5 h-5" />
                                                            </button>
                                                        </div>

                                                        {/* Progress bar simulation / Status line */}
                                                        <div className="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-synapse-purple to-transparent w-full opacity-0 group-hover:opacity-50 transition-opacity" />
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
            </Dialog>
        </Transition>
    );
}
