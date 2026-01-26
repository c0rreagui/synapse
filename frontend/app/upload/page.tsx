'use client';

import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import Sidebar from '../components/Sidebar';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import {
    CloudArrowUpIcon, DocumentIcon, FilmIcon,
    XMarkIcon, CheckCircleIcon, ArrowPathIcon
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { TikTokProfile } from '../types';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace('localhost', '127.0.0.1') + '/api/v1';

export default function UploadPage() {
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
    const [selectedProfile, setSelectedProfile] = useState<string>('');
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch Profiles for Dropdown
    useEffect(() => {
        fetch(`${API_BASE}/profiles/list`)
            .then(res => res.json())
            .then(data => {
                setProfiles(data);
                if (data.length > 0) setSelectedProfile(data[0].id);
            })
            .catch(console.error);
    }, []);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        setFiles(prev => [...prev, ...acceptedFiles]);
        setSuccess(false);
        setError(null);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'video/mp4': ['.mp4'],
            'video/quicktime': ['.mov'],
            'video/x-msvideo': ['.avi'],
            'video/webm': ['.webm']
        }
    });

    const removeFile = (idx: number) => {
        setFiles(prev => prev.filter((_, i) => i !== idx));
    };

    const handleUpload = async () => {
        if (!files.length || !selectedProfile) return;
        setUploading(true);
        setProgress(0);
        setError(null);

        // Upload sequentially (could be parallel)
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('profile_id', selectedProfile); // Backend handles formatting

            try {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', `${API_BASE}/ingestion/upload`);

                xhr.upload.onprogress = (event) => {
                    if (event.lengthComputable) {
                        const fileProgress = (event.loaded / event.total) * 100;
                        const totalProgress = ((i * 100) + fileProgress) / files.length;
                        setProgress(totalProgress);
                    }
                };

                await new Promise((resolve, reject) => {
                    xhr.onload = () => {
                        if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.response);
                        else reject(xhr.response);
                    };
                    xhr.onerror = () => reject('Network Error');
                    xhr.send(formData);
                });

            } catch (err: any) {
                console.error(err);
                setError(`Erro ao enviar ${file.name}`);
                setUploading(false);
                return;
            }
        }

        setProgress(100);
        setUploading(false);
        setSuccess(true);
        setFiles([]);
        setTimeout(() => setSuccess(false), 3000);
    };

    return (
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans">
            <Sidebar />

            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern">
                <header className="mb-8">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <CloudArrowUpIcon className="w-8 h-8 text-synapse-primary" />
                        Upload Manual
                    </h2>
                    <p className="text-sm text-gray-500">Envie vídeos para a fila de processamento</p>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* LEFT: Upload Area */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Profile Selector */}
                        <StitchCard className="p-4 flex items-center gap-4 bg-black/20">
                            <span className="text-sm font-bold text-gray-400 uppercase">Perfil Destino:</span>
                            <select
                                value={selectedProfile}
                                onChange={(e) => setSelectedProfile(e.target.value)}
                                className="bg-[#1c2128] border border-white/10 text-white rounded px-3 py-2 text-sm flex-1 focus:border-synapse-primary outline-none"
                            >
                                <option value="" disabled>Selecione um perfil...</option>
                                {profiles.map(p => (
                                    <option key={p.id} value={p.id}>{p.label} (@{p.username})</option>
                                ))}
                            </select>
                        </StitchCard>

                        {/* Dropzone */}
                        <div
                            {...getRootProps()}
                            className={clsx(
                                "border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer transition-all",
                                isDragActive ? "border-synapse-primary bg-synapse-primary/10" : "border-white/10 hover:border-white/20 hover:bg-white/5",
                                "min-h-[300px]"
                            )}
                        >
                            <input {...getInputProps()} />
                            <CloudArrowUpIcon className={clsx("w-16 h-16 mb-4 transition-colors", isDragActive ? "text-synapse-primary" : "text-gray-600")} />
                            {isDragActive ? (
                                <p className="text-synapse-primary font-bold">Solte os arquivos aqui...</p>
                            ) : (
                                <div className="text-center">
                                    <p className="text-lg font-bold text-gray-300">Arraste vídeos ou clique para selecionar</p>
                                    <p className="text-sm text-gray-500 mt-2">MP4, MOV, AVI (Max 500MB)</p>
                                </div>
                            )}
                        </div>

                        {/* Error/Success Messages */}
                        {error && (
                            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                                ⚠️ {error}
                            </div>
                        )}
                        {success && (
                            <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2">
                                <CheckCircleIcon className="w-5 h-5" />
                                Upload concluído! Vídeos enviados para a fila.
                            </div>
                        )}
                    </div>

                    {/* RIGHT: File List */}
                    <div className="lg:col-span-1">
                        <StitchCard className="h-full flex flex-col p-0 overflow-hidden bg-[#161b22]">
                            <div className="p-4 border-b border-white/10 bg-black/20 font-bold text-sm text-gray-400 uppercase tracking-wider">
                                Fila de Upload ({files.length})
                            </div>

                            <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar max-h-[500px]">
                                {files.length === 0 && (
                                    <div className="h-full flex flex-col items-center justify-center text-gray-600 p-8 text-center opacity-50">
                                        <DocumentIcon className="w-12 h-12 mb-2" />
                                        <span className="text-xs">Nenhum arquivo selecionado</span>
                                    </div>
                                )}
                                {files.map((file, idx) => (
                                    <div key={idx} className="flex items-center gap-3 p-3 rounded bg-white/5 border border-white/5 group">
                                        <FilmIcon className="w-8 h-8 text-synapse-primary/50" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-white truncate font-medium">{file.name}</p>
                                            <p className="text-[10px] text-gray-500">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                                        </div>
                                        {!uploading && (
                                            <button
                                                onClick={() => removeFile(idx)}
                                                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 hover:text-red-400 rounded transition-all"
                                            >
                                                <XMarkIcon className="w-4 h-4" />
                                            </button>
                                        )}
                                    </div>
                                ))}
                            </div>

                            <div className="p-4 border-t border-white/10 bg-black/20">
                                {uploading && (
                                    <div className="mb-4">
                                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                                            <span>Enviando...</span>
                                            <span>{Math.round(progress)}%</span>
                                        </div>
                                        <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                            <div className="h-full bg-synapse-primary transition-all duration-300" style={{ width: `${progress}%` }} />
                                        </div>
                                    </div>
                                )}
                                <NeonButton
                                    className="w-full flex justify-center items-center gap-2"
                                    onClick={handleUpload}
                                    disabled={files.length === 0 || uploading || !selectedProfile}
                                >
                                    {uploading ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <CloudArrowUpIcon className="w-4 h-4" />}
                                    {uploading ? 'Enviando...' : 'Iniciar Upload'}
                                </NeonButton>
                            </div>
                        </StitchCard>
                    </div>
                </div>
            </main>
        </div>
    );
}
