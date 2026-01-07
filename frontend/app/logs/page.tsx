'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import {
    ArrowPathIcon, TrashIcon,
    CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XCircleIcon
} from '@heroicons/react/24/outline';

interface LogEntry {
    id: string;
    timestamp: string;
    level: 'info' | 'success' | 'warning' | 'error';
    message: string;
    source: string;
}

const API_BASE = 'http://localhost:8000/api/v1';

export default function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [stats, setStats] = useState({ info: 0, success: 0, warning: 0, error: 0, total: 0 });
    const [filter, setFilter] = useState<string>('all');
    const [autoScroll, setAutoScroll] = useState(true);
    const [loading, setLoading] = useState(true);
    const logContainerRef = useRef<HTMLDivElement>(null);

    const fetchLogs = useCallback(async () => {
        try {
            const [logsRes, statsRes] = await Promise.all([
                fetch(`${API_BASE}/logs/?limit=100${filter !== 'all' ? `&level=${filter}` : ''}`),
                fetch(`${API_BASE}/logs/stats`)
            ]);

            if (logsRes.ok) {
                const data = await logsRes.json();
                setLogs(data.logs);
            }

            if (statsRes.ok) {
                setStats(await statsRes.json());
            }
        } catch {
            // Backend offline - use mock data
            setLogs([
                { id: '1', timestamp: new Date().toLocaleTimeString('pt-BR'), level: 'warning', message: 'Backend offline - usando dados locais', source: 'frontend' }
            ]);
        }
        setLoading(false);
    }, [filter]);

    const clearLogs = async () => {
        try {
            await fetch(`${API_BASE}/logs/clear`, { method: 'DELETE' });
            fetchLogs();
        } catch {
            setLogs([]);
        }
    };

    const addTestLog = async (level: string) => {
        try {
            await fetch(`${API_BASE}/logs/add?level=${level}&message=Log de teste (${level})&source=frontend`, { method: 'POST' });
            fetchLogs();
        } catch { }
    };

    // Initial load + polling
    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 3000);
        return () => clearInterval(interval);
    }, [fetchLogs]);

    useEffect(() => {
        if (autoScroll && logContainerRef.current) {
            logContainerRef.current.scrollTop = 0;
        }
    }, [logs, autoScroll]);

    const getLevelIcon = (level: string) => {
        switch (level) {
            case 'success': return <CheckCircleIcon style={{ width: '16px', height: '16px', color: '#3fb950' }} />;
            case 'warning': return <ExclamationTriangleIcon style={{ width: '16px', height: '16px', color: '#d29922' }} />;
            case 'error': return <XCircleIcon style={{ width: '16px', height: '16px', color: '#f85149' }} />;
            default: return <InformationCircleIcon style={{ width: '16px', height: '16px', color: '#58a6ff' }} />;
        }
    };

    const getLevelColor = (level: string) => {
        switch (level) {
            case 'success': return '#3fb950';
            case 'warning': return '#d29922';
            case 'error': return '#f85149';
            default: return '#58a6ff';
        }
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0d1117', color: '#c9d1d9', fontFamily: 'Inter, system-ui, sans-serif' }}>
            <Sidebar />

            <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
                {/* Header */}
                <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                    <div>
                        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', margin: 0 }}>System Logs</h2>
                        <p style={{ fontSize: '12px', color: '#8b949e', margin: '4px 0 0' }}>Histórico de eventos do sistema • Atualizando a cada 3s</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button onClick={() => addTestLog('info')} style={{ padding: '8px 12px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #58a6ff', color: '#58a6ff', cursor: 'pointer', fontSize: '12px' }}>+ Info</button>
                        <button onClick={() => addTestLog('success')} style={{ padding: '8px 12px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #3fb950', color: '#3fb950', cursor: 'pointer', fontSize: '12px' }}>+ Success</button>
                        <button onClick={() => addTestLog('warning')} style={{ padding: '8px 12px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #d29922', color: '#d29922', cursor: 'pointer', fontSize: '12px' }}>+ Warning</button>
                        <button onClick={() => addTestLog('error')} style={{ padding: '8px 12px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #f85149', color: '#f85149', cursor: 'pointer', fontSize: '12px' }}>+ Error</button>
                        <button onClick={clearLogs} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #30363d', color: '#8b949e', cursor: 'pointer' }}>
                            <TrashIcon style={{ width: '16px', height: '16px' }} />
                        </button>
                        <button onClick={fetchLogs} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px', borderRadius: '8px', backgroundColor: '#238636', border: 'none', color: '#fff', cursor: 'pointer' }}>
                            <ArrowPathIcon style={{ width: '16px', height: '16px' }} />
                        </button>
                    </div>
                </header>

                {/* Filters */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                    {['all', 'info', 'success', 'warning', 'error'].map((level) => (
                        <button
                            key={level}
                            onClick={() => setFilter(level)}
                            style={{
                                padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                                backgroundColor: filter === level ? (level === 'all' ? '#58a6ff' : getLevelColor(level)) : '#1c2128',
                                color: filter === level ? '#fff' : '#8b949e',
                                fontSize: '12px', fontWeight: 500, textTransform: 'capitalize'
                            }}
                        >
                            {level === 'all' ? 'Todos' : level}
                        </button>
                    ))}
                    <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '12px', color: '#8b949e' }}>Auto-scroll</span>
                        <button
                            onClick={() => setAutoScroll(!autoScroll)}
                            style={{
                                width: '40px', height: '20px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                                backgroundColor: autoScroll ? '#238636' : '#30363d',
                                position: 'relative', transition: 'background-color 0.2s'
                            }}
                        >
                            <div style={{
                                width: '16px', height: '16px', borderRadius: '50%', backgroundColor: '#fff',
                                position: 'absolute', top: '2px', left: autoScroll ? '22px' : '2px',
                                transition: 'left 0.2s'
                            }} />
                        </button>
                    </div>
                </div>

                {/* Stats */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
                    {[
                        { label: 'Info', count: stats.info, color: '#58a6ff' },
                        { label: 'Success', count: stats.success, color: '#3fb950' },
                        { label: 'Warning', count: stats.warning, color: '#d29922' },
                        { label: 'Error', count: stats.error, color: '#f85149' },
                    ].map((stat) => (
                        <div key={stat.label} style={{ padding: '16px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #30363d', textAlign: 'center' }}>
                            <p style={{ fontSize: '24px', fontWeight: 'bold', color: stat.color, margin: 0 }}>{stat.count}</p>
                            <p style={{ fontSize: '12px', color: '#8b949e', margin: '4px 0 0' }}>{stat.label}</p>
                        </div>
                    ))}
                </div>

                {/* Log List */}
                <div
                    ref={logContainerRef}
                    style={{
                        backgroundColor: '#1c2128', borderRadius: '12px', border: '1px solid #30363d',
                        maxHeight: 'calc(100vh - 320px)', overflowY: 'auto'
                    }}
                >
                    {loading ? (
                        <div style={{ padding: '48px', textAlign: 'center' }}>
                            <p style={{ color: '#8b949e' }}>Carregando logs...</p>
                        </div>
                    ) : logs.length > 0 ? logs.map((log) => (
                        <div
                            key={log.id}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px',
                                borderBottom: '1px solid #30363d'
                            }}
                        >
                            {getLevelIcon(log.level)}
                            <span style={{ fontSize: '12px', color: '#8b949e', fontFamily: 'monospace', minWidth: '70px' }}>{log.timestamp}</span>
                            <span style={{
                                fontSize: '10px', padding: '2px 6px', borderRadius: '4px',
                                backgroundColor: `${getLevelColor(log.level)}20`, color: getLevelColor(log.level),
                                fontFamily: 'monospace', minWidth: '80px', textAlign: 'center'
                            }}>
                                {log.source}
                            </span>
                            <span style={{ fontSize: '13px', color: '#c9d1d9', flex: 1 }}>{log.message}</span>
                        </div>
                    )) : (
                        <div style={{ padding: '48px', textAlign: 'center' }}>
                            <p style={{ color: '#8b949e' }}>Nenhum log encontrado</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
