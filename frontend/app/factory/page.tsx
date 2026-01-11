'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import {
    ArrowLeftIcon, FolderIcon, ArrowPathIcon,
    CheckCircleIcon, ClockIcon, ExclamationTriangleIcon, PlayIcon, CubeTransparentIcon
} from '@heroicons/react/24/outline';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import clsx from 'clsx';

interface IngestionStatus { queued: number; processing: number; completed: number; failed: number; }

const API_BASE = 'http://localhost:8000/api/v1';

export default function FactoryPage() {
    const [status, setStatus] = useState<IngestionStatus>({ queued: 0, processing: 0, completed: 0, failed: 0 });
    const [scanning, setScanning] = useState(false);
    const [lastScan, setLastScan] = useState<string>('');

    const fetchStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/ingest/status`);
            if (res.ok) setStatus(await res.json());
        } catch { /* Backend offline */ }
    };

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
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    const folders = [
        { name: 'inputs/', description: 'Arquivos aguardando processamento', count: status.queued, color: 'text-synapse-amber', bg: 'bg-synapse-amber/15', icon: ClockIcon },
        { name: 'processing/', description: 'Em processamento pelo Brain', count: status.processing, color: 'text-synapse-cyan', bg: 'bg-synapse-cyan/15', icon: CubeTransparentIcon },
        { name: 'done/', description: 'Processamento concluído', count: status.completed, color: 'text-synapse-emerald', bg: 'bg-synapse-emerald/15', icon: CheckCircleIcon },
        { name: 'errors/', description: 'Falhas no processamento', count: status.failed, color: 'text-red-500', bg: 'bg-red-500/15', icon: ExclamationTriangleIcon },
    ];

    return (
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans selection:bg-synapse-primary selection:text-white">
            <Sidebar />

            {/* MAIN */}
            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern">
                <header className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                        <Link href="/">
                            <div className="w-10 h-10 rounded-lg bg-[#1c2128] border border-white/10 flex items-center justify-center cursor-pointer hover:border-synapse-primary/50 transition-colors group">
                                <ArrowLeftIcon className="w-5 h-5 text-gray-400 group-hover:text-synapse-primary" />
                            </div>
                        </Link>
                        <div>
                            <h2 className="text-2xl font-bold text-white m-0">Factory Watcher</h2>
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
