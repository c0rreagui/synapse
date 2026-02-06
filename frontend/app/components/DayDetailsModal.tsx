'use client';

import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { ScheduleEvent, TikTokProfile } from '../types';
import { NeonButton } from './NeonButton';
import { XMarkIcon, ClockIcon, TrashIcon, CalendarIcon, PlusIcon, MusicalNoteIcon, PencilSquareIcon, CheckIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import clsx from 'clsx';
import { toast } from 'sonner';

interface DayDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    date: Date;
    events: ScheduleEvent[];
    profiles: TikTokProfile[];
    onDeleteEvent: (eventId: string) => void;
    onEditEvent: (eventId: string, newTime: string) => void;
    onAddEvent: () => void;
}

export default function DayDetailsModal({
    isOpen,
    onClose,
    date,
    events,
    profiles,
    onDeleteEvent,
    onEditEvent,
    onAddEvent
}: DayDetailsModalProps) {

    // Sort events by time
    const sortedEvents = [...events].sort((a, b) =>
        new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime()
    );

    const getProfileLabel = (id: string) => {
        const p = profiles.find(pr => pr.id === id);
        return p ? p.label : id;
    };

    // [SYN-UX] Profile Color Mapping (Robust Hash - Consistent with Scheduler)
    const getProfileColor = (pid: string) => {
        const colors = [
            'bg-cyan-400',    // Vibe
            'bg-rose-400',    // Opiniao
            'bg-emerald-400', // Green
            'bg-amber-400',   // Yellow
            'bg-violet-400',  // Purple
            'bg-fuchsia-400'  // Pink
        ];
        let hash = 0;
        for (let i = 0; i < pid.length; i++) {
            hash = pid.charCodeAt(i) + ((hash << 5) - hash);
        }
        return colors[Math.abs(hash) % colors.length];
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
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-md" />
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
                            <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-[#0f0a15] border border-white/10 p-0 text-left shadow-[0_0_50px_rgba(139,92,246,0.15)] transition-all">

                                {/* Header (Cyberpunk Style) */}
                                <div className="relative p-6 border-b border-white/5 bg-gradient-to-r from-synapse-purple/10 to-transparent">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-2xl font-bold text-white flex items-center gap-3 capitalize tracking-wide">
                                                <CalendarIcon className="w-7 h-7 text-synapse-purple" />
                                                {format(date, "EEEE, d", { locale: ptBR })}
                                            </h3>
                                            <div className="flex items-center gap-2 mt-1 px-1">
                                                <span className="text-xs font-mono text-synapse-purple uppercase tracking-wider">
                                                    {format(date, "MMMM yyyy", { locale: ptBR })}
                                                </span>
                                                <span className="text-xs text-gray-600">•</span>
                                                <span className="text-xs text-gray-400 font-mono">
                                                    {events.length} Eventos Agendados
                                                </span>
                                            </div>
                                        </div>
                                        <button onClick={onClose} className="p-2 -mr-2 -mt-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors">
                                            <XMarkIcon className="w-6 h-6" />
                                        </button>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto custom-scrollbar">
                                    {sortedEvents.length === 0 ? (
                                        <div className="py-12 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-white/5 rounded-2xl bg-white/[0.02]">
                                            <ClockIcon className="w-12 h-12 mb-3 opacity-30" />
                                            <p className="text-sm font-medium text-gray-400">Dia livre. Nenhum agendamento.</p>
                                            <p className="text-xs text-gray-600 mt-1">Comece adicionando vídeos à fila.</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            {sortedEvents.map((event) => (
                                                <EventRow
                                                    key={event.id}
                                                    event={event}
                                                    profileLabel={getProfileLabel(event.profile_id)}
                                                    profileColor={getProfileColor(event.profile_id)} // [SYN-UX] Consistent Color
                                                    onEdit={onEditEvent}
                                                    onDelete={onDeleteEvent}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Footer Actions */}
                                <div className="p-6 border-t border-white/5 bg-white/[0.02]">
                                    <NeonButton
                                        variant="primary"
                                        className="w-full flex items-center justify-center gap-2 py-3"
                                        onClick={onAddEvent}
                                    >
                                        <PlusIcon className="w-5 h-5" />
                                        Agendar Novo Vídeo
                                    </NeonButton>
                                </div>

                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}

// Sub-component for individual Event Row logic
function EventRow({ event, profileLabel, profileColor, onEdit, onDelete }: {
    event: ScheduleEvent,
    profileLabel: string,
    profileColor: string,
    onEdit: (id: string, time: string) => void,
    onDelete: (id: string) => void
}) {
    const [isEditing, setIsEditing] = useState(false);
    const [editTime, setEditTime] = useState(format(new Date(event.scheduled_time), 'HH:mm'));

    useEffect(() => {
        setEditTime(format(new Date(event.scheduled_time), 'HH:mm'));
    }, [event.scheduled_time]);

    const [deletingId, setDeletingId] = useState<string | null>(null);

    const handleDeleteClick = () => {
        if (deletingId === event.id) {
            onDelete(event.id);
            setDeletingId(null);
        } else {
            setDeletingId(event.id);
            setTimeout(() => setDeletingId(curr => curr === event.id ? null : curr), 3000);
        }
    };

    const handleSave = () => {
        onEdit(event.id, editTime);
        setIsEditing(false);
    };

    return (
        <div
            className="group relative flex items-center gap-4 p-4 rounded-xl bg-[#13111a] border border-white/5 hover:border-synapse-purple/30 transition-all shadow-sm hover:shadow-lg hover:shadow-synapse-purple/5 overflow-hidden"
        >
            {/* [SYN-UX] Profile Color Indicator Bar */}
            <div className={clsx("absolute left-0 top-0 bottom-0 w-1", profileColor)} />
            {/* Time Badge */}
            {isEditing ? (
                <div className="flex items-center gap-2">
                    <input
                        type="time"
                        value={editTime}
                        onChange={(e) => setEditTime(e.target.value)}
                        className="bg-black/50 border border-synapse-purple rounded px-2 py-1 text-sm text-white outline-none w-24"
                        autoFocus
                    />
                    <button onClick={handleSave} className="p-1 text-green-400 hover:bg-green-400/10 rounded">
                        <CheckIcon className="w-4 h-4" />
                    </button>
                    <button onClick={() => setIsEditing(false)} className="p-1 text-red-400 hover:bg-red-400/10 rounded">
                        <XMarkIcon className="w-4 h-4" />
                    </button>
                </div>
            ) : (
                <div className="flex flex-col items-center justify-center w-14 h-14 rounded-lg bg-black/40 border border-white/10 font-mono group-hover:border-synapse-purple/40 transition-colors">
                    <span className="text-lg font-bold text-white">{format(new Date(event.scheduled_time), 'HH')}</span>
                    <span className="text-[10px] text-gray-500">{format(new Date(event.scheduled_time), 'mm')}</span>
                </div>
            )}

            {/* Details */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-bold text-white truncate text-shadow-sm">{profileLabel}</p>
                    {event.viral_music_enabled && (
                        <div className="px-1.5 py-0.5 rounded-full bg-synapse-purple/20 border border-synapse-purple/30 flex items-center gap-1">
                            <MusicalNoteIcon className="w-3 h-3 text-synapse-purple" />
                            <span className="text-[9px] text-synapse-purple font-bold">VIRAL BOOST</span>
                        </div>
                    )}
                </div>
                <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span className={clsx(
                            "w-2 h-2 rounded-full",
                            event.status === 'posted' || event.status === 'completed' || event.status === 'ready' ? "bg-green-500 shadow-[0_0_5px_#22c55e]" :
                                (event.status === 'failed' ? "bg-red-500 shadow-[0_0_5px_#ef4444]" :
                                    (event.status === 'paused_login_required' ? "bg-orange-500 animate-pulse shadow-[0_0_5px_#f97316]" : "bg-yellow-500 shadow-[0_0_5px_#eab308]"))
                        )} />
                        <span className="uppercase tracking-wider font-mono text-[10px]">
                            {event.status === 'paused_login_required' ? 'SESSÃO EXPIRADA' : (event.status || 'AGENDADO')}
                        </span>
                    </div>
                    {event.status === 'paused_login_required' && (
                        <div className="mt-1 p-2 rounded bg-orange-500/10 border border-orange-500/20 text-[10px] text-orange-300 font-mono">
                            <span className="font-bold block mb-0.5 text-orange-400">🚨 ACESSO NEGADO:</span>
                            A postagem foi pausada porque o login expirou.
                            <a href="/profiles" className="block mt-1 text-white underline decoration-orange-500/50 hover:text-orange-200 transition-colors">
                                Sincronizar Perfil no Menu Perfis →
                            </a>
                        </div>
                    )}
                    {(event.status === 'failed' && (event.error_message || event.metadata?.error)) && (
                        <div className="mt-1 p-2 rounded bg-red-500/10 border border-red-500/20 text-[10px] text-red-300 font-mono break-all relative group/error cursor-help">
                            <span className="font-bold block mb-0.5 text-red-400">⚠️ FALHA NO PROCESSO:</span>
                            {event.error_message || event.metadata.error}

                            {/* Generic Hint */}
                            <div className="absolute left-0 bottom-full mb-2 w-48 p-2 bg-black/90 border border-white/10 rounded text-xs text-gray-400 opacity-0 group-hover/error:opacity-100 transition-opacity pointer-events-none z-50">
                                O sistema tentou processar mas encontrou um erro irrecuperável. Verifique os logs se persistir.
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Actions */}
            {!isEditing && (
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity translate-x-2 group-hover:translate-x-0">
                    <button
                        onClick={() => setIsEditing(true)}
                        className="p-2 rounded-lg text-gray-500 hover:text-white hover:bg-white/10 transition-colors"
                        title="Editar Horário"
                    >
                        <PencilSquareIcon className="w-4 h-4" />
                    </button>
                    <button
                        onClick={handleDeleteClick}
                        className={clsx(
                            "p-2 rounded-lg transition-all flex items-center gap-1",
                            deletingId === event.id
                                ? "bg-red-500 text-white w-auto px-3"
                                : "text-gray-500 hover:text-red-400 hover:bg-red-500/10"
                        )}
                        title="Remover agendamento"
                    >
                        {deletingId === event.id ? (
                            <span className="text-[10px] font-bold whitespace-nowrap">Confirmar?</span>
                        ) : (
                            <TrashIcon className="w-4 h-4" />
                        )}
                    </button>
                </div>
            )}
        </div>
    );
}
