'use client';

import { Fragment, useState, useEffect, useRef, useMemo } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { TikTokProfile } from '../types';
import { NeonButton } from './NeonButton';
import { XMarkIcon, CloudArrowUpIcon, TrashIcon, FilmIcon, ClockIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format, addMinutes } from 'date-fns';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';

interface BatchUploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    profiles: TikTokProfile[];
}

interface VideoFile extends File {
    preview?: string;
    duration?: number;
}

export default function BatchUploadModal({
    isOpen,
    onClose,
    onSuccess,
    profiles
}: BatchUploadModalProps) {
    // Files State
    const [files, setFiles] = useState<VideoFile[]>([]);

    // Config State
    const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
    const [strategy, setStrategy] = useState<'INTERVAL' | 'ORACLE'>('INTERVAL');
    const [intervalMinutes, setIntervalMinutes] = useState(60);
    const [startDate, setStartDate] = useState(format(new Date(), 'yyyy-MM-dd'));
    const [startTime, setStartTime] = useState('10:00');
    const [viralBoost, setViralBoost] = useState(false);

    // Dropzone Logic
    const onDrop = async (acceptedFiles: File[]) => {
        const newFiles = await Promise.all(acceptedFiles.map(async (file) => {
            const preview = await generateThumbnail(file);
            return Object.assign(file, { preview });
        }));
        setFiles(prev => [...prev, ...newFiles]);
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'video/*': [] }
    });

    const generateThumbnail = (file: File): Promise<string> => {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            video.preload = 'metadata';
            video.src = URL.createObjectURL(file);
            video.muted = true;
            video.playsInline = true;
            video.currentTime = 1; // Capture frame at 1s

            video.onloadeddata = () => {
                const canvas = document.createElement('canvas');
                canvas.width = 160;
                canvas.height = 90;
                const ctx = canvas.getContext('2d');
                ctx?.drawImage(video, 0, 0, 160, 90);
                resolve(canvas.toDataURL('image/jpeg'));
                URL.revokeObjectURL(video.src);
            };

            video.onerror = () => resolve(''); // Fallback
        });
    };

    const toggleProfile = (id: string) => {
        setSelectedProfiles(prev =>
            prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
        );
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    // Timeline Calculation
    const timelinePreview = useMemo(() => {
        if (files.length === 0) return [];
        const start = new Date(`${startDate}T${startTime}`);
        return files.map((_, idx) => {
            const time = addMinutes(start, idx * intervalMinutes);
            return format(time, 'HH:mm');
        });
    }, [files, startDate, startTime, intervalMinutes]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const filePaths = files.map(f => `C:\\Videos\\${f.name}`); // Mock path

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
            setFiles([]);
            setSelectedProfiles([]);
        } catch (error) {
            console.error("Batch error", error);
            alert("Failed to schedule batch.");
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
                            <Dialog.Panel className="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-[#0f0a15] border border-white/10 p-6 text-left shadow-[0_0_50px_rgba(139,92,246,0.1)] transition-all">
                                <Dialog.Title className="flex justify-between items-center mb-8">
                                    <div>
                                        <h3 className="text-xl font-bold text-white flex items-center gap-3">
                                            <CloudArrowUpIcon className="w-7 h-7 text-synapse-purple" />
                                            Batch Commander
                                        </h3>
                                        <p className="text-xs text-gray-500 font-mono mt-1">// MASS_UPLOAD_PROTOCOL</p>
                                    </div>
                                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                                        <XMarkIcon className="w-6 h-6" />
                                    </button>
                                </Dialog.Title>

                                <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                                    {/* LEFT: FILES (Cols 7) */}
                                    <div className="lg:col-span-7 space-y-6">
                                        {/* Dropzone */}
                                        <div
                                            {...getRootProps()}
                                            className={clsx(
                                                "border-2 border-dashed rounded-2xl h-48 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 relative overflow-hidden group",
                                                isDragActive
                                                    ? "border-synapse-purple bg-synapse-purple/10 scale-[1.02] shadow-[0_0_30px_rgba(139,92,246,0.3)]"
                                                    : "border-gray-700 hover:border-synapse-purple/50 bg-white/5"
                                            )}
                                        >
                                            <input {...getInputProps()} />
                                            <CloudArrowUpIcon className={clsx("w-10 h-10 mb-3 transition-colors", isDragActive ? "text-synapse-purple animate-bounce" : "text-gray-500 group-hover:text-synapse-purple")} />
                                            <p className="text-sm text-gray-300 font-medium">Drag & Drop videos here</p>
                                            <p className="text-xs text-gray-600 mt-1">or click to browse filesystem</p>

                                            {isDragActive && (
                                                <div className="absolute inset-0 bg-synapse-purple/10 pointer-events-none" />
                                            )}
                                        </div>

                                        {/* Video Grid */}
                                        <div className="space-y-2">
                                            <div className="flex justify-between items-center px-1">
                                                <label className="text-xs font-mono text-gray-500 uppercase tracking-wider">Queue ({files.length})</label>
                                                {files.length > 0 && (
                                                    <button type="button" onClick={() => setFiles([])} className="text-[10px] text-red-500 hover:text-red-400">Clear All</button>
                                                )}
                                            </div>

                                            {files.length === 0 ? (
                                                <div className="h-40 flex items-center justify-center text-gray-700 text-sm border border-white/5 rounded-xl bg-black/20">
                                                    Queue is empty
                                                </div>
                                            ) : (
                                                <div className="grid grid-cols-3 gap-3 max-h-[300px] overflow-y-auto custom-scrollbar p-1">
                                                    <AnimatePresence>
                                                        {files.map((file, idx) => (
                                                            <motion.div
                                                                key={`${file.name}-${idx}`}
                                                                initial={{ opacity: 0, scale: 0.9 }}
                                                                animate={{ opacity: 1, scale: 1 }}
                                                                exit={{ opacity: 0, scale: 0.9 }}
                                                                className="relative group aspect-video bg-black rounded-lg overflow-hidden border border-white/10"
                                                            >
                                                                {file.preview ? (
                                                                    <img src={file.preview} alt="thumb" className="w-full h-full object-cover opacity-70 group-hover:opacity-100 transition-opacity" />
                                                                ) : (
                                                                    <div className="w-full h-full flex items-center justify-center bg-gray-900">
                                                                        <FilmIcon className="w-6 h-6 text-gray-600" />
                                                                    </div>
                                                                )}

                                                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent p-2 flex flex-col justify-end">
                                                                    <p className="text-[10px] text-white truncate w-full">{file.name}</p>
                                                                </div>

                                                                <button
                                                                    type="button"
                                                                    onClick={() => removeFile(idx)}
                                                                    className="absolute top-1 right-1 p-1 bg-black/60 rounded text-gray-400 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                                                                >
                                                                    <TrashIcon className="w-3 h-3" />
                                                                </button>

                                                                <div className="absolute top-1 left-1 px-1.5 py-0.5 bg-synapse-purple rounded text-[9px] text-white font-mono shadow-lg">
                                                                    #{idx + 1}
                                                                </div>
                                                            </motion.div>
                                                        ))}
                                                    </AnimatePresence>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* RIGHT: CONFIG (Cols 5) */}
                                    <div className="lg:col-span-5 space-y-6 flex flex-col h-full">

                                        {/* Strategy */}
                                        <div className="grid grid-cols-2 gap-3">
                                            {['INTERVAL', 'ORACLE'].map((opt) => (
                                                <div
                                                    key={opt}
                                                    onClick={() => setStrategy(opt as any)}
                                                    className={clsx(
                                                        "p-3 rounded-xl bordercursor-pointer transition-all border relative overflow-hidden",
                                                        strategy === opt
                                                            ? "bg-synapse-purple/20 border-synapse-purple shadow-[0_0_15px_rgba(139,92,246,0.2)]"
                                                            : "bg-white/5 border-white/10 hover:bg-white/10"
                                                    )}
                                                >
                                                    <div className="relative z-10">
                                                        <div className="text-sm font-bold text-white mb-1">
                                                            {opt === 'INTERVAL' ? '💧 Drip Feed' : '🧠 Oracle AI'}
                                                        </div>
                                                        <div className="text-[10px] text-gray-400 leading-tight">
                                                            {opt === 'INTERVAL' ? 'Regular intervals' : 'AI optimized times'}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        {/* Timeline Config */}
                                        <div className="p-5 rounded-2xl bg-white/5 border border-white/5 space-y-4">
                                            <div className="flex gap-3">
                                                <div className="flex-1 space-y-1">
                                                    <label className="text-[10px] uppercase text-gray-500 font-bold">Start Date</label>
                                                    <input
                                                        type="date" value={startDate}
                                                        onChange={e => setStartDate(e.target.value)}
                                                        className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-synapse-purple"
                                                    />
                                                </div>
                                                <div className="flex-1 space-y-1">
                                                    <label className="text-[10px] uppercase text-gray-500 font-bold">Start Time</label>
                                                    <input
                                                        type="time" value={startTime}
                                                        onChange={e => setStartTime(e.target.value)}
                                                        className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-synapse-purple"
                                                    />
                                                </div>
                                            </div>

                                            {strategy === 'INTERVAL' && (
                                                <div className="space-y-3">
                                                    <div className="flex justify-between items-center">
                                                        <label className="text-[10px] uppercase text-gray-500 font-bold">Frequency</label>
                                                        <span className="text-xs text-synapse-purple font-mono">
                                                            {intervalMinutes < 60 ? `${intervalMinutes}m` : `${(intervalMinutes / 60).toFixed(1)}h`}
                                                        </span>
                                                    </div>

                                                    {/* Presets */}
                                                    <div className="grid grid-cols-3 gap-2">
                                                        {[
                                                            { label: '1x / Day', val: 1440 },
                                                            { label: '2x / Day', val: 720 },
                                                            { label: '3x / Day', val: 480 },
                                                            { label: '1x / Week', val: 10080 },
                                                            { label: 'Every 4h', val: 240 },
                                                            { label: 'Custom', val: -1 }
                                                        ].map((opt) => (
                                                            <button
                                                                key={opt.label}
                                                                type="button"
                                                                onClick={() => {
                                                                    if (opt.val !== -1) setIntervalMinutes(opt.val);
                                                                    // We could track "mode" state if needed, but checking val is enough for UI highlight
                                                                }}
                                                                className={clsx(
                                                                    "px-2 py-1.5 rounded-lg text-[10px] border transition-all",
                                                                    (opt.val === intervalMinutes || (opt.val === -1 && ![1440, 720, 480, 10080, 240].includes(intervalMinutes)))
                                                                        ? "bg-synapse-purple text-white border-synapse-purple"
                                                                        : "bg-black/40 text-gray-400 border-white/10 hover:border-white/30"
                                                                )}
                                                            >
                                                                {opt.label}
                                                            </button>
                                                        ))}
                                                    </div>

                                                    {/* Custom Slider (always visible or only when custom?) -> Always visible for fine tuning is better UX */}
                                                    <input
                                                        type="range" min="15" max="2880" step="15"
                                                        value={intervalMinutes}
                                                        onChange={e => setIntervalMinutes(Number(e.target.value))}
                                                        className="w-full accent-synapse-purple h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer mt-2"
                                                    />
                                                </div>
                                            )}

                                            {/* Visual Timeline Bar */}
                                            {files.length > 0 && (
                                                <div className="pt-2 border-t border-white/5 mt-4">
                                                    <label className="text-[10px] uppercase text-gray-500 font-bold mb-2 block">Timeline Preview</label>
                                                    <div className="flex items-center gap-1 overflow-x-auto pb-2 custom-scrollbar">
                                                        {timelinePreview.map((time, i) => (
                                                            <div key={i} className="flex-shrink-0 flex flex-col items-center gap-1 group">
                                                                <div className="w-1.5 h-6 rounded-full bg-gray-700 group-hover:bg-synapse-purple transition-colors relative">
                                                                    {/* Connector */}
                                                                    {i < timelinePreview.length - 1 && (
                                                                        <div className="absolute top-1/2 left-full w-4 h-[1px] bg-gray-800 -translate-y-1/2 -z-10" />
                                                                    )}
                                                                </div>
                                                                <span className="text-[9px] text-gray-500 font-mono group-hover:text-white">{time}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Profiles Selection */}
                                        <div className="flex-1 flex flex-col min-h-0">
                                            <div className="flex justify-between items-center mb-2">
                                                <label className="text-xs font-mono text-gray-500 uppercase tracking-wider">Targets ({selectedProfiles.length})</label>
                                                <div className="flex gap-2">
                                                    <button type="button" onClick={() => setSelectedProfiles(profiles.map(p => p.id))} className="text-[10px] text-synapse-purple hover:underline">All</button>
                                                    <button type="button" onClick={() => setSelectedProfiles([])} className="text-[10px] text-gray-500 hover:text-white hover:underline">None</button>
                                                </div>
                                            </div>

                                            <div className="flex-1 overflow-y-auto custom-scrollbar border border-white/5 rounded-xl bg-black/20 p-2 space-y-1">
                                                {profiles.map(p => (
                                                    <div
                                                        key={p.id}
                                                        onClick={() => toggleProfile(p.id)}
                                                        className={clsx(
                                                            "flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all border",
                                                            selectedProfiles.includes(p.id)
                                                                ? "bg-synapse-purple/10 border-synapse-purple/30"
                                                                : "bg-transparent border-transparent hover:bg-white/5"
                                                        )}
                                                    >
                                                        <div className="w-6 h-6 rounded-full bg-gray-800 overflow-hidden text-[10px] flex items-center justify-center font-bold text-gray-400">
                                                            {p.avatar_url ? <img src={p.avatar_url} className="w-full h-full object-cover" /> : p.label.substring(0, 1)}
                                                        </div>
                                                        <span className={clsx("text-xs truncate flex-1", selectedProfiles.includes(p.id) ? "text-white" : "text-gray-400")}>{p.label}</span>
                                                        {selectedProfiles.includes(p.id) && <div className="w-1.5 h-1.5 rounded-full bg-synapse-purple shadow-[0_0_5px_#8b5cf6]" />}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Actions */}
                                        <div className="flex gap-3 pt-2">
                                            <NeonButton
                                                type="submit"
                                                variant="primary"
                                                className="w-full py-3 text-sm"
                                                disabled={files.length === 0 || selectedProfiles.length === 0}
                                            >
                                                Launch Campaign
                                            </NeonButton>
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
