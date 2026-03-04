'use client';

import React, { useState, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import axios from 'axios';
import { getApiUrl } from '../utils/apiClient';
import { RetentionChart } from '../components/oracle/RetentionChart';
import { MetricComparisonChart } from '../components/oracle/MetricComparisonChart';

interface AnalysisResult {
    profile: string;
    analysis: Record<string, unknown>;
    raw_data: Record<string, unknown>;
    timestamp: string;
}

interface LogEntry {
    text: string;
    type: 'info' | 'error' | 'success' | 'warn';
    time: string;
}

export default function OraclePage() {
    const [prompt, setPrompt] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [phase, setPhase] = useState<'idle' | 'scanning' | 'done'>('idle');
    const logRef = useRef<HTMLDivElement>(null);
    const API = getApiUrl();

    const addLog = (text: string, type: LogEntry['type'] = 'info') => {
        const time = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        setLogs(prev => [...prev, { text, type, time }]);
    };

    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [logs]);

    const handleAnalyze = async () => {
        if (!prompt.trim()) return;

        const username = prompt.trim().replace('@', '');
        setIsProcessing(true);
        setPhase('scanning');
        setResult(null);
        setLogs([]);

        addLog(`Inicializando motor Oracle para @${username}...`, 'info');
        addLog('Sense Faculty: Acionando web scraper TikTok...', 'info');

        try {
            const res = await axios.post(`${API}/api/v1/oracle/analyze?username=${encodeURIComponent(username)}`);

            addLog('Sense Faculty: Dados coletados com sucesso.', 'success');
            addLog('Mind Faculty: Processando análise estratégica via Gemini...', 'info');

            const data = res.data as AnalysisResult;
            setResult(data);

            const analysis = data.analysis || {};
            const rawData = data.raw_data || {};

            // Log key insights
            if (rawData && typeof rawData === 'object' && 'followers' in rawData) {
                addLog(`Perfil: ${rawData.followers} seguidores | ${rawData.likes || '?'} curtidas`, 'success');
            }
            if (analysis && typeof analysis === 'object' && 'best_times' in analysis) {
                const times = analysis.best_times as string[];
                addLog(`Melhores horários: ${times.slice(0, 3).join(', ')}`, 'success');
            }
            if (analysis && typeof analysis === 'object' && 'content_strategy' in analysis) {
                addLog('Estratégia de conteúdo gerada.', 'success');
            }

            addLog('Oracle: Varredura completa. Widgets renderizados.', 'success');
            setPhase('done');
            toast.success(`Análise de @${username} concluída!`);

        } catch (err: unknown) {
            const errMsg = err instanceof Error ? err.message : 'Erro desconhecido';
            addLog(`FALHA: ${errMsg}`, 'error');
            setPhase('idle');
            toast.error(`Falha ao analisar @${username}`);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && prompt.trim() && !isProcessing) {
            handleAnalyze();
        }
    };

    const getLogColor = (type: LogEntry['type']) => {
        switch (type) {
            case 'error': return 'text-magenta-500';
            case 'success': return 'text-emerald-400';
            case 'warn': return 'text-yellow-400';
            default: return 'text-cyan-400';
        }
    };

    const getLogTag = (type: LogEntry['type']) => {
        switch (type) {
            case 'error': return '[ERR]';
            case 'success': return '[OK]';
            case 'warn': return '[WARN]';
            default: return '[SYS]';
        }
    };

    // Extract data for charts from result
    const retentionData = result?.analysis && typeof result.analysis === 'object' && 'retention_curve' in result.analysis
        ? result.analysis.retention_curve as { second: number; retention_rate: number }[]
        : undefined;

    const rawVideos = result?.raw_data && typeof result.raw_data === 'object' && 'videos' in result.raw_data
        ? result.raw_data.videos as { views: string }[]
        : undefined;

    // Build strategy summary from analysis
    const strategy = result?.analysis || {};
    const bestTimes = 'best_times' in strategy ? (strategy.best_times as string[]) : [];
    const contentStrategy = 'content_strategy' in strategy ? (strategy.content_strategy as string) : '';
    const hashtags = 'recommended_hashtags' in strategy ? (strategy.recommended_hashtags as string[]) : [];

    return (
        <div className="relative z-10 flex flex-col h-full grow w-full mx-auto min-h-[calc(100vh-88px)] bg-transparent text-slate-100 font-display selection:bg-cyan-400/30 selection:text-white">
            {/* Background elements */}
            <div className="fixed inset-0 z-0 pointer-events-none bg-[radial-gradient(circle_at_50%_40%,#1e1b4b_0%,#0f172a_40%,#020204_100%)]">
                <div className="absolute top-[-20%] left-[-10%] w-[80%] h-[80%] nebula-cloud opacity-40 mix-blend-screen animate-pulse duration-[10000ms]"></div>
                <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] nebula-cloud opacity-30 mix-blend-screen animate-pulse duration-[12000ms]" style={{ background: 'radial-gradient(circle at 50% 50%, rgba(7, 182, 213, 0.06), transparent 70%)' }}></div>
                <div className="absolute inset-0 star-field opacity-60"></div>
                <div className="absolute inset-0 star-field opacity-30 scale-150 transform rotate-12"></div>
                <div className="absolute inset-0 opacity-[0.07] mix-blend-overlay"></div>
                <div className="absolute inset-0 scan-line pointer-events-none"></div>
            </div>

            <main className="flex flex-col flex-1 relative overflow-y-auto z-10 w-full">

                {/* Hero / Input Section */}
                <div className={`relative w-full flex items-center justify-center transition-all duration-700 ${phase === 'idle' ? 'min-h-[700px]' : 'min-h-[250px] py-8'}`}>
                    {/* Orbit rings - only show fully in idle */}
                    {phase === 'idle' && (
                        <div className="absolute w-[650px] h-[650px] transform-style-3d orbit-container pointer-events-none opacity-80">
                            <div className="absolute inset-0 border border-cyan-400/10 rounded-full transform rotate-x-[75deg] shadow-[0_0_15px_rgba(7,182,213,0.05)]"></div>
                            <div className="absolute inset-[15%] border border-indigo-500/15 rounded-full transform rotate-x-[75deg] rotate-y-[45deg]"></div>
                            <div className="absolute inset-[30%] border border-white/5 rounded-full transform rotate-x-[75deg] rotate-y-[-45deg] border-dashed"></div>

                            <div className="absolute top-[10%] left-[50%] transform -translate-x-1/2 translate-z-[240px] orbit-item">
                                <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group">
                                    <span className="size-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(7,182,213,0.8)]"></span>
                                    <span className="text-[10px] font-mono text-cyan-400/90 tracking-wider group-hover:text-white transition-colors uppercase drop-shadow-[0_0_5px_rgba(7,182,213,0.4)]">Aprendizado_Profundo</span>
                                </div>
                            </div>
                            <div className="absolute top-[50%] right-[0%] transform translate-x-1/2 translate-z-[120px] orbit-item">
                                <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group">
                                    <span className="size-1.5 bg-indigo-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
                                    <span className="text-[10px] font-mono text-indigo-400/90 tracking-wider group-hover:text-white transition-colors uppercase drop-shadow-[0_0_5px_rgba(99,102,241,0.4)]">Rede_Neural</span>
                                </div>
                            </div>
                            <div className="absolute bottom-[20%] left-[20%] transform translate-z-[-180px] orbit-item">
                                <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group border-white/10">
                                    <span className="size-1.5 bg-slate-400 rounded-full"></span>
                                    <span className="text-[10px] font-mono text-slate-300 tracking-wider uppercase">Auto_Escala</span>
                                </div>
                            </div>
                            <div className="absolute bottom-[10%] right-[40%] transform translate-z-[200px] orbit-item">
                                <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group">
                                    <span className="size-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(7,182,213,0.8)]"></span>
                                    <span className="text-[10px] font-mono text-cyan-400/90 tracking-wider uppercase drop-shadow-[0_0_5px_rgba(7,182,213,0.4)]">Singularidade</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="relative z-20 group w-full max-w-[500px] flex flex-col items-center gap-8">
                        <div className={`relative ${phase === 'idle' ? 'size-56 md:size-72' : 'size-32'} flex items-center justify-center transition-all duration-700`}>
                            <div className="absolute inset-4 rounded-full z-10 singularity-core volumetric-glow border border-cyan-400/20 overflow-hidden">
                                <div className="absolute inset-0 internal-energy opacity-50 mix-blend-screen"></div>
                                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-400/5 to-transparent animate-pulse"></div>
                            </div>
                            <div className={`absolute inset-0 rounded-full border border-cyan-400/10 border-t-cyan-400/40 ${isProcessing ? 'animate-spin' : ''}`} style={{ animationDuration: '2s' }}></div>
                            <div className="absolute inset-[-15px] rounded-full border border-indigo-500/10 border-b-indigo-500/30 animate-[spin_12s_linear_infinite_reverse]"></div>
                            <div className="absolute inset-[-30px] rounded-full border border-dashed border-white/5 animate-[spin_20s_linear_infinite]"></div>
                            {phase === 'idle' && <div className="absolute inset-[-50px] bg-cyan-400/5 rounded-full blur-[60px] animate-pulse"></div>}

                            <div className="relative z-20 w-full h-full flex items-center justify-center">
                                <input
                                    autoFocus
                                    className="bg-transparent border-none text-center text-white text-xl font-medium placeholder:text-cyan-400/30 focus:ring-0 w-[80%] drop-shadow-[0_0_10px_rgba(255,255,255,0.2)] tracking-wide outline-none disabled:opacity-50"
                                    placeholder={isProcessing ? "PROCESSANDO..." : "INICIAR SEQUÊNCIA..."}
                                    type="text"
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    disabled={isProcessing}
                                />
                            </div>
                        </div>

                        {phase === 'idle' && (
                            <div className="text-center space-y-3 opacity-0 group-focus-within:opacity-100 transition-opacity duration-700">
                                <p className="text-cyan-400 tracking-[0.3em] text-[10px] font-mono soft-pulse uppercase border-b border-cyan-400/20 pb-1 inline-block">Aguardando Sequência de Entrada</p>
                                <p className="text-slate-500 text-xs font-mono tracking-wide">Digite um <span className="text-white">@username</span> e pressione <span className="text-white">ENTER</span></p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Log Terminal + Results */}
                {phase !== 'idle' && (
                    <div className="w-full max-w-7xl mx-auto px-6 pb-12 space-y-6">

                        {/* Log Terminal */}
                        <div className="border border-white/10 bg-black/60 backdrop-blur overflow-hidden">
                            <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-black/80">
                                <div className="flex items-center gap-2">
                                    <span className={`size-2 rounded-full ${isProcessing ? 'bg-cyan-400 animate-pulse' : 'bg-emerald-400'}`}></span>
                                    <span className="text-[10px] font-mono text-slate-400 tracking-wider uppercase">Oracle Terminal</span>
                                </div>
                                <span className="text-[9px] font-mono text-slate-600">
                                    {isProcessing ? 'EXECUTANDO...' : phase === 'done' ? 'COMPLETO' : 'IDLE'}
                                </span>
                            </div>
                            <div ref={logRef} className="max-h-[200px] overflow-y-auto p-4 font-mono text-xs space-y-0.5">
                                {logs.map((log, idx) => (
                                    <div key={idx} className="flex gap-3 items-start">
                                        <span className="text-slate-600 w-16 shrink-0">{log.time}</span>
                                        <span className={`${getLogColor(log.type)} font-bold w-12 shrink-0`}>{getLogTag(log.type)}</span>
                                        <span className={`${log.type === 'error' ? 'text-red-300' : 'text-slate-300'}`}>{log.text}</span>
                                    </div>
                                ))}
                                {isProcessing && (
                                    <div className="flex gap-3 items-start">
                                        <span className="text-slate-600 w-16 shrink-0"></span>
                                        <span className="text-cyan-400 animate-pulse">▊</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Analytics Widgets */}
                        {phase === 'done' && result && (
                            <div className="space-y-6 animate-in fade-in duration-700">

                                {/* Profile Summary Banner */}
                                <div className="border border-white/10 bg-black/40 backdrop-blur p-6 flex flex-col md:flex-row gap-6 items-start">
                                    <div className="flex-1">
                                        <h2 className="text-2xl font-display tracking-wider text-white mb-1">
                                            @{result.profile}
                                        </h2>
                                        <p className="text-slate-500 text-xs font-mono tracking-wider uppercase mb-4">Análise Estratégica Completa</p>

                                        {/* Best Times */}
                                        {bestTimes.length > 0 && (
                                            <div className="mb-3">
                                                <p className="text-[10px] text-cyan-400 font-mono tracking-widest uppercase mb-1">Melhores Horários</p>
                                                <div className="flex gap-2 flex-wrap">
                                                    {bestTimes.map((t, i) => (
                                                        <span key={i} className="px-2 py-0.5 border border-cyan-400/20 bg-cyan-400/5 text-cyan-400 text-xs font-mono">{t}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Hashtags */}
                                        {hashtags.length > 0 && (
                                            <div className="mb-3">
                                                <p className="text-[10px] text-indigo-400 font-mono tracking-widest uppercase mb-1">Hashtags Recomendadas</p>
                                                <div className="flex gap-2 flex-wrap">
                                                    {hashtags.slice(0, 8).map((h, i) => (
                                                        <span key={i} className="px-2 py-0.5 border border-indigo-400/20 bg-indigo-400/5 text-indigo-300 text-xs font-mono">#{h}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* KPIs from raw_data */}
                                    {result.raw_data && (
                                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                            {['followers' in result.raw_data && { label: 'Seguidores', value: result.raw_data.followers },
                                            'likes' in result.raw_data && { label: 'Curtidas', value: result.raw_data.likes },
                                            'following' in result.raw_data && { label: 'Seguindo', value: result.raw_data.following },
                                            rawVideos && { label: 'Vídeos', value: rawVideos.length },
                                            ].filter(Boolean).map((kpi, i) => {
                                                const k = kpi as { label: string; value: unknown };
                                                return (
                                                    <div key={i} className="border border-white/5 bg-black/30 p-3 text-center">
                                                        <p className="text-[9px] text-slate-500 font-mono uppercase tracking-widest mb-1">{k.label}</p>
                                                        <p className="text-xl font-display text-white tracking-wider">{String(k.value)}</p>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>

                                {/* Charts Grid */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                    <RetentionChart data={retentionData} />
                                    <MetricComparisonChart />
                                </div>

                                {/* Strategy Text */}
                                {contentStrategy && (
                                    <div className="border border-white/10 bg-black/40 backdrop-blur p-6">
                                        <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2 mb-4">
                                            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]"></span>
                                            Estratégia de Conteúdo (Gemini)
                                        </h3>
                                        <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap font-mono">
                                            {contentStrategy}
                                        </div>
                                    </div>
                                )}

                                {/* New Analysis Button */}
                                <div className="flex justify-center pt-4 pb-8">
                                    <button
                                        onClick={() => { setPhase('idle'); setResult(null); setLogs([]); setPrompt(''); }}
                                        className="px-6 py-2 border border-cyan-400/30 text-cyan-400 hover:bg-cyan-400/10 text-xs font-mono uppercase tracking-widest transition-all"
                                    >
                                        Nova Análise
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Matrix rain - only idle */}
                {phase === 'idle' && (
                    <div className="absolute inset-0 pointer-events-none z-0 flex justify-between px-10 md:px-32 overflow-hidden opacity-10">
                        <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '2.5s', animationDelay: '0.2s' }}></div>
                        <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '3.1s', animationDelay: '1.5s' }}></div>
                        <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '2.8s', animationDelay: '0.8s' }}></div>
                        <div className="w-[1px] h-full matrix-rain hidden md:block" style={{ animationDuration: '3.5s', animationDelay: '2.1s' }}></div>
                        <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '2.2s', animationDelay: '0.5s' }}></div>
                        <div className="w-[1px] h-full matrix-rain hidden md:block" style={{ animationDuration: '4s', animationDelay: '1.2s' }}></div>
                    </div>
                )}
            </main>
        </div>
    );
}
