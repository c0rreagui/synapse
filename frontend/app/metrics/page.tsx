'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import { ArrowPathIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import clsx from 'clsx';

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

    // Simple bar chart renderer (using Tailwind)
    const renderBar = (value: number, maxValue: number, colorClass: string, label: string) => {
        const height = maxValue > 0 ? (value / maxValue) * 100 : 0;
        return (
            <div key={label} className="flex flex-col items-center gap-2 group">
                <div className="w-12 h-32 bg-black/40 rounded-t-lg flex items-end overflow-hidden relative border-b border-white/5">
                    <div
                        className={clsx("w-full transition-all duration-500 ease-out flex items-start justify-center pt-2 relative opacity-80 group-hover:opacity-100", colorClass)}
                        style={{ height: `${height}%` }}
                    >
                        {height > 10 && <span className="text-[10px] text-white/90 font-bold">{value}</span>}
                    </div>
                </div>
                {height <= 10 && <span className={clsx("text-lg font-bold transition-colors", colorClass.replace('bg-', 'text-'))}>{value}</span>}
                <span className="text-[10px] text-gray-500 uppercase font-mono tracking-wider">{label}</span>
            </div>
        );
    };

    // Mini sparkline for history
    const renderSparkline = (data: number[], color: string) => {
        if (data.length < 2) return null;
        const max = Math.max(...data, 1);
        const points = data.map((v, i) => `${(i / (data.length - 1)) * 100},${100 - (v / max) * 80}`).join(' ');
        return (
            <div className="h-10 w-full opacity-60">
                <svg viewBox="0 0 100 100" className="w-full h-full overflow-visible" preserveAspectRatio="none">
                    <polyline fill="none" stroke={color} strokeWidth="2" points={points} vectorEffect="non-scaling-stroke" />
                    {data.map((v, i) => (
                        <circle
                            key={i}
                            cx={(i / (data.length - 1)) * 100}
                            cy={100 - (v / max) * 80}
                            r="1.5"
                            fill={color}
                            className="opacity-0 hover:opacity-100 transition-opacity"
                        />
                    ))}
                </svg>
            </div>
        );
    };

    return (
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans selection:bg-synapse-primary selection:text-white">
            <Sidebar />

            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern">
                {/* Header */}
                <header className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-white m-0">Métricas do Sistema</h2>
                        <p className="text-sm text-gray-500 m-0 mt-1 font-mono">Última atualização: {lastUpdate}</p>
                    </div>
                    <NeonButton onClick={fetchData} className="flex items-center gap-2">
                        <ArrowPathIcon className="w-4 h-4" />
                        Atualizar
                    </NeonButton>
                </header>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <StitchCard className="p-6">
                        <p className="text-xs text-synapse-cyan m-0 mb-2 uppercase font-bold tracking-wider">Total Processado</p>
                        <p className="text-4xl font-bold text-white m-0 mb-3">{total}</p>
                        <div className="mt-auto pt-2 border-t border-white/5">{renderSparkline(history.map(h => h.completed + h.failed), '#06b6d4')}</div>
                    </StitchCard>

                    <StitchCard className="p-6">
                        <p className="text-xs text-synapse-emerald m-0 mb-2 uppercase font-bold tracking-wider">Taxa de Sucesso</p>
                        <div className="flex items-center gap-2 mb-3">
                            <p className="text-4xl font-bold text-synapse-emerald m-0">{successRate}%</p>
                            <ArrowTrendingUpIcon className="w-6 h-6 text-synapse-emerald" />
                        </div>
                        <div className="mt-auto pt-2 border-t border-white/5">{renderSparkline(history.map(h => h.completed), '#10b981')}</div>
                    </StitchCard>

                    <StitchCard className="p-6">
                        <p className="text-xs text-red-500 m-0 mb-2 uppercase font-bold tracking-wider">Taxa de Falha</p>
                        <div className="flex items-center gap-2 mb-3">
                            <p className="text-4xl font-bold text-red-500 m-0">{failureRate}%</p>
                            {parseFloat(failureRate) > 10 && <ArrowTrendingDownIcon className="w-6 h-6 text-red-500" />}
                        </div>
                        <div className="mt-auto pt-2 border-t border-white/5">{renderSparkline(history.map(h => h.failed), '#ef4444')}</div>
                    </StitchCard>

                    <StitchCard className="p-6">
                        <p className="text-xs text-synapse-purple m-0 mb-2 uppercase font-bold tracking-wider">Em Processamento</p>
                        <p className="text-4xl font-bold text-synapse-purple m-0 mb-3">{status.processing}</p>
                        <div className="mt-auto pt-2 border-t border-white/5">{renderSparkline(history.map(h => h.processing), '#8b5cf6')}</div>
                    </StitchCard>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Bar Chart */}
                    <StitchCard className="p-6">
                        <h3 className="text-base font-bold text-white m-0 mb-6 flex items-center gap-2">
                            <span className="w-1 h-4 bg-synapse-primary rounded-full"></span>
                            Distribuição do Pipeline
                        </h3>
                        <div className="flex justify-around items-end h-64 px-4 bg-black/20 rounded-xl border border-white/5 pt-8 pb-2">
                            {renderBar(status.queued, Math.max(status.queued, status.processing, status.completed, status.failed, 1), 'bg-synapse-amber', 'Fila')}
                            {renderBar(status.processing, Math.max(status.queued, status.processing, status.completed, status.failed, 1), 'bg-synapse-cyan', 'Proc.')}
                            {renderBar(status.completed, Math.max(status.queued, status.processing, status.completed, status.failed, 1), 'bg-synapse-emerald', 'OK')}
                            {renderBar(status.failed, Math.max(status.queued, status.processing, status.completed, status.failed, 1), 'bg-red-500', 'Erro')}
                        </div>
                    </StitchCard>

                    {/* Donut Chart Approximation */}
                    <StitchCard className="p-6">
                        <h3 className="text-base font-bold text-white m-0 mb-6 flex items-center gap-2">
                            <span className="w-1 h-4 bg-synapse-emerald rounded-full"></span>
                            Status Geral
                        </h3>
                        <div className="flex items-center justify-center gap-8 h-64 bg-black/20 rounded-xl border border-white/5">
                            <div className="relative w-32 h-32">
                                <svg viewBox="0 0 36 36" className="w-32 h-32 rotate-[-90deg]">
                                    <circle cx="18" cy="18" r="15.9" fill="none" stroke="#161b22" strokeWidth="3" />
                                    <circle
                                        cx="18" cy="18" r="15.9" fill="none" stroke="#34d399" strokeWidth="3"
                                        strokeDasharray={`${parseFloat(successRate)} 100`}
                                        strokeLinecap="round"
                                        className="transition-all duration-1000 ease-out"
                                    />
                                </svg>
                                <div className="absolute inset-0 flex items-center justify-center flex-col">
                                    <span className="text-2xl font-bold text-synapse-emerald">{successRate}%</span>
                                    <span className="text-[10px] text-gray-500 uppercase">Sucesso</span>
                                </div>
                            </div>
                            <div className="space-y-3">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-synapse-emerald shadow-[0_0_10px_rgba(16,185,129,0.4)]" />
                                    <span className="text-sm text-gray-300">Concluídos: <span className="text-white font-bold">{status.completed}</span></span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.4)]" />
                                    <span className="text-sm text-gray-300">Falhas: <span className="text-white font-bold">{status.failed}</span></span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-synapse-cyan shadow-[0_0_10px_rgba(6,182,212,0.4)]" />
                                    <span className="text-sm text-gray-300">Processando: <span className="text-white font-bold">{status.processing}</span></span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full bg-synapse-amber shadow-[0_0_10px_rgba(245,158,11,0.4)]" />
                                    <span className="text-sm text-gray-300">Na fila: <span className="text-white font-bold">{status.queued}</span></span>
                                </div>
                            </div>
                        </div>
                    </StitchCard>
                </div>
            </main>
        </div>
    );
}
