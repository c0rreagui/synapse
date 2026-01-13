"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '../components/Sidebar';
import { OracleInput } from '../components/oracle/OracleInput';
import { ViralScoreGauge } from '../components/oracle/ViralScoreGauge';
import { InsightCard } from '../components/oracle/InsightCard';
import { SentimentCard } from '../components/oracle/SentimentCard';
import LogTerminal from '../components/LogTerminal';
import { analyzeProfile, OracleAnalysis } from '../../services/oracleService';
import { useMood } from '../context/MoodContext';

// Tradução dos logs de carregamento
const TERMINAL_LINES = [
    "INICIALIZANDO NEURAL LINK...",
    "QUEBRANDO PROTOCOLOS DE SEGURANÇA...",
    "EXTRAINDO DATA-POINTS DO TIKTOK...",
    "CONECTANDO AO CÓRTEX DA GROQ...",
    "ANALISANDO PADRÕES VIRAIS...",
    "DECRIPTANDO FÓRMULA DE SUCESSO..."
];

export default function OraclePage() {
    const { setMood } = useMood();
    const [analysis, setAnalysis] = useState<OracleAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [terminalLog, setTerminalLog] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);

    // Logs exclusivos do Oráculo (pós-análise)
    const [oracleLogs, setOracleLogs] = useState<string[]>([]);

    const handleAnalyze = async (username: string) => {
        setLoading(true);
        setMood('PROCESSING'); // Trigger "Thinking" Aura
        setAnalysis(null);
        setError(null);
        setTerminalLog([]);
        setOracleLogs([]); // Limpa logs anteriores

        // Simulação de Terminal Hacker (Loading)
        let i = 0;
        const interval = setInterval(() => {
            if (i < TERMINAL_LINES.length) {
                setTerminalLog(prev => [...prev, TERMINAL_LINES[i]]);
                i++;
            } else {
                clearInterval(interval);
            }
        }, 1200);

        try {
            const start = Date.now();
            const result = await analyzeProfile(username);
            const duration = ((Date.now() - start) / 1000).toFixed(2);

            setAnalysis(result);

            // Popula o log exclusivo de confirmação
            setOracleLogs([
                `[${new Date().toLocaleTimeString()}] INICIANDO ANÁLISE PROFUNDA PARA ${username.toUpperCase()}`,
                `[${new Date().toLocaleTimeString()}] CONEXÃO ESTABELECIDA COM BACKEND (LAMA 3.3 70B)`,
                `[${new Date().toLocaleTimeString()}] PERFIL ANALISADO: ${result.profile}`,
                `[${new Date().toLocaleTimeString()}] MÉTRICAS COMPUTADAS COM SUCESSO`,
                `[${new Date().toLocaleTimeString()}] PARSE JSON: OK`,
                `[${new Date().toLocaleTimeString()}] COMPUTAÇÃO CONCLUÍDA EM ${duration}s`,
                `[${new Date().toLocaleTimeString()}] STATUS: ✅ SUCESSO`
            ]);

            setMood('SUCCESS');
            setTimeout(() => setMood('IDLE'), 3000); // Back to blue after 3s

        } catch (err: unknown) {
            const errorObj = err as any;
            setError(errorObj.response?.data?.detail || "Falha na Conexão com o Oráculo");
            setOracleLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ❌ ERRO CRÍTICO: ${errorObj.message}`]);
            setMood('ERROR');
        } finally {
            clearInterval(interval);
            setLoading(false);
        }
    };

    return (
        <div className="flex bg-[#050505] h-screen overflow-hidden font-sans text-gray-100 selection:bg-[#00f3ff] selection:text-black">
            <Sidebar />
            <main className="flex-1 overflow-y-auto relative h-full scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {/* Background Grid */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(18,18,18,0)_1px,transparent_1px),linear-gradient(90deg,rgba(18,18,18,0)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none z-0 opacity-20" />

                <div className="max-w-7xl mx-auto relative z-10 space-y-12 pb-20 p-8">

                    {/* Header */}
                    <header className="text-center space-y-4">
                        <motion.h1
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-6xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-200 to-gray-500 drop-shadow-[0_0_30px_rgba(255,255,255,0.1)]"
                        >
                            ORACLE <span className="text-[#00f3ff]">INTELLIGENCE</span>
                        </motion.h1>
                        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                            Motor de Estratégia Viral & Diagnóstico via IA
                        </p>
                    </header>

                    {/* Search Area */}
                    <section className="py-8">
                        <OracleInput onAnalyze={handleAnalyze} isLoading={loading} />
                    </section>

                    {/* Loading Terminal */}
                    <AnimatePresence>
                        {loading && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="bg-black border border-green-500/30 rounded-lg p-6 font-mono text-green-500 text-sm max-w-2xl mx-auto shadow-[0_0_50px_rgba(0,255,0,0.1)]"
                            >
                                {terminalLog.map((line, idx) => (
                                    <div key={idx} className="mb-2">
                                        <span className="mr-2 opacity-50">[{new Date().toLocaleTimeString()}]</span>
                                        <span className="typing-effect">{line}</span>
                                    </div>
                                ))}
                                <div className="animate-pulse">_</div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Error State */}
                    {error && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl text-center max-w-xl mx-auto"
                        >
                            ⚠️ FALHA NO SISTEMA: {error}
                        </motion.div>
                    )}

                    {/* Results Grid - Horizontal Scroll Layout */}
                    {analysis && !loading && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="space-y-8"
                        >
                            {/* Score & Profile (Fixed Top) */}
                            <div className="flex justify-center">
                                <div className="bg-[#0a0a0f]/60 backdrop-blur border border-white/5 rounded-2xl p-8 flex flex-col items-center max-w-2xl w-full shadow-[0_0_30px_rgba(0,243,255,0.1)] text-center">
                                    <ViralScoreGauge score={analysis.analysis.virality_score} />
                                    <h2 className="text-3xl font-bold mt-4 text-white">@{analysis.profile}</h2>

                                    {/* Profile Type Badge */}
                                    {analysis.analysis.profile_type && (
                                        <div className="flex gap-2 mt-2">
                                            <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider border ${analysis.analysis.profile_type.includes('Clips')
                                                ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
                                                : 'bg-blue-500/10 text-blue-500 border-blue-500/20'
                                                }`}>
                                                {analysis.analysis.profile_type}
                                            </span>
                                            {analysis.analysis.voice_authenticity && (
                                                <span className="px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-gray-800 text-gray-400 border border-gray-700">
                                                    Voice: {analysis.analysis.voice_authenticity}
                                                </span>
                                            )}
                                        </div>
                                    )}

                                    <div className="flex gap-2 mt-2 mb-4">
                                        {analysis.analysis.content_pillars.map((pillar, i) => (
                                            <span key={i} className="px-2 py-1 rounded-full bg-white/5 text-xs text-gray-300 border border-white/10 uppercase tracking-wider">
                                                {pillar}
                                            </span>
                                        ))}
                                    </div>
                                    <p className="text-gray-400 text-sm leading-relaxed">{analysis.analysis.summary}</p>

                                    {/* Quick Metrics */}
                                    <div className="grid grid-cols-4 gap-4 mt-6 w-full border-t border-white/5 pt-6">
                                        <div>
                                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Engajamento</div>
                                            <div className="text-[#00f3ff] font-bold text-lg">{analysis.analysis.engagement_quality}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Views/Média</div>
                                            <div className="text-[#00f3ff] font-bold text-lg">{analysis.analysis.performance_metrics.avg_views_estimate}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Vídeos Scan</div>
                                            <div className="text-[#00f3ff] font-bold text-lg">{analysis.analysis.performance_metrics.verified_video_count || 12}</div>
                                        </div>
                                        <div>
                                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Comentários</div>
                                            <div className="text-[#00f3ff] font-bold text-lg">{analysis.analysis.performance_metrics.comments_analyzed_count || 300}+</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Horizontal Scroll Container for Insights */}
                            <div className="relative">
                                {/* Gradient fade indicators */}
                                <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-[#050505] to-transparent z-10 pointer-events-none" />
                                <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-[#050505] to-transparent z-10 pointer-events-none" />

                                <div className="flex w-full overflow-x-auto gap-6 pb-6 px-4 snap-x snap-mandatory scrollbar-thin scrollbar-thumb-[#00f3ff]/20 scrollbar-track-transparent">

                                    {/* Card 0: Sentiment Pulse */}
                                    {analysis.analysis.sentiment_pulse && (
                                        <div className="min-w-[550px] snap-center">
                                            <SentimentCard
                                                data={analysis.analysis.sentiment_pulse}
                                                delay={0.1}
                                            />
                                        </div>
                                    )}

                                    {/* Card 1: Audience Persona */}
                                    <div className="min-w-[400px] snap-center">
                                        <motion.div
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.2 }}
                                            className="bg-[#0a0a0f]/60 backdrop-blur-md border border-purple-500/20 rounded-xl p-6 h-full hover:border-purple-500/40 transition-colors"
                                        >
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="text-purple-400 text-xl">👥</div>
                                                <h3 className="text-xl font-bold text-white tracking-wide">Persona do Público</h3>
                                            </div>
                                            <div className="space-y-4">
                                                <div>
                                                    <div className="text-xs text-gray-500 uppercase mb-1">Demografia</div>
                                                    <p className="text-purple-200">{analysis.analysis.audience_persona.demographics}</p>
                                                </div>
                                                <div>
                                                    <div className="text-xs text-gray-500 uppercase mb-1">Psicografia</div>
                                                    <p className="text-gray-400 text-sm">{analysis.analysis.audience_persona.psychographics}</p>
                                                </div>
                                                <div>
                                                    <div className="text-xs text-gray-500 uppercase mb-1">Dores Principais</div>
                                                    <div className="flex flex-wrap gap-2">
                                                        {analysis.analysis.audience_persona.pain_points.map((pain, i) => (
                                                            <span key={i} className="px-2 py-0.5 bg-purple-500/10 text-purple-300 text-xs rounded border border-purple-500/20">{pain}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    </div>

                                    {/* Card 2: Viral Hooks Strategy */}
                                    <div className="min-w-[400px] snap-center">
                                        <motion.div
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: 0.3 }}
                                            className="bg-[#0a0a0f]/60 backdrop-blur-md border border-white/10 rounded-xl p-6 h-full hover:border-[#00f3ff]/30 transition-colors"
                                        >
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="text-[#00f3ff] text-xl">⚡</div>
                                                <h3 className="text-xl font-bold text-white tracking-wide">Mecânica Viral</h3>
                                            </div>
                                            <ul className="space-y-4">
                                                {analysis.analysis.viral_hooks.map((hook, i) => (
                                                    <li key={i} className="bg-white/5 p-3 rounded-lg border border-white/5">
                                                        <div className="text-[#00f3ff] text-xs font-bold uppercase mb-1">{hook.type}</div>
                                                        <span className="text-gray-300 text-sm">{typeof hook === 'string' ? hook : hook.description}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </motion.div>
                                    </div>

                                    {/* Card 3: Content Gaps */}
                                    <div className="min-w-[350px] snap-center">
                                        <InsightCard
                                            title="Oportunidades (Gaps)"
                                            items={analysis.analysis.content_gaps}
                                            delay={0.4}
                                            icon="🎯"
                                        />
                                    </div>

                                    {/* Card 4: Next Video Suggestion */}
                                    <div className="min-w-[450px] snap-center">
                                        <motion.div
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 0.6 }}
                                            className="bg-gradient-to-r from-[#00f3ff]/10 to-blue-600/10 border border-[#00f3ff]/30 rounded-xl p-6 h-full relative overflow-hidden group hover:border-[#00f3ff]/60 transition-colors flex flex-col justify-between"
                                        >
                                            <div className="absolute inset-0 bg-[#00f3ff]/5 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                                            <div>
                                                <h3 className="text-[#00f3ff] font-bold tracking-widest text-xs uppercase mb-2">Sugestão de Próximo Vídeo</h3>
                                                <h4 className="text-2xl font-bold text-white mb-3">{analysis.analysis.suggested_next_video.title}</h4>
                                                <p className="text-gray-300 mb-4 text-sm leading-relaxed">{analysis.analysis.suggested_next_video.concept}</p>

                                                <div className="bg-[#00f3ff]/5 p-3 rounded border-l-2 border-[#00f3ff] mb-4">
                                                    <span className="text-[#00f3ff] text-xs font-bold uppercase block mb-1">Roteiro do Gancho (0-3s)</span>
                                                    <span className="text-gray-200 font-mono text-xs italic">&quot;{analysis.analysis.suggested_next_video.hook_script}&quot;</span>
                                                </div>
                                            </div>

                                            <div className="text-xs text-[#00f3ff]/70 font-mono border-t border-[#00f3ff]/20 pt-3 mt-2">
                                                MOTIVO: {analysis.analysis.suggested_next_video.reasoning}
                                            </div>
                                        </motion.div>
                                    </div>
                                </div>
                            </div>

                            {/* Exclusive Oracle Log (Proof of Work) */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.8 }}
                                className="max-w-4xl mx-auto pt-8 border-t border-white/5 pb-20"
                            >
                                <h3 className="text-xs font-mono text-gray-500 mb-2 uppercase tracking-widest">Registro de Execução Neural</h3>
                                <LogTerminal logs={oracleLogs} className="h-48" />
                            </motion.div>

                        </motion.div>
                    )}

                </div>
            </main>
        </div>
    );
}
