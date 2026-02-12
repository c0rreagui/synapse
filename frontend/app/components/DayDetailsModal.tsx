'use client';

import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition, Menu } from '@headlessui/react';
import { ScheduleEvent, TikTokProfile } from '../types';
import { NeonButton } from './NeonButton';
import { XMarkIcon, ClockIcon, TrashIcon, CalendarIcon, PlusIcon, MusicalNoteIcon, PencilSquareIcon, CheckIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import clsx from 'clsx';
import { toast } from 'sonner';
import EditScheduleModal, { EditScheduleData } from './EditScheduleModal';

interface DayDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    date: Date;
    events: ScheduleEvent[];
    profiles: TikTokProfile[];
    onDeleteEvent: (eventId: string) => void;
    onEditEvent: (eventId: string, newTime: string) => void;
    onAddEvent: () => void;
    onRetryEvent: (eventId: string, mode: 'now' | 'next_slot') => void;
    onFullEdit?: (eventId: string, data: EditScheduleData) => Promise<void>;
}

export default function DayDetailsModal({
    isOpen,
    onClose,
    date,
    events,
    profiles,
    onDeleteEvent,
    onEditEvent,
    onAddEvent,
    onRetryEvent,
    onFullEdit
}: DayDetailsModalProps) {

    // [SYN-EDIT] Full Edit Modal State
    const [editingEvent, setEditingEvent] = useState<ScheduleEvent | null>(null);

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
                                                    profileColor={getProfileColor(event.profile_id)}
                                                    onEdit={onEditEvent}
                                                    onDelete={onDeleteEvent}
                                                    onRetry={onRetryEvent}
                                                    onFullEdit={onFullEdit ? () => setEditingEvent(event) : undefined}
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

                {/* [SYN-EDIT] Full Edit Modal */}
                {onFullEdit && (
                    <EditScheduleModal
                        isOpen={editingEvent !== null}
                        onClose={() => setEditingEvent(null)}
                        event={editingEvent}
                        profiles={profiles}
                        onSave={async (eventId, data) => {
                            await onFullEdit(eventId, data);
                            setEditingEvent(null);
                        }}
                    />
                )}
            </Dialog>
        </Transition>
    );
}

