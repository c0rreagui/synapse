'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import { ArrowPathIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';

interface IngestionStatus { queued: number; processing: number; completed: number; failed: number; }

const API_BASE = 'http://localhost:8000/api/v1';

export default function MetricsPage() {
    const [status, setStatus] = useState<IngestionStatus>({ queued: 0, processing: 0, completed: 0, failed: 0 });
    const [history, setHistory] = useState<IngestionStatus[]>([]);
    const [lastUpdate, setLastUpdate] = useState('');

    const fetchData = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/ingest/status`);
            if (res.ok) {
                const data = await res.json();
                setStatus(data);
                setHistory(prev => [...prev.slice(-11), data]); // Keep last 12 data points
            }
        } catch { }
        setLastUpdate(new Date().toLocaleTimeString('pt-BR'));
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const total = status.queued + status.processing + status.completed + status.failed;
    const successRate = total > 0 ? ((status.completed / total) * 100).toFixed(1) : '0';
    const failureRate = total > 0 ? ((status.failed / total) * 100).toFixed(1) : '0';

    // Simple bar chart renderer
    const renderBar = (value: number, maxValue: number, color: string, label: string) => {
        const height = maxValue > 0 ? (value / maxValue) * 100 : 0;
        return (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '40px', height: '120px', backgroundColor: '#161b22', borderRadius: '4px', display: 'flex', alignItems: 'flex-end', overflow: 'hidden' }}>
                    <div style={{ width: '100%', height: `${height}%`, backgroundColor: color, borderRadius: '4px 4px 0 0', transition: 'height 0.3s ease' }} />
                </div>
                <span style={{ fontSize: '20px', fontWeight: 'bold', color }}>{value}</span>
                <span style={{ fontSize: '10px', color: '#8b949e', textTransform: 'uppercase' }}>{label}</span>
            </div>
        );
    };

    // Mini sparkline for history
    const renderSparkline = (data: number[], color: string) => {
        if (data.length < 2) return null;
        const max = Math.max(...data, 1);
        const points = data.map((v, i) => `${(i / (data.length - 1)) * 100},${100 - (v / max) * 80}`).join(' ');
        return (
            <svg viewBox="0 0 100 100" style={{ width: '100%', height: '40px' }} preserveAspectRatio="none">
                <polyline fill="none" stroke={color} strokeWidth="2" points={points} />
            </svg>
        );
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0d1117', color: '#c9d1d9', fontFamily: 'Inter, system-ui, sans-serif' }}>
            <Sidebar />

            <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
                {/* Header */}
                <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
                    <div>
                        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', margin: 0 }}>Métricas do Sistema</h2>
                        <p style={{ fontSize: '12px', color: '#8b949e', margin: '4px 0 0' }}>Última atualização: {lastUpdate}</p>
                    </div>
                    <button onClick={fetchData} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', borderRadius: '8px', backgroundColor: '#238636', border: 'none', color: '#fff', cursor: 'pointer' }}>
                        <ArrowPathIcon style={{ width: '16px', height: '16px' }} />
                        Atualizar
                    </button>
                </header>

                {/* KPI Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
                    <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                        <p style={{ fontSize: '12px', color: '#8b949e', margin: '0 0 8px' }}>TOTAL PROCESSADO</p>
                        <p style={{ fontSize: '36px', fontWeight: 'bold', color: '#fff', margin: 0 }}>{total}</p>
                        <div style={{ marginTop: '12px' }}>{renderSparkline(history.map(h => h.completed + h.failed), '#58a6ff')}</div>
                    </div>

                    <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                        <p style={{ fontSize: '12px', color: '#8b949e', margin: '0 0 8px' }}>TAXA DE SUCESSO</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <p style={{ fontSize: '36px', fontWeight: 'bold', color: '#3fb950', margin: 0 }}>{successRate}%</p>
                            <ArrowTrendingUpIcon style={{ width: '24px', height: '24px', color: '#3fb950' }} />
                        </div>
                        <div style={{ marginTop: '12px' }}>{renderSparkline(history.map(h => h.completed), '#3fb950')}</div>
                    </div>

                    <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                        <p style={{ fontSize: '12px', color: '#8b949e', margin: '0 0 8px' }}>TAXA DE FALHA</p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <p style={{ fontSize: '36px', fontWeight: 'bold', color: '#f85149', margin: 0 }}>{failureRate}%</p>
                            {parseFloat(failureRate) > 10 && <ArrowTrendingDownIcon style={{ width: '24px', height: '24px', color: '#f85149' }} />}
                        </div>
                        <div style={{ marginTop: '12px' }}>{renderSparkline(history.map(h => h.failed), '#f85149')}</div>
                    </div>

                    <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                        <p style={{ fontSize: '12px', color: '#8b949e', margin: '0 0 8px' }}>EM PROCESSAMENTO</p>
                        <p style={{ fontSize: '36px', fontWeight: 'bold', color: '#58a6ff', margin: 0 }}>{status.processing}</p>
                        <div style={{ marginTop: '12px' }}>{renderSparkline(history.map(h => h.processing), '#58a6ff')}</div>
                    </div>
                </div>

                {/* Charts Row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                    {/* Bar Chart */}
                    <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                        <h3 style={{ fontSize: '16px', color: '#fff', margin: '0 0 24px' }}>Distribuição do Pipeline</h3>
                        <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'flex-end' }}>
                            {renderBar(status.queued, Math.max(status.queued, status.processing, status.completed, status.failed, 1), '#d29922', 'Fila')}
                            {renderBar(status.processing, Math.max(status.queued, status.processing, status.completed, status.failed, 1), '#58a6ff', 'Proc.')}
                            {renderBar(status.completed, Math.max(status.queued, status.processing, status.completed, status.failed, 1), '#3fb950', 'OK')}
                            {renderBar(status.failed, Math.max(status.queued, status.processing, status.completed, status.failed, 1), '#f85149', 'Erro')}
                        </div>
                    </div>

                    {/* Donut Chart Approximation */}
                    <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                        <h3 style={{ fontSize: '16px', color: '#fff', margin: '0 0 24px' }}>Status Geral</h3>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '32px' }}>
                            <div style={{ position: 'relative', width: '120px', height: '120px' }}>
                                <svg viewBox="0 0 36 36" style={{ width: '120px', height: '120px', transform: 'rotate(-90deg)' }}>
                                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="#161b22" strokeWidth="3" />
                                    <circle
                                        cx="18" cy="18" r="15.9" fill="none" stroke="#3fb950" strokeWidth="3"
                                        strokeDasharray={`${parseFloat(successRate)} 100`}
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#3fb950' }}>{successRate}%</span>
                                </div>
                            </div>
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                    <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#3fb950' }} />
                                    <span style={{ fontSize: '12px', color: '#c9d1d9' }}>Concluídos: {status.completed}</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                    <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#f85149' }} />
                                    <span style={{ fontSize: '12px', color: '#c9d1d9' }}>Falhas: {status.failed}</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                    <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#58a6ff' }} />
                                    <span style={{ fontSize: '12px', color: '#c9d1d9' }}>Processando: {status.processing}</span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <div style={{ width: '12px', height: '12px', borderRadius: '2px', backgroundColor: '#d29922' }} />
                                    <span style={{ fontSize: '12px', color: '#c9d1d9' }}>Na fila: {status.queued}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
