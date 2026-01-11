'use client';

import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { TikTokProfile } from '../types';
import { NeonButton } from './NeonButton';
import { XMarkIcon, CalendarDaysIcon, ClockIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format } from 'date-fns';

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

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const dateTime = new Date(`${selectedDate}T${selectedTime}`);
        onSubmit({
            scheduled_time: dateTime.toISOString(),
            profile_ids: selectedProfiles,
            viral_music_enabled: viralBoost
        });
        onClose();
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

                                <form onSubmit={handleSubmit} className="space-y-6">
                                    {/* Date & Time */}
                                    <div className="grid grid-cols-2 gap-4">
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
                                            <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Horário</label>
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

                                    {/* Viral Boost Toggle (Syncs with page) */}
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
