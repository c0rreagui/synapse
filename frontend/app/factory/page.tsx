
"use client";

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import {
    ArrowLeftIcon, FolderIcon, ArrowPathIcon,
    CheckCircleIcon, ClockIcon, ExclamationTriangleIcon, PlayIcon, CubeTransparentIcon,
    CpuChipIcon
} from '@heroicons/react/24/outline';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import clsx from 'clsx';
import useWebSocket from '../hooks/useWebSocket';
import { BackendStatus } from '../types';

interface IngestionStatus { queued: number; processing: number; completed: number; failed: number; }

const API_BASE = 'http://localhost:8000/api/v1';

export default function FactoryPage() {
    const [status, setStatus] = useState<IngestionStatus>({ queued: 0, processing: 0, completed: 0, failed: 0 });
    const [scanning, setScanning] = useState(false);
    const [lastScan, setLastScan] = useState<string>('');
    const [activeJob, setActiveJob] = useState<BackendStatus['job'] | null>(null);

    const fetchStatus = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/ingest/status`);
            if (res.ok) setStatus(await res.json());
        } catch { /* Backend offline */ }
    }, []);

    // WebSocket Integration
    const { isConnected } = useWebSocket({
        onPipelineUpdate: (data) => {
            console.log("⚡ Pipeline Update:", data);
            setActiveJob(data.job);
            // Trigger status refresh when job state changes to keep counts in sync
            fetchStatus();
        }
    });

    const triggerScan = async () => {
        setScanning(true);
        try {
            await fetch(`${API_BASE}/content/scan`, { method: 'POST' });
            setLastScan(new Date().toLocaleTimeString('pt-BR'));
            await fetchStatus();
        } catch { /* Error */ }
        setScanning(false);
    };

    useEffect(() => {
        fetchStatus();
        // Fallback polling (keep sync even if WS misses packet)
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const folders = [
        { name: 'inputs/', description: 'Arquivos aguardando processamento', count: status.queued, color: 'text-synapse-amber', bg: 'bg-synapse-amber/15', icon: ClockIcon },
        { name: 'processing/', description: 'Em processamento pelo Brain', count: status.processing, color: 'text-synapse-cyan', bg: 'bg-synapse-cyan/15', icon: CubeTransparentIcon },
        { name: 'done/', description: 'Processamento concluído', count: status.completed, color: 'text-synapse-emerald', bg: 'bg-synapse-emerald/15', icon: CheckCircleIcon },
        { name: 'errors/', description: 'Falhas no processamento', count: status.failed, color: 'text-red-500', bg: 'bg-red-500/15', icon: ExclamationTriangleIcon },
    ];

    return (
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans selection:bg-synapse-primary selection:text-white">
            <Sidebar />

            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern">
                <header className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link href="/">
                            <div className="w-10 h-10 rounded-lg bg-[#1c2128] border border-white/10 flex items-center justify-center cursor-pointer hover:border-synapse-primary/50 transition-colors group">
                                <ArrowLeftIcon className="w-5 h-5 text-gray-400 group-hover:text-synapse-primary" />
                            </div>
                        </Link>
                        <div>
                            <h2 className="text-2xl font-bold text-white m-0 flex items-center gap-3">
                                Factory Watcher
                                {isConnected && <span className="flex items-center gap-1.5 text-[10px] bg-synapse-emerald/10 text-synapse-emerald px-2 py-0.5 rounded-full border border-synapse-emerald/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]"><span className="w-1.5 h-1.5 rounded-full bg-synapse-emerald animate-pulse"></span>LIVE</span>}
                            </h2>
                            <p className="text-sm text-gray-500 m-0">Monitoramento de pastas do pipeline</p>
                        </div>
                    </div>
                    <NeonButton
                        onClick={triggerScan}
                        disabled={scanning}
                        className={clsx("flex items-center gap-2", scanning && "opacity-70 cursor-wait")}
                    >
                        <ArrowPathIcon className={clsx("w-4 h-4", scanning && "animate-spin")} />
                        {scanning ? 'Escaneando...' : 'Escanear Pastas'}
                    </NeonButton>
                </header>

                {/* Active Job Monitor */}
                {activeJob && activeJob.name && activeJob.name !== 'Idle' && activeJob.name !== 'None' && (
                    <div className="mb-8 animate-in slide-in-from-top-4 fade-in duration-500">
                        <StitchCard className="p-1 relative overflow-hidden bg-gradient-to-r from-synapse-primary/20 to-synapse-cyan/20 border-synapse-primary/50">
                            <div className="absolute inset-0 bg-grid-white/[0.05] [mask-image:linear-gradient(0deg,white,transparent)]" />
                            <div className="bg-[#1c2128]/90 rounded-lg p-4 relative z-10 flex items-center gap-4 backdrop-blur-sm">
                                <div className="w-12 h-12 rounded-full bg-synapse-primary/20 flex items-center justify-center">
                                    <CpuChipIcon className="w-6 h-6 text-synapse-primary animate-pulse" />
                                </div>
                                <div className="flex-1">
                                    <div className="flex justify-between items-center mb-1">
                                        <h3 className="text-white font-bold flex items-center gap-2">
                                            Processando Agora: <span className="text-synapse-primary">{activeJob.name}</span>
                                        </h3>
                                        <span className="text-xs font-mono text-synapse-cyan bg-synapse-cyan/10 px-2 py-1 rounded">{activeJob.step}</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-synapse-primary to-synapse-cyan transition-all duration-300"
                                            style={{ width: `${activeJob.progress}%` }}
                                        />
                                    </div>
                                    <div className="mt-1 flex justify-between text-xs text-gray-400">
                                        <span>{activeJob.progress}% Concluído</span>
                                        <span className="font-mono">{activeJob.logs?.[0] || 'Iniciando...'}</span>
                                    </div>
                                </div>
                            </div>
                        </StitchCard>
                    </div>
                )}

                {/* Folder Status Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    {folders.map((folder, i) => (
                        <StitchCard key={i} className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-12 h-12 rounded-xl ${folder.bg} flex items-center justify-center`}>
                                        <folder.icon className={`w-6 h-6 ${folder.color}`} />
                                    </div>
                                    <div>
                                        <h3 className="text-base font-bold text-white m-0 font-mono">{folder.name}</h3>
                                        <p className="text-xs text-gray-500 m-0 mt-1">{folder.description}</p>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <span className={`text-4xl font-bold ${folder.color}`}>{folder.count}</span>
                                <span className="text-sm text-gray-500">arquivos</span>
                            </div>
                        </StitchCard>
                    ))}
                </div>

                {/* Pipeline Flow */}
                <StitchCard className="p-8">
                    <h3 className="text-lg font-bold text-white mb-8 border-b border-white/10 pb-4">Pipeline de Processamento</h3>
                    <div className="flex items-center justify-between relative px-8">
                        {/* Connecting Line */}
                        <div className="absolute top-[34px] left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-synapse-amber via-synapse-cyan to-synapse-emerald opacity-20 z-0"></div>

                        {['inputs/', 'processing/', 'done/'].map((step, i) => {
                            const colors = [
                                { bg: 'bg-synapse-amber/10', text: 'text-synapse-amber', border: 'border-synapse-amber/30' },
                                { bg: 'bg-synapse-cyan/10', text: 'text-synapse-cyan', border: 'border-synapse-cyan/30' },
                                { bg: 'bg-synapse-emerald/10', text: 'text-synapse-emerald', border: 'border-synapse-emerald/30' }
                            ][i];

                            return (
                                <div key={i} className="relative z-10 flex flex-col items-center">
                                    <div className={clsx(
                                        "w-16 h-16 rounded-full flex items-center justify-center mb-4 border transition-all duration-500",
                                        colors.bg, colors.border
                                    )}>
                                        {i === 0 ? <ClockIcon className={`w-7 h-7 ${colors.text}`} /> :
                                            i === 1 ? <CubeTransparentIcon className={`w-7 h-7 ${colors.text}`} /> :
                                                <CheckCircleIcon className={`w-7 h-7 ${colors.text}`} />}
                                    </div>
                                    <p className="text-xs text-gray-400 font-mono mb-1">{step}</p>
                                    <p className="text-2xl font-bold text-white">
                                        {i === 0 ? status.queued : i === 1 ? status.processing : status.completed}
                                    </p>

                                    {i < 2 && (
                                        <div className="absolute -right-[calc(50%-2rem)] top-6 text-gray-600">
                                            <PlayIcon className="w-4 h-4" />
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </StitchCard>

                {lastScan && (
                    <p className="text-xs text-gray-500 mt-4 text-center font-mono">
                        Último scan: {lastScan}
                    </p>
                )}
            </main>
        </div>
    );
}
