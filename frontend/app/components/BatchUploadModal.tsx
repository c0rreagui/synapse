'use client';

import { Fragment, useState, useEffect, useRef } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { TikTokProfile } from '../types';
import { NeonButton } from './NeonButton';
import { XMarkIcon, CalendarDaysIcon, ClockIcon, UserGroupIcon, CloudArrowUpIcon, DocumentIcon, TrashIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format } from 'date-fns';

interface BatchUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    profiles: TikTokProfile[];
}

export default function BatchUploadModal({
    isOpen,
    onClose,
    onSuccess,
    profiles
}: BatchUploadModalProps) {
    // Files State
    const [files, setFiles] = useState<File[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Config State
    const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
    const [strategy, setStrategy] = useState<'INTERVAL' | 'ORACLE'>('INTERVAL');
    const [intervalMinutes, setIntervalMinutes] = useState(60);
    const [startDate, setStartDate] = useState(format(new Date(), 'yyyy-MM-dd'));
    const [startTime, setStartTime] = useState('10:00');
    const [viralBoost, setViralBoost] = useState(false);

    const toggleProfile = (id: string) => {
        setSelectedProfiles(prev =>
            prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
        );
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFiles(prev => [...prev, ...Array.from(e.target.files!)]);
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Mock file paths for now as we don't have real upload yet
        // In real impl, we would upload files first or send paths if local
        const filePaths = files.map(f => `C:\\Videos\\${f.name}`);

        try {
            const startDateTime = new Date(`${startDate}T${startTime}`);

            const payload = {
                files: filePaths,
                profile_ids: selectedProfiles,
                strategy: strategy,
                start_time: startDateTime.toISOString(),
                interval_minutes: intervalMinutes,
                viral_music_enabled: viralBoost
            };

            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_URL}/api/v1/scheduler/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Batch scheduling failed");

            onSuccess();
            onClose();
            // Reset state
            setFiles([]);
            setSelectedProfiles([]);
        } catch (error) {
            console.error("Batch error", error);
            alert("Failed to schedule batch. Check console.");
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
                            <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-[#0f0a15] border border-white/10 p-6 text-left align-middle shadow-xl transition-all">
                                <Dialog.Title
                                    as="h3"
                                    className="text-lg font-bold text-white flex justify-between items-center mb-6"
                                >
                                    <div className="flex items-center gap-2">
                                        <CloudArrowUpIcon className="w-6 h-6 text-synapse-purple" />
                                        <span>Batch Upload & Schedule</span>
                                    </div>
                                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                                        <XMarkIcon className="w-5 h-5" />
                                    </button>
                                </Dialog.Title>

                                <form onSubmit={handleSubmit} className="space-y-8">

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                                        {/* LEFT COLUMN: FILES & PROFILES */}
                                        <div className="space-y-6">
                                            {/* File Upload */}
                                            <div className="space-y-2">
                                                <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Vídeos ({files.length})</label>

                                                <div
                                                    onClick={() => fileInputRef.current?.click()}
                                                    className="border-2 border-dashed border-gray-700 hover:border-synapse-purple/50 bg-white/5 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-colors"
                                                >
                                                    <CloudArrowUpIcon className="w-8 h-8 text-gray-500 mb-2" />
                                                    <p className="text-sm text-gray-300">Clique para adicionar vídeos</p>
                                                    <p className="text-xs text-gray-600">Simulação: Apenas nomes são usados</p>
                                                    <input
                                                        ref={fileInputRef}
                                                        type="file"
                                                        multiple
                                                        accept="video/*"
                                                        className="hidden"
                                                        onChange={handleFileChange}
                                                    />
                                                </div>

                                                {/* File List */}
                                                {files.length > 0 && (
                                                    <div className="max-h-40 overflow-y-auto space-y-2 custom-scrollbar pr-2 mt-2">
                                                        {files.map((file, idx) => (
                                                            <div key={idx} className="flex justify-between items-center bg-white/5 px-3 py-2 rounded text-xs text-gray-300 border border-white/5">
                                                                <div className="flex items-center gap-2 truncate">
                                                                    <DocumentIcon className="w-4 h-4 text-synapse-purple opacity-70" />
                                                                    <span className="truncate">{file.name}</span>
                                                                </div>
                                                                <button type="button" onClick={() => removeFile(idx)} className="text-gray-500 hover:text-red-400">
                                                                    <TrashIcon className="w-4 h-4" />
                                                                </button>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            {/* Profiles */}
                                            <div className="space-y-2">
                                                <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block flex items-center gap-2">
                                                    <UserGroupIcon className="w-3 h-3" />
                                                    Destino
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
                                        </div>

                                        {/* RIGHT COLUMN: CONFIGURATION */}
                                        <div className="space-y-6">

                                            {/* Strategy Selector */}
                                            <div className="space-y-2">
                                                <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Estratégia</label>
                                                <div className="grid grid-cols-2 gap-2">
                                                    <div
                                                        onClick={() => setStrategy('INTERVAL')}
                                                        className={clsx(
                                                            "p-3 rounded-xl border cursor-pointer transition-all",
                                                            strategy === 'INTERVAL' ? "bg-synapse-purple/20 border-synapse-purple" : "bg-white/5 border-white/10 hover:bg-white/10"
                                                        )}
                                                    >
                                                        <div className="text-sm font-bold text-white mb-1">💧 Drip Feed</div>
                                                        <div className="text-[10px] text-gray-400">Intervalo fixo entre vídeos. Ideal para consistência.</div>
                                                    </div>
                                                    <div
                                                        onClick={() => setStrategy('ORACLE')}
                                                        className={clsx(
                                                            "p-3 rounded-xl border cursor-pointer transition-all",
                                                            strategy === 'ORACLE' ? "bg-synapse-purple/20 border-synapse-purple" : "bg-white/5 border-white/10 hover:bg-white/10"
                                                        )}
                                                    >
                                                        <div className="text-sm font-bold text-white mb-1">🧠 Oracle AI</div>
                                                        <div className="text-[10px] text-gray-400">Melhores horários baseados em dados anteriores.</div>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Time Config */}
                                            <div className="space-y-4 p-4 rounded-xl bg-white/5 border border-white/5">
                                                <div className="space-y-2">
                                                    <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Início</label>
                                                    <div className="flex gap-2">
                                                        <input
                                                            type="date"
                                                            required
                                                            value={startDate}
                                                            onChange={(e) => setStartDate(e.target.value)}
                                                            className="flex-1 bg-black/30 border border-white/10 rounded-lg py-2 px-3 text-sm text-white focus:border-synapse-purple outline-none"
                                                        />
                                                        <input
                                                            type="time"
                                                            required
                                                            value={startTime}
                                                            onChange={(e) => setStartTime(e.target.value)}
                                                            className="flex-1 bg-black/30 border border-white/10 rounded-lg py-2 px-3 text-sm text-white focus:border-synapse-purple outline-none"
                                                        />
                                                    </div>
                                                </div>

                                                {strategy === 'INTERVAL' && (
                                                    <div className="space-y-2">
                                                        <label className="text-xs font-mono text-gray-500 uppercase tracking-wider block">Intervalo (Minutos)</label>
                                                        <input
                                                            type="number"
                                                            min="15"
                                                            step="15"
                                                            value={intervalMinutes}
                                                            onChange={(e) => setIntervalMinutes(parseInt(e.target.value))}
                                                            className="w-full bg-black/30 border border-white/10 rounded-lg py-2 px-3 text-sm text-white focus:border-synapse-purple outline-none"
                                                        />
                                                        <p className="text-[10px] text-gray-500">Ex: 60 = 1 vídeo por hora.</p>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Viral Boost */}
                                            <div className="flex items-center justify-between p-3 rounded-lg bg-synapse-purple/10 border border-synapse-purple/20">
                                                <div className="flex items-center gap-2">
                                                    <div className={`w-2 h-2 rounded-full ${viralBoost ? 'bg-synapse-purple animate-pulse' : 'bg-gray-600'}`} />
                                                    <span className="text-sm text-white font-medium">Viral Audio Boost (All)</span>
                                                </div>
                                                <label className="relative inline-flex items-center cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={viralBoost}
                                                        onChange={(e) => setViralBoost(e.target.checked)}
                                                        className="sr-only peer"
                                                    />
                                                    <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:bg-synapse-purple"></div>
                                                </label>
                                            </div>

                                            {/* Summary */}
                                            <div className="text-xs text-center text-gray-500">
                                                Total: {files.length * selectedProfiles.length} agendamentos previstos.
                                            </div>

                                            <div className="flex gap-3">
                                                <button
                                                    type="button"
                                                    onClick={onClose}
                                                    className="flex-1 px-4 py-3 rounded-lg border border-white/10 text-gray-400 hover:bg-white/5 hover:text-white transition-colors text-sm"
                                                >
                                                    Cancelar
                                                </button>
                                                <NeonButton
                                                    type="submit"
                                                    variant="primary"
                                                    className="flex-1"
                                                    disabled={files.length === 0 || selectedProfiles.length === 0}
                                                >
                                                    Iniciar Agendamento
                                                </NeonButton>
                                            </div>

                                        </div>
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
