import React, { useRef } from 'react';
import { useBatch } from './BatchContext';
import { useDropzone } from 'react-dropzone';
import { Music, Sparkles, X, Play } from 'lucide-react';
import clsx from 'clsx';

export function BatchMain() {
    const {
        files, setFiles,
        viralBoost, setViralBoost,
        mixViralSounds, setMixViralSounds,
        aiCaptions,
        setEditingFileId, // [SYN-44] Added for Editor
        privacyLevel, setPrivacyLevel
    } = useBatch();

    // Dropzone Logic
    const onDrop = (acceptedFiles: File[]) => {
        const newFiles = acceptedFiles.map(file => ({
            file,
            filename: file.name,
            preview: URL.createObjectURL(file), // Basic preview
            duration: 0, // Placeholder
            status: 'pending' as const,
            progress: 0,
            id: Math.random().toString(36).substr(2, 9)
        }));
        setFiles(prev => [...prev, ...newFiles]);
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'video/*': ['.mp4', '.mov', '.avi'] },
        multiple: true
    });

    const removeFile = (id: string) => {
        setFiles(prev => prev.filter(f => f.id !== id));
    };

    return (
        <div className="flex-1 h-full bg-[#0a0a0a]/50 flex flex-col relative">
            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-8">

                {/* 1. Intelligence Section (Opus Style "Feature Block") */}
                <div className="mb-8 p-1 rounded-2xl bg-gradient-to-r from-synapse-purple/20 to-cyan-500/20 p-[1px]">
                    <div className="bg-[#0f0a15] rounded-2xl p-5 backdrop-blur-xl">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-synapse-purple to-cyan-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
                                    <Sparkles className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-white">Synapse Estúdio</h3>
                                    <p className="text-[11px] text-gray-400">Automação de conteúdo e otimização viral</p>
                                </div>
                            </div>

                            {/* Global Toggles */}
                            <div className="flex items-center gap-4">
                                {/* Privacy Toggle */}
                                <div className="flex items-center gap-2 cursor-pointer group" onClick={() => setPrivacyLevel(privacyLevel === 'public' ? 'private' : 'public')}>
                                    <span className="text-[11px] font-mono text-gray-400 group-hover:text-white transition-colors">
                                        {privacyLevel === 'public' ? 'PÚBLICO' : 'PRIVADO'}
                                    </span>
                                    <div className={clsx(
                                        "w-10 h-6 rounded-full p-1 transition-colors",
                                        privacyLevel === 'public' ? "bg-cyan-500" : "bg-red-500/50"
                                    )}>
                                        <div className={clsx(
                                            "w-4 h-4 rounded-full bg-white shadow-sm transition-transform",
                                            privacyLevel === 'public' ? "translate-x-4" : "translate-x-0"
                                        )} />
                                    </div>
                                </div>

                                <div className="w-px h-4 bg-white/10" />

                                {/* Viral Boost */}
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <span className="text-[11px] font-mono text-gray-400 group-hover:text-white transition-colors">VIRAL BOOST</span>
                                    <div className={clsx(
                                        "w-10 h-6 rounded-full p-1 transition-colors",
                                        viralBoost ? "bg-purple-600 shadow-[0_0_10px_rgba(147,51,234,0.5)]" : "bg-gray-700"
                                    )} onClick={() => setViralBoost(!viralBoost)}>
                                        <div className={clsx(
                                            "w-4 h-4 rounded-full bg-white shadow-sm transition-transform",
                                            viralBoost ? "translate-x-4" : "translate-x-0"
                                        )} />
                                    </div>
                                </label>
                            </div>
                        </div>

                        {/* Collapsible Options */}
                        {viralBoost && (
                            <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-white/5 animate-in slide-in-from-top-2 duration-300">
                                {/* Mix Options */}
                                <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                                            <Music className="w-4 h-4 text-cyan-400" />
                                        </div>
                                        <div>
                                            <p className="text-xs font-medium text-white">Mixar Trends</p>
                                            <p className="text-[10px] text-gray-500">Música única por vídeo</p>
                                        </div>
                                    </div>
                                    <input
                                        type="checkbox"
                                        checked={mixViralSounds}
                                        onChange={(e) => setMixViralSounds(e.target.checked)}
                                        className="accent-cyan-400 w-4 h-4 rounded-md cursor-pointer"
                                    />
                                </div>

                                {/* Smart Captions (Read Only / Indicator) */}
                                <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between opacity-80">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                            <span className="text-xs font-black text-purple-400">AI</span>
                                        </div>
                                        <div>
                                            <p className="text-xs font-medium text-white">Smart Captions</p>
                                            <p className="text-[10px] text-gray-500">Gerado automaticamente</p>
                                        </div>
                                    </div>
                                    <div className="text-[10px] text-purple-400 font-mono font-bold px-2 py-1 rounded bg-purple-500/10 border border-purple-500/20">
                                        AUTO
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* 2. Upload/Drop Area */}
                {files.length === 0 ? (
                    <div
                        {...getRootProps()}
                        className={clsx(
                            "border-2 border-dashed rounded-3xl h-64 flex flex-col items-center justify-center cursor-pointer transition-all",
                            isDragActive
                                ? "border-synapse-purple bg-synapse-purple/10 scale-[0.99]"
                                : "border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20"
                        )}
                    >
                        <input {...getInputProps()} />
                        <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center mb-4 shadow-xl">
                            <span className="text-2xl">☁️</span>
                        </div>
                        <p className="text-sm font-medium text-white mb-2">Arraste seus vídeos aqui</p>
                        <p className="text-xs text-gray-500">MP4, MOV ou AVI</p>
                    </div>
                ) : (
                    /* 3. Grid Gallery (Opus Style) */
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-20">
                        {/* Add More Button */}
                        <div
                            {...getRootProps()}
                            className="aspect-[9/16] rounded-xl border border-dashed border-white/20 bg-white/5 hover:bg-white/10 flex flex-col items-center justify-center cursor-pointer transition-colors group"
                        >
                            <input {...getInputProps()} />
                            <div className="w-8 h-8 rounded-full border border-white/30 flex items-center justify-center text-white mb-2 group-hover:scale-110 transition-transform">
                                +
                            </div>
                            <span className="text-xs text-gray-400">Adicionar</span>
                        </div>

                        {files.map((file, idx) => (
                            <div
                                key={file.id}
                                onClick={() => setEditingFileId(file.id)}
                                className="relative aspect-[9/16] bg-black rounded-xl overflow-hidden group border border-white/10 shadow-lg cursor-pointer hover:border-synapse-purple/50 transition-all"
                            >
                                {/* Preview */}
                                {file.preview ? (
                                    <video src={file.preview} className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" />
                                ) : (
                                    <div className="w-full h-full bg-gray-900" />
                                )}

                                {/* Overlay Info */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-3 flex flex-col justify-end">
                                    <p className="text-xs font-medium text-white line-clamp-2 leading-tight mb-1">{file.filename}</p>
                                    <p className="text-[10px] text-gray-500">
                                        {file.file ? (file.file.size / 1024 / 1024).toFixed(1) + ' MB' : 'Remoto'}
                                    </p>
                                </div>

                                {/* Order Badge */}
                                <div className="absolute top-2 left-2 w-6 h-6 rounded-lg bg-black/50 border border-white/10 backdrop-blur flex items-center justify-center text-[10px] font-bold text-white z-10">
                                    {idx + 1}
                                </div>

                                {/* Remove Button */}
                                <button
                                    onClick={(e) => { e.stopPropagation(); removeFile(file.id); }}
                                    className="absolute top-2 right-2 w-6 h-6 rounded-lg bg-red-500/20 hover:bg-red-500 text-red-500 hover:text-white flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100"
                                >
                                    <X className="w-3 h-3" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}

            </div>
        </div>
    );
}
