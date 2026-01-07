'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import {
    ArrowLeftIcon, FolderIcon, ArrowPathIcon,
    CheckCircleIcon, ClockIcon, ExclamationTriangleIcon, PlayIcon, CubeTransparentIcon
} from '@heroicons/react/24/outline';

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
        { name: 'inputs/', description: 'Arquivos aguardando processamento', count: status.queued, color: '#d29922', icon: ClockIcon },
        { name: 'processing/', description: 'Em processamento pelo Brain', count: status.processing, color: '#58a6ff', icon: CubeTransparentIcon },
        { name: 'done/', description: 'Processamento concluído', count: status.completed, color: '#3fb950', icon: CheckCircleIcon },
        { name: 'errors/', description: 'Falhas no processamento', count: status.failed, color: '#f85149', icon: ExclamationTriangleIcon },
    ];

    return (
        <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0d1117', color: '#c9d1d9', fontFamily: 'Inter, system-ui, sans-serif' }}>
            <Sidebar />

            {/* MAIN */}
            <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
                <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <Link href="/">
                            <div style={{ width: '40px', height: '40px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
                                <ArrowLeftIcon style={{ width: '20px', height: '20px', color: '#8b949e' }} />
                            </div>
                        </Link>
                        <div>
                            <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', margin: 0 }}>Factory Watcher</h2>
                            <p style={{ fontSize: '12px', color: '#8b949e', margin: 0 }}>Monitoramento de pastas do pipeline</p>
                        </div>
                    </div>
                    <button
                        onClick={triggerScan}
                        disabled={scanning}
                        style={{
                            display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px',
                            borderRadius: '8px', backgroundColor: '#238636', border: 'none',
                            color: '#fff', fontSize: '14px', cursor: 'pointer', opacity: scanning ? 0.7 : 1
                        }}
                    >
                        <ArrowPathIcon style={{ width: '16px', height: '16px', animation: scanning ? 'spin 1s linear infinite' : 'none' }} />
                        {scanning ? 'Escaneando...' : 'Escanear Pastas'}
                    </button>
                </header>

                {/* Folder Status Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginBottom: '32px' }}>
                    {folders.map((folder, i) => (
                        <div key={i} style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: `${folder.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <FolderIcon style={{ width: '24px', height: '24px', color: folder.color }} />
                                    </div>
                                    <div>
                                        <h3 style={{ fontSize: '16px', color: '#fff', margin: 0, fontFamily: 'monospace' }}>{folder.name}</h3>
                                        <p style={{ fontSize: '12px', color: '#8b949e', margin: '4px 0 0' }}>{folder.description}</p>
                                    </div>
                                </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                <span style={{ fontSize: '48px', fontWeight: 'bold', color: folder.color }}>{folder.count}</span>
                                <span style={{ fontSize: '16px', color: '#8b949e' }}>arquivos</span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Pipeline Flow */}
                <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#fff', margin: '0 0 24px' }}>Pipeline de Processamento</h3>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        {['inputs/', 'processing/', 'done/'].map((step, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{
                                        width: '64px', height: '64px', borderRadius: '50%',
                                        backgroundColor: i === 0 ? 'rgba(210,153,34,0.15)' : i === 1 ? 'rgba(88,166,255,0.15)' : 'rgba(63,185,80,0.15)',
                                        display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 8px'
                                    }}>
                                        {i === 0 ? <ClockIcon style={{ width: '28px', height: '28px', color: '#d29922' }} /> :
                                            i === 1 ? <CubeTransparentIcon style={{ width: '28px', height: '28px', color: '#58a6ff' }} /> :
                                                <CheckCircleIcon style={{ width: '28px', height: '28px', color: '#3fb950' }} />}
                                    </div>
                                    <p style={{ fontSize: '12px', color: '#fff', margin: 0, fontFamily: 'monospace' }}>{step}</p>
                                    <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', margin: '4px 0 0' }}>
                                        {i === 0 ? status.queued : i === 1 ? status.processing : status.completed}
                                    </p>
                                </div>
                                {i < 2 && (
                                    <div style={{ width: '80px', height: '2px', backgroundColor: '#30363d', position: 'relative' }}>
                                        <PlayIcon style={{ width: '16px', height: '16px', color: '#8b949e', position: 'absolute', top: '-7px', left: '50%', transform: 'translateX(-50%)' }} />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {lastScan && (
                    <p style={{ fontSize: '12px', color: '#8b949e', marginTop: '16px', textAlign: 'center' }}>
                        Último scan: {lastScan}
                    </p>
                )}
            </main>

            <style jsx global>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        * { box-sizing: border-box; }
        body { margin: 0; }
      `}</style>
        </div>
    );
}