// Sub-component for individual Event Row logic
function EventRow({ event, profileLabel, profileColor, onEdit, onDelete, onRetry, onFullEdit }: {
    event: ScheduleEvent,
    profileLabel: string,
    profileColor: string,
    onEdit: (id: string, time: string) => void,
    onDelete: (id: string) => void,
    onRetry: (id: string, mode: 'now' | 'next_slot') => void,
    onFullEdit?: () => void
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
            className={clsx(
                "group relative flex items-center gap-4 p-4 rounded-xl border transition-all shadow-sm hover:shadow-lg", // [SYN-FIX] Removed overflow-hidden for Popover
                (event.status === 'completed' || event.status === 'posted')
                    ? "bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40 hover:shadow-emerald-500/10"
                    : event.status === 'failed'
                        ? "bg-red-500/5 border-red-500/20 hover:border-red-500/40 hover:shadow-red-500/10"
                        : "bg-[#13111a] border-white/5 hover:border-synapse-purple/30 hover:shadow-synapse-purple/5"
            )}
        >
            {/* [SYN-UX] Profile Color Indicator Bar (Rounded to match container since overflow is visible) */}
            <div className={clsx("absolute left-0 top-0 bottom-0 w-1 rounded-l-xl", profileColor)} />
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
                            {event.status === 'paused_login_required'
                                ? 'SESSÃO EXPIRADA'
                                : ((event.status === 'completed' || event.status === 'posted') ? 'POSTADO' : (event.status || 'AGENDADO'))}
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
                            <div className="absolute left-0 bottom-full mb-2 w-48 p-2 bg-black/90 border border-white/10 rounded text-xs text-gray-400 opacity-0 group-hover/error:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                                O sistema tentou processar mas encontrou um erro irrecuperável. Verifique os logs se persistir.
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Actions */}
            {!isEditing && (
                <div className={clsx(
                    "flex gap-1 transition-all duration-300 relative",
                    // [SYN-UX] Show actions if failed/paused OR hover
                    (event.status === 'failed' || event.status === 'paused_login_required')
                        ? "opacity-100 translate-x-0"
                        : "opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0"
                )}>
                    {/* [SYN-73] Retry Button (Headless UI Menu with Portal via anchor) */}
                    {(event.status === 'failed' || event.status === 'paused_login_required') && (
                        <Menu as="div" className="relative">
                            {({ open }) => (
                                <>
                                    <Menu.Button
                                        className={clsx(
                                            "p-2 rounded-lg transition-all border border-transparent flex items-center justify-center",
                                            "bg-synapse-purple/10 text-synapse-purple border-synapse-purple/20 hover:bg-synapse-purple/20 shadow-[0_0_15px_rgba(139,92,246,0.1)]",
                                            open && "ring-2 ring-synapse-purple/50 bg-synapse-purple/25 shadow-[0_0_20px_rgba(139,92,246,0.2)]"
                                        )}
                                        title="Opções de Recuperação"
                                    >
                                        <ArrowPathIcon className={clsx("w-4 h-4 transition-transform duration-500", !open && "animate-pulse", open && "rotate-180")} />
                                    </Menu.Button>

                                    <Transition
                                        as={Fragment}
                                        enter="transition ease-out duration-100"
                                        enterFrom="transform opacity-0 scale-95"
                                        enterTo="transform opacity-100 scale-100"
                                        leave="transition ease-in duration-75"
                                        leaveFrom="transform opacity-100 scale-100"
                                        leaveTo="transform opacity-0 scale-95"
                                    >
                                        <Menu.Items
                                            anchor="bottom end"
                                            className="w-56 bg-[#0c0a10] border border-synapse-purple/40 rounded-xl shadow-[0_20px_50px_rgba(0,0,0,1)] z-[9999] focus:outline-none overflow-hidden ring-1 ring-white/10 [--anchor-gap:8px]"
                                        >
                                            <div className="p-1.5 space-y-1">
                                                <div className="px-3 py-2 text-[10px] font-bold text-synapse-purple uppercase tracking-[0.2em] border-b border-white/5 mb-1.5 flex items-center justify-between">
                                                    <span>RECUPERAÇÃO</span>
                                                    <div className="w-1 h-1 rounded-full bg-synapse-purple animate-pulse" />
                                                </div>

                                                <Menu.Item>
                                                    {({ active }) => (
                                                        <button
                                                            onClick={() => onRetry(event.id, 'now')}
                                                            className={clsx(
                                                                "w-full text-left px-3 py-3 rounded-lg transition-all flex items-center gap-3 group/btn",
                                                                active ? "bg-white/5 text-white" : "text-gray-300"
                                                            )}
                                                        >
                                                            <div className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-[0_0_10px_#ef4444]" />
                                                            <div className="flex flex-col">
                                                                <span className="font-bold text-xs">Repostar Agora</span>
                                                                <span className="text-[9px] text-gray-500 group-hover/btn:text-gray-400">Tenta enviar imediatamente</span>
                                                            </div>
                                                        </button>
                                                    )}
                                                </Menu.Item>

                                                <Menu.Item>
                                                    {({ active }) => (
                                                        <button
                                                            onClick={() => onRetry(event.id, 'next_slot')}
                                                            className={clsx(
                                                                "w-full text-left px-3 py-3 rounded-lg transition-all flex items-center gap-3 group/btn",
                                                                active ? "bg-white/5 text-white" : "text-gray-300"
                                                            )}
                                                        >
                                                            <div className="w-2.5 h-2.5 rounded-full bg-blue-400 shadow-[0_0_10px_#3b82f6]" />
                                                            <div className="flex flex-col">
                                                                <span className="font-bold text-xs">Reagendar Vídeo</span>
                                                                <span className="text-[9px] text-gray-500 group-hover/btn:text-gray-400">Próximo horário disponível</span>
                                                            </div>
                                                        </button>
                                                    )}
                                                </Menu.Item>
                                            </div>
                                            <div className="bg-synapse-purple/10 p-2 text-[9px] text-gray-500 font-mono text-center border-t border-white/5 italic">
                                                Restaura arquivo original automaticamente
                                            </div>
                                        </Menu.Items>
                                    </Transition>
                                </>
                            )}
                        </Menu>
                    )}

                    {/* Edit/Delete Buttons (Standard) */}
                    <button
                        onClick={() => onFullEdit ? onFullEdit() : setIsEditing(true)}
                        className="p-2 rounded-lg text-gray-500 hover:text-white hover:bg-white/10 transition-colors"
                        title={onFullEdit ? 'Editar Agendamento' : 'Editar Horario'}
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
