"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '../components/Sidebar';
import { OracleInput } from '../components/oracle/OracleInput';
import { ViralScoreGauge } from '../components/oracle/ViralScoreGauge';
import { InsightCard } from '../components/oracle/InsightCard';
import { SentimentCard } from '../components/oracle/SentimentCard';
import LogTerminal from '../components/LogTerminal';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import { analyzeProfile, OracleAnalysis } from '../../services/oracleService';
import { useMood } from '../context/MoodContext';
import { TikTokProfile } from '../types';
import { toast } from 'sonner';
import clsx from 'clsx';
import {
    CubeTransparentIcon, SparklesIcon, MagnifyingGlassIcon,
    ArrowPathIcon, EyeIcon, CheckIcon, ClipboardIcon
} from '@heroicons/react/24/outline';
import { StatCard } from '../components/analytics/StatCard';
import { PerformanceChart } from '../components/analytics/PerformanceChart';
import { ChartBarIcon, HeartIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/solid';
import { RetentionChart } from '../components/oracle/RetentionChart';
import { EngagementHeatmap } from '../components/oracle/EngagementHeatmap';
import { PatternCard, PatternType } from '../components/oracle/PatternCard';
import { MetricComparisonChart } from '../components/oracle/MetricComparisonChart';
import axios from 'axios';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace('localhost', '127.0.0.1');

// Terminal loading lines
const TERMINAL_LINES = [
    "INICIALIZANDO NEURAL LINK...",
    "QUEBRANDO PROTOCOLOS DE SEGURANÇA...",
    "EXTRAINDO DATA-POINTS DO TIKTOK...",
    "CONECTANDO AO CÓRTEX DO ORACLE...",
    "ANALISANDO PADRÕES VIRAIS...",
    "DECRIPTANDO FÓRMULA DE SUCESSO..."
];

type TabType = 'INTELLIGENCE' | 'AUDIT' | 'SPY' | 'DISCOVERY' | 'DEEP_ANALYTICS';

// Define Data Type based on backend response
interface AnalyticsData {
    profile_id: string;
    username: string;
    summary: {
        followers: number;
        total_likes: number;
        total_views: number;
        posts_analyzed: number;
        avg_engagement: number;
    };
    history: {
        date: string;
        views: number;
        likes: number;
        engagement: number;
    }[];
    best_times: any[];
    // [SYN-38] Enhanced Analytics Field Mapping
    heatmap_data: { hour: number; intensity: number }[];
    retention_curve: { time: number; retention: number }[];
    comparison: {
        period: string;
        current: { views: number; likes: number; count: number };
        previous: { views: number; likes: number; count: number };
        growth: { views: number; likes: number };
    };
    patterns: {
        type: PatternType;
        title: string;
        description: string;
        confidence: number;
        impact: 'HIGH' | 'MEDIUM' | 'LOW';
    }[];
}

export default function OraclePage() {
    const { setMood } = useMood();
    const [activeTab, setActiveTab] = useState<TabType>('INTELLIGENCE');

    // Intelligence State
    const [analysis, setAnalysis] = useState<OracleAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [terminalLog, setTerminalLog] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [oracleLogs, setOracleLogs] = useState<string[]>([]);

    // Audit State  
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
    const [selectedProfileId, setSelectedProfileId] = useState<string>('');
    const [auditResult, setAuditResult] = useState<any>(null);
    const [bioOptions, setBioOptions] = useState<string[]>([]);

    // Analytics State
    const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);

    // Spy State
    const [competitorHandle, setCompetitorHandle] = useState('');
    const [spyResult, setSpyResult] = useState<any>(null);

    // Discovery State
    const [hashtagForm, setHashtagForm] = useState({ niche: '', topic: '' });
    const [hashtagResult, setHashtagResult] = useState<any>(null);

    // Load profiles on mount
    useEffect(() => {
        fetch(`${API_URL}/api/v1/profiles`)
            .then(res => res.json())
            .then(data => {
                setProfiles(data);
                if (data.length > 0) setSelectedProfileId(data[0].id);
            })
            .catch(() => { });
    }, []);

    // Fetch Analytics when tab is active and profile selected
    useEffect(() => {
        if (activeTab === 'DEEP_ANALYTICS' && selectedProfileId) {
            const fetchAnalytics = async () => {
                setLoading(true);
                try {
                    const response = await axios.get(`${API_URL}/api/v1/analytics/${selectedProfileId}`);
                    setAnalyticsData(response.data);
                } catch (error) {
                    console.error("Error loading analytics:", error);
                    setAnalyticsData(null);
                } finally {
                    setLoading(false);
                }
            };
            fetchAnalytics();
        }
    }, [activeTab, selectedProfileId]);

    // === INTELLIGENCE HANDLERS ===
    const handleAnalyze = async (username: string) => {
        setLoading(true);
        setMood('PROCESSING');
        setAnalysis(null);
        setError(null);
        setTerminalLog([]);
        setOracleLogs([]);

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
            setOracleLogs([
                `[${new Date().toLocaleTimeString()}] SCAN COMPLETO: ${username.toUpperCase()}`,
                `[${new Date().toLocaleTimeString()}] FACULDADES ATIVAS: SENSE + MIND`,
                `[${new Date().toLocaleTimeString()}] DURAÇÃO: ${duration}s`,
                `[${new Date().toLocaleTimeString()}] STATUS: ✅ SUCESSO`
            ]);

            setMood('SUCCESS');
            setTimeout(() => setMood('IDLE'), 3000);
        } catch (err: unknown) {
            const errorObj = err as any;
            setError(errorObj.response?.data?.detail || "Falha na Conexão com o Oracle");
            setMood('ERROR');
        } finally {
            clearInterval(interval);
            setLoading(false);
        }
    };

    // === AUDIT HANDLERS ===
    const runAudit = async () => {
        if (!selectedProfileId) return;
        setLoading(true);
        setAuditResult(null);
        try {
            const res = await fetch(`${API_URL}/api/v1/oracle/seo/audit/${selectedProfileId}`, { method: 'POST' });
            if (!res.ok) throw new Error("Audit failed");
            const data = await res.json();
            setAuditResult(data);
            toast.success("Auditoria concluída!");
        } catch (e) {
            toast.error("Erro na auditoria.");
        } finally {
            setLoading(false);
        }
    };

    const fixBio = async () => {
        setLoading(true);
        try {
            const currentBio = auditResult?.profile_overiew?.bio || "Nova conta, sem bio definida.";
            const res = await fetch(`${API_URL}/api/v1/oracle/seo/fix-bio`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ current_bio: currentBio, niche: "General" })
            });
            const data = await res.json();
            setBioOptions(data.options || []);
        } finally {
            setLoading(false);
        }
    };

    // === SPY HANDLERS ===
    const runSpy = async () => {
        if (!competitorHandle) return;
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/v1/oracle/seo/spy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ competitor_handle: competitorHandle })
            });
            const data = await res.json();
            setSpyResult(data);
            toast.success("Dossiê gerado!");
        } catch (e) {
            toast.error("Erro ao espionar.");
        } finally {
            setLoading(false);
        }
    };

    // === DISCOVERY HANDLERS ===
    const runHashtags = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/v1/oracle/seo/hashtags`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hashtagForm })
            });
            const data = await res.json();
            setHashtagResult(data);
        } finally {
            setLoading(false);
        }
    };

    const formatNumber = (num: number) => {
        return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
    };

    const tabs = [
        { id: 'INTELLIGENCE' as TabType, label: 'Full Scan', icon: CubeTransparentIcon },
        { id: 'DEEP_ANALYTICS' as TabType, label: 'Deep Analytics', icon: ChartBarIcon },
        { id: 'AUDIT' as TabType, label: 'Auditoria SEO', icon: SparklesIcon },
        { id: 'SPY' as TabType, label: 'Competitor Spy', icon: MagnifyingGlassIcon },
        { id: 'DISCOVERY' as TabType, label: 'Discovery', icon: ArrowPathIcon },
    ];

    return (
        <div className="flex bg-[#050505] h-screen overflow-hidden font-sans text-gray-100">
            <Sidebar />
            <main className="flex-1 overflow-y-auto relative h-full scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {/* Background Grid */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(18,18,18,0)_1px,transparent_1px),linear-gradient(90deg,rgba(18,18,18,0)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none z-0 opacity-20" />

                <div className="max-w-7xl mx-auto relative z-10 space-y-8 pb-20 p-8">

                    {/* Header */}
                    <header className="text-center space-y-4">
                        <motion.h1
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-5xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-200 to-gray-500"
                        >
                            ORACLE
                        </motion.h1>
                        <p className="text-gray-400 text-lg">
                            Motor de Inteligência Artificial Unificado
                        </p>
                    </header>

                    {/* Tabs */}
                    <div className="flex justify-center gap-2 border-b border-white/10 pb-2">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={clsx(
                                    "flex items-center gap-2 px-5 py-2.5 text-sm font-bold uppercase tracking-wide transition-all rounded-t-lg",
                                    activeTab === tab.id
                                        ? "text-[#00f3ff] border-b-2 border-[#00f3ff] bg-[#00f3ff]/5"
                                        : "text-gray-500 hover:text-white hover:bg-white/5"
                                )}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Tab Content */}
                    <AnimatePresence mode="wait">
                        {/* INTELLIGENCE TAB */}
                        {activeTab === 'INTELLIGENCE' && (
                            <motion.div
                                key="intelligence"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="space-y-8"
                            >
                                <OracleInput onAnalyze={handleAnalyze} isLoading={loading} />

                                {/* Loading Terminal */}
                                {loading && (
                                    <div className="bg-black border border-green-500/30 rounded-lg p-6 font-mono text-green-500 text-sm max-w-2xl mx-auto">
                                        {terminalLog.map((line, idx) => (
                                            <div key={idx} className="mb-2">
                                                <span className="mr-2 opacity-50">[{new Date().toLocaleTimeString()}]</span>
                                                {line}
                                            </div>
                                        ))}
                                        <div className="animate-pulse">_</div>
                                    </div>
                                )}

                                {/* Error */}
                                {error && (
                                    <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl text-center max-w-xl mx-auto">
                                        ⚠️ ERRO: {error}
                                    </div>
                                )}

                                {/* Results */}
                                {analysis && !loading && (
                                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
                                        {/* Profile Header with Score */}
                                        <StitchCard className="p-6 bg-gradient-to-r from-[#00f3ff]/5 to-[#8b5cf6]/5">
                                            <div className="flex flex-col md:flex-row items-center gap-6">
                                                <div className="flex-shrink-0">
                                                    <ViralScoreGauge score={analysis.analysis.virality_score} />
                                                </div>
                                                <div className="flex-1 text-center md:text-left">
                                                    <div className="flex items-center justify-center md:justify-start gap-3 mb-2">
                                                        <h2 className="text-3xl font-black text-white">@{analysis.profile}</h2>
                                                        {analysis.analysis.profile_type && (
                                                            <span className={clsx(
                                                                "px-3 py-1 rounded-full text-xs font-bold",
                                                                analysis.analysis.profile_type === "Original Creator" ? "bg-green-500/20 text-green-400" :
                                                                    analysis.analysis.profile_type?.includes("Clips") ? "bg-purple-500/20 text-purple-400" :
                                                                        "bg-blue-500/20 text-blue-400"
                                                            )}>
                                                                {analysis.analysis.profile_type}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-gray-400">{analysis.analysis.summary}</p>
                                                    <div className="flex flex-wrap items-center gap-4 mt-3">
                                                        {analysis.analysis.voice_authenticity && (
                                                            <span className="text-xs text-gray-500">
                                                                🎙️ Voz: <span className="text-white">{analysis.analysis.voice_authenticity}</span>
                                                            </span>
                                                        )}
                                                        {analysis.analysis.engagement_quality && (
                                                            <span className="text-xs text-gray-500">
                                                                💬 Engajamento: <span className={clsx(
                                                                    analysis.analysis.engagement_quality === "High" ? "text-green-400" :
                                                                        analysis.analysis.engagement_quality === "Medium" ? "text-yellow-400" : "text-red-400"
                                                                )}>{analysis.analysis.engagement_quality}</span>
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        </StitchCard>

                                        {/* Performance Metrics Grid */}
                                        {analysis.analysis.performance_metrics && (
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                <StitchCard className="p-4 text-center">
                                                    <span className="text-2xl">📊</span>
                                                    <p className="text-xl font-bold text-white mt-2">{analysis.analysis.performance_metrics.avg_views_estimate}</p>
                                                    <p className="text-xs text-gray-500">VIEWS MÉDIOS</p>
                                                </StitchCard>
                                                <StitchCard className="p-4 text-center">
                                                    <span className="text-2xl">🎬</span>
                                                    <p className="text-xl font-bold text-white mt-2">{analysis.analysis.performance_metrics.verified_video_count}</p>
                                                    <p className="text-xs text-gray-500">VÍDEOS ANALISADOS</p>
                                                </StitchCard>
                                                <StitchCard className="p-4 text-center">
                                                    <span className="text-2xl">💬</span>
                                                    <p className="text-xl font-bold text-white mt-2">{analysis.analysis.performance_metrics.comments_analyzed_count}</p>
                                                    <p className="text-xs text-gray-500">COMENTÁRIOS</p>
                                                </StitchCard>
                                                <StitchCard className="p-4 text-center">
                                                    <span className="text-2xl">⚡</span>
                                                    <p className="text-sm font-bold text-white mt-2 line-clamp-2">{analysis.analysis.performance_metrics.engagement_rate_analysis}</p>
                                                    <p className="text-xs text-gray-500">ANÁLISE</p>
                                                </StitchCard>
                                            </div>
                                        )}

                                        {/* Audience Persona + Content Pillars */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Audience Persona */}
                                            {analysis.analysis.audience_persona && (
                                                <StitchCard className="p-5">
                                                    <h4 className="font-bold text-[#00f3ff] mb-4 flex items-center gap-2">
                                                        <span>👥</span> Persona da Audiência
                                                    </h4>
                                                    <div className="space-y-3">
                                                        <div>
                                                            <p className="text-xs text-gray-500 uppercase">DEMOGRAFIA</p>
                                                            <p className="text-sm text-white">{analysis.analysis.audience_persona.demographics}</p>
                                                        </div>
                                                        <div>
                                                            <p className="text-xs text-gray-500 uppercase">PSICOGRAFIA</p>
                                                            <p className="text-sm text-gray-300">{analysis.analysis.audience_persona.psychographics}</p>
                                                        </div>
                                                        {analysis.analysis.audience_persona.pain_points && (
                                                            <div>
                                                                <p className="text-xs text-gray-500 uppercase mb-2">DORES DO PÚBLICO</p>
                                                                <ul className="space-y-1">
                                                                    {analysis.analysis.audience_persona.pain_points.map((pain: string, i: number) => (
                                                                        <li key={i} className="flex items-start gap-2 text-sm">
                                                                            <span className="text-red-400">•</span>
                                                                            <span className="text-gray-300">{pain}</span>
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                    </div>
                                                </StitchCard>
                                            )}

                                            {/* Content Pillars + Gaps */}
                                            <StitchCard className="p-5">
                                                <h4 className="font-bold text-[#8b5cf6] mb-4 flex items-center gap-2">
                                                    <span>📚</span> Pilares de Conteúdo
                                                </h4>
                                                {analysis.analysis.content_pillars && (
                                                    <div className="flex flex-wrap gap-2 mb-4">
                                                        {analysis.analysis.content_pillars.map((pillar: string, i: number) => (
                                                            <span key={i} className="px-3 py-1 bg-[#8b5cf6]/20 text-[#8b5cf6] text-sm rounded-full">{pillar}</span>
                                                        ))}
                                                    </div>
                                                )}
                                                <h4 className="font-bold text-yellow-400 mb-3 flex items-center gap-2">
                                                    <span>🎯</span> Gaps (Oportunidades)
                                                </h4>
                                                {analysis.analysis.content_gaps && (
                                                    <ul className="space-y-2">
                                                        {analysis.analysis.content_gaps.map((gap: string, i: number) => (
                                                            <li key={i} className="flex items-start gap-2 text-sm">
                                                                <span className="text-yellow-400">→</span>
                                                                <span className="text-gray-300">{gap}</span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                )}
                                            </StitchCard>
                                        </div>

                                        {/* Sentiment + Viral Hooks Row */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Enhanced Sentiment */}
                                            {analysis.analysis.sentiment_pulse && (
                                                <StitchCard className="p-5">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <h4 className="font-bold text-pink-400 flex items-center gap-2">
                                                            <span>💗</span> Pulso do Sentimento
                                                        </h4>
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-2xl font-black text-pink-400">{analysis.analysis.sentiment_pulse.score}%</span>
                                                            <span className={clsx(
                                                                "px-2 py-1 rounded text-xs font-bold",
                                                                analysis.analysis.sentiment_pulse.dominant_emotion?.includes("Love") ? "bg-pink-500/20 text-pink-400" :
                                                                    analysis.analysis.sentiment_pulse.dominant_emotion?.includes("Curiosity") ? "bg-blue-500/20 text-blue-400" :
                                                                        "bg-red-500/20 text-red-400"
                                                            )}>
                                                                {analysis.analysis.sentiment_pulse.dominant_emotion}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    {analysis.analysis.sentiment_pulse.top_questions?.length > 0 && (
                                                        <div className="mb-3">
                                                            <p className="text-xs text-gray-500 uppercase mb-2">TOP DÚVIDAS DA AUDIÊNCIA</p>
                                                            {analysis.analysis.sentiment_pulse.top_questions.map((q: string, i: number) => (
                                                                <p key={i} className="text-sm text-gray-300 mb-1">❓ {q}</p>
                                                            ))}
                                                        </div>
                                                    )}
                                                    {analysis.analysis.sentiment_pulse.debate_topic && (
                                                        <div className="p-3 bg-orange-500/10 rounded-lg">
                                                            <p className="text-xs text-orange-400 font-bold">🔥 TRENDING DEBATE</p>
                                                            <p className="text-sm text-gray-300">{analysis.analysis.sentiment_pulse.debate_topic}</p>
                                                        </div>
                                                    )}
                                                </StitchCard>
                                            )}

                                            {/* Enhanced Viral Hooks */}
                                            <StitchCard className="p-5 bg-gradient-to-r from-yellow-900/10 to-transparent">
                                                <h4 className="font-bold text-yellow-400 mb-4 flex items-center gap-2">
                                                    <span>⚡</span> Ganchos Virais Detectados
                                                </h4>
                                                <div className="space-y-3">
                                                    {analysis.analysis.viral_hooks?.map((hook: { type: string; description: string }, i: number) => (
                                                        <div key={i} className="flex items-start gap-3">
                                                            <span className={clsx(
                                                                "px-2 py-0.5 rounded text-xs font-bold flex-shrink-0",
                                                                hook.type === "Visual" ? "bg-blue-500/20 text-blue-400" :
                                                                    hook.type === "Psychological" ? "bg-purple-500/20 text-purple-400" :
                                                                        "bg-green-500/20 text-green-400"
                                                            )}>
                                                                {hook.type}
                                                            </span>
                                                            <p className="text-sm text-gray-300">{hook.description}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </StitchCard>
                                        </div>

                                        {/* Suggested Next Video */}
                                        {analysis.analysis.suggested_next_video && (
                                            <StitchCard className="p-6 bg-gradient-to-r from-green-900/20 to-transparent border-l-4 border-l-green-500">
                                                <h4 className="font-bold text-green-400 mb-4 flex items-center gap-2 text-lg">
                                                    <span>🎬</span> Próximo Vídeo Sugerido pela IA
                                                </h4>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                    <div>
                                                        <p className="text-xs text-gray-500 uppercase mb-2">TÍTULO</p>
                                                        <p className="text-lg font-bold text-white mb-4">{analysis.analysis.suggested_next_video.title}</p>
                                                        <p className="text-xs text-gray-500 uppercase mb-2">CONCEITO</p>
                                                        <p className="text-sm text-gray-300">{analysis.analysis.suggested_next_video.concept}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-gray-500 uppercase mb-2">HOOK (PRIMEIROS 3s)</p>
                                                        <div className="p-3 bg-black/30 rounded-lg mb-4 cursor-pointer hover:bg-black/50 transition-all"
                                                            onClick={() => { navigator.clipboard.writeText(analysis.analysis.suggested_next_video.hook_script); toast.success("Hook copiado!"); }}
                                                        >
                                                            <p className="text-white font-mono text-sm">"{analysis.analysis.suggested_next_video.hook_script}"</p>
                                                        </div>
                                                        <p className="text-xs text-gray-500 uppercase mb-2">POR QUÊ VAI FUNCIONAR</p>
                                                        <p className="text-sm text-gray-300">{analysis.analysis.suggested_next_video.reasoning}</p>
                                                    </div>
                                                </div>
                                            </StitchCard>
                                        )}

                                        {/* Best Times */}
                                        {(analysis.analysis.best_times?.length ?? 0) > 0 && (
                                            <StitchCard className="p-5">
                                                <h4 className="font-bold text-[#00f3ff] mb-4 flex items-center gap-2">
                                                    <span>🕐</span> Melhores Horários para Postar
                                                </h4>
                                                <div className="flex flex-wrap gap-3">
                                                    {analysis.analysis.best_times?.map((time: { day: string; hour: number; reason: string }, i: number) => (
                                                        <div key={i} className="p-3 bg-[#00f3ff]/10 rounded-lg text-center min-w-[120px]">
                                                            <p className="text-sm font-bold text-[#00f3ff]">{time.day}</p>
                                                            <p className="text-xl font-black text-white">{time.hour}:00</p>
                                                            <p className="text-xs text-gray-400">{time.reason}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </StitchCard>
                                        )}

                                        {/* Log */}
                                        <div className="max-w-4xl mx-auto pt-4 border-t border-white/5">
                                            <h3 className="text-xs font-mono text-gray-500 mb-2 uppercase tracking-widest">Registro Neural</h3>
                                            <LogTerminal logs={oracleLogs} className="h-32" />
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* DEEP ANALYTICS TAB */}
                        {activeTab === 'DEEP_ANALYTICS' && (
                            <motion.div
                                key="deep-analytics"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="space-y-6"
                            >
                                {/* Profile Selector (Shared with Audit) */}
                                <div className="flex justify-end mb-4">
                                    <div className="flex items-center gap-3 bg-[#0f0a15] border border-white/10 rounded-full px-4 py-2">
                                        <span className="text-sm text-gray-400">Perfil:</span>
                                        <select
                                            value={selectedProfileId}
                                            onChange={(e) => setSelectedProfileId(e.target.value)}
                                            className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
                                        >
                                            {profiles.map(p => (
                                                <option key={p.id} value={p.id} className="bg-[#0f0a15]">
                                                    {p.label || p.username}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {loading ? (
                                    <div className="h-64 flex flex-col items-center justify-center text-[#00f3ff] animate-pulse">
                                        <ChartBarIcon className="w-12 h-12 mb-4" />
                                        <p>Processando Dados...</p>
                                    </div>
                                ) : analyticsData ? (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
                                        {/* KPI Grid */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                            <StatCard
                                                label="Total de Views"
                                                value={formatNumber(analyticsData.summary.total_views)}
                                                icon={<EyeIcon className="w-6 h-6 text-white" />}
                                                color="purple"
                                                trend="up"
                                                trendValue="12%"
                                            />
                                            <StatCard
                                                label="Engajamento Médio"
                                                value={analyticsData.summary.avg_engagement.toFixed(1)}
                                                icon={<HeartIcon className="w-6 h-6 text-white" />}
                                                color="pink"
                                                subValue="Likes + Comentários por View"
                                            />
                                            <StatCard
                                                label="Seguidores"
                                                value={formatNumber(analyticsData.summary.followers)}
                                                icon={<SparklesIcon className="w-6 h-6 text-white" />}
                                                color="blue"
                                            />
                                            <StatCard
                                                label="Posts Analisados"
                                                value={analyticsData.summary.posts_analyzed}
                                                icon={<ChatBubbleLeftIcon className="w-6 h-6 text-white" />}
                                                color="green"
                                            />
                                        </div>

                                        {/* Advanced Charts Row 1: Retention & Heatmap */}
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                            {/* Fix Key Mismatch: Backend 'time' -> Component 'second' (or update component) */}
                                            {/* We will update Component to be flexible, but here let's map it just in case */}
                                            <RetentionChart data={analyticsData.retention_curve?.map(d => ({ second: d.time, retention_rate: d.retention }))} />
                                            <EngagementHeatmap data={analyticsData.heatmap_data} />
                                        </div>

                                        {/* Advanced Charts Row 2: Performance & Comparison */}
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                            <div className="lg:col-span-2">
                                                <StitchCard className="p-1 border-none bg-transparent">
                                                    <h3 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider ml-2">Histórico de Views</h3>
                                                    <PerformanceChart data={analyticsData.history} />
                                                </StitchCard>
                                            </div>
                                            <div>
                                                {/* Transform Comparison Data for Chart */}
                                                <MetricComparisonChart data={[
                                                    {
                                                        period: 'Views',
                                                        current: analyticsData.comparison?.current.views || 0,
                                                        previous: analyticsData.comparison?.previous.views || 0
                                                    },
                                                    {
                                                        period: 'Likes',
                                                        current: analyticsData.comparison?.current.likes || 0,
                                                        previous: analyticsData.comparison?.previous.likes || 0
                                                    }
                                                ]} />
                                            </div>
                                        </div>

                                        {/* Patterns Intelligence */}
                                        <div>
                                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                                <SparklesIcon className="w-5 h-5 text-yellow-400" />
                                                Padrões Detectados pela IA
                                            </h3>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                                {analyticsData.patterns && analyticsData.patterns.length > 0 ? (
                                                    analyticsData.patterns.map((pattern, idx) => (
                                                        <PatternCard
                                                            key={idx}
                                                            type={pattern.type}
                                                            title={pattern.title}
                                                            description={pattern.description}
                                                            confidence={pattern.confidence}
                                                            impact={pattern.impact}
                                                        />
                                                    ))
                                                ) : (
                                                    <p className="text-gray-500 col-span-3 text-sm">Nenhum padrão significativo detectado ainda.</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="h-64 flex items-center justify-center text-gray-500 border border-white/5 rounded-xl bg-white/[0.02]">
                                        Selecione um perfil para visualizar os dados profundos.
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* AUDIT TAB */}
                        {activeTab === 'AUDIT' && (
                            <motion.div
                                key="audit"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="space-y-6"
                            >
                                <div className="flex gap-4 items-end bg-[#13111a] p-4 rounded-xl border border-white/5">
                                    <div className="flex-1">
                                        <label className="text-xs text-gray-500 font-bold block mb-2">SELECIONE O PERFIL</label>
                                        <select
                                            value={selectedProfileId}
                                            onChange={(e) => setSelectedProfileId(e.target.value)}
                                            className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white outline-none focus:border-[#00f3ff]"
                                        >
                                            {profiles.map(p => (
                                                <option key={p.id} value={p.id}>{p.label || p.username} ({p.username})</option>
                                            ))}
                                        </select>
                                    </div>
                                    <NeonButton onClick={runAudit} disabled={loading} className="py-3 px-8">
                                        {loading ? "Analisando..." : "Executar Auditoria"}
                                    </NeonButton>
                                </div>

                                {auditResult && (
                                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
                                        {/* Main Score */}
                                        <div className="flex justify-center">
                                            <StitchCard className="p-8 text-center bg-gradient-to-br from-[#13111a] to-[#0a0815] max-w-sm w-full">
                                                <div className="text-7xl font-black bg-gradient-to-r from-[#00f3ff] to-[#8b5cf6] bg-clip-text text-transparent">
                                                    {auditResult.total_score}
                                                </div>
                                                <p className="text-gray-400 mt-2 text-sm uppercase tracking-wider">Score Geral</p>
                                                <div className="mt-4 h-2 bg-gray-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-[#00f3ff] to-[#8b5cf6] transition-all duration-1000"
                                                        style={{ width: `${auditResult.total_score}%` }}
                                                    />
                                                </div>
                                            </StitchCard>
                                        </div>

                                        {/* Niche Detection Badge */}
                                        {auditResult.niche && auditResult.niche.niche && (
                                            <StitchCard className="p-5 bg-gradient-to-r from-[#00f3ff]/5 to-[#8b5cf6]/5 border-l-4 border-l-[#00f3ff]">
                                                <div className="flex flex-wrap items-center gap-4">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-2xl">🎯</span>
                                                        <div>
                                                            <p className="text-xs text-gray-500 uppercase">Nicho Detectado</p>
                                                            <p className="text-lg font-bold text-[#00f3ff]">{auditResult.niche.niche}</p>
                                                        </div>
                                                    </div>
                                                    {auditResult.niche.audience && (
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xl">👥</span>
                                                            <div>
                                                                <p className="text-xs text-gray-500 uppercase">Público</p>
                                                                <p className="text-sm text-gray-300">{auditResult.niche.audience}</p>
                                                            </div>
                                                        </div>
                                                    )}
                                                    {auditResult.niche.content_style && (
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xl">🎬</span>
                                                            <div>
                                                                <p className="text-xs text-gray-500 uppercase">Estilo</p>
                                                                <p className="text-sm text-gray-300">{auditResult.niche.content_style}</p>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                                {auditResult.niche.trending_format && (
                                                    <div className="mt-3 p-2 rounded-lg bg-[#8b5cf6]/10 text-sm">
                                                        <span className="text-[#8b5cf6] font-bold">🔥 Formato em Alta:</span>
                                                        <span className="text-gray-300 ml-2">{auditResult.niche.trending_format}</span>
                                                    </div>
                                                )}
                                            </StitchCard>
                                        )}

                                        {/* Section Cards Grid */}
                                        {auditResult.sections && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                                {Object.entries(auditResult.sections).map(([key, section]: [string, any]) => (
                                                    <StitchCard key={key} className="p-5 hover:border-[#00f3ff]/30 transition-all">
                                                        <div className="flex items-center justify-between mb-3">
                                                            <span className="text-2xl">{section.icon}</span>
                                                            <span className={clsx(
                                                                "text-2xl font-bold",
                                                                section.score >= 70 ? "text-green-400" :
                                                                    section.score >= 50 ? "text-yellow-400" : "text-red-400"
                                                            )}>
                                                                {section.score}
                                                            </span>
                                                        </div>
                                                        <h4 className="text-sm font-bold text-white mb-2">{section.label}</h4>
                                                        <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden mb-3">
                                                            <div
                                                                className={clsx(
                                                                    "h-full transition-all duration-700",
                                                                    section.score >= 70 ? "bg-green-500" :
                                                                        section.score >= 50 ? "bg-yellow-500" : "bg-red-500"
                                                                )}
                                                                style={{ width: `${section.score}%` }}
                                                            />
                                                        </div>
                                                        <ul className="space-y-1.5 max-h-32 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700">
                                                            {section.items.slice(0, 4).map((item: any, idx: number) => (
                                                                <li key={idx} className="flex items-start gap-2 text-xs">
                                                                    <span className={clsx(
                                                                        "mt-0.5 flex-shrink-0",
                                                                        item.status === "ok" ? "text-green-400" :
                                                                            item.status === "warning" ? "text-yellow-400" :
                                                                                item.status === "tip" ? "text-[#00f3ff]" : "text-gray-400"
                                                                    )}>
                                                                        {item.status === "ok" ? "✓" :
                                                                            item.status === "warning" ? "!" :
                                                                                item.status === "tip" ? "💡" : "•"}
                                                                    </span>
                                                                    <span className="text-gray-300">{item.text}</span>
                                                                </li>
                                                            ))}
                                                            {section.items.length === 0 && (
                                                                <li className="text-xs text-gray-600 italic">Sem dados</li>
                                                            )}
                                                        </ul>
                                                    </StitchCard>
                                                ))}
                                            </div>
                                        )}

                                        {/* AI Recommendations */}
                                        {auditResult.recommendations && auditResult.recommendations.length > 0 && (
                                            <StitchCard className="p-6 bg-gradient-to-r from-[#8b5cf6]/10 to-transparent border-l-4 border-l-[#8b5cf6]">
                                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                                    <SparklesIcon className="w-5 h-5 text-[#8b5cf6]" />
                                                    Recomendações da IA
                                                </h3>
                                                <ul className="space-y-2">
                                                    {auditResult.recommendations.map((rec: string, idx: number) => (
                                                        <li key={idx} className="flex items-start gap-3 text-sm">
                                                            <span className="w-6 h-6 rounded-full bg-[#8b5cf6]/20 text-[#8b5cf6] flex items-center justify-center text-xs font-bold flex-shrink-0">
                                                                {idx + 1}
                                                            </span>
                                                            <span className="text-gray-300">{rec}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </StitchCard>
                                        )}

                                        {/* Bio Optimizer - Enhanced */}
                                        <StitchCard className="p-6 bg-gradient-to-r from-synapse-purple/10 to-transparent">
                                            <div className="flex justify-between items-center mb-4">
                                                <h3 className="text-xl font-bold">Bio Optimizer</h3>
                                                <NeonButton onClick={fixBio} disabled={loading}>✨ Auto-Fix Bio</NeonButton>
                                            </div>

                                            {/* Current Bio Display */}
                                            {auditResult.profile_overiew?.bio && (
                                                <div className="mb-4 p-4 rounded-xl bg-black/30 border border-white/10">
                                                    <p className="text-xs text-gray-500 font-bold mb-2">BIO ATUAL</p>
                                                    <p className="text-sm text-gray-300">{auditResult.profile_overiew.bio || "Sem bio definida"}</p>
                                                </div>
                                            )}

                                            {/* CTA Suggestions from audit */}
                                            {auditResult.sections?.bio?.cta_suggestions && (
                                                <div className="mb-4">
                                                    <p className="text-xs text-gray-500 font-bold mb-3">💡 SUGESTÕES DE CTA</p>
                                                    <div className="flex flex-wrap gap-2">
                                                        {auditResult.sections.bio.cta_suggestions.map((cta: string, i: number) => (
                                                            <button
                                                                key={i}
                                                                onClick={() => { navigator.clipboard.writeText(cta); toast.success("CTA copiado!"); }}
                                                                className="px-3 py-1.5 text-xs rounded-full bg-[#8b5cf6]/20 text-[#8b5cf6] border border-[#8b5cf6]/30 hover:bg-[#8b5cf6]/30 transition-all cursor-pointer"
                                                            >
                                                                {cta}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* AI Generated Bio Options */}
                                            {bioOptions.length > 0 ? (
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                                                    {bioOptions.map((opt, i) => (
                                                        <div key={i} className="p-4 rounded-xl bg-black/40 border border-white/10 cursor-pointer hover:border-[#00f3ff]/50 group transition-all"
                                                            onClick={() => { navigator.clipboard.writeText(opt); toast.success("Bio copiada!"); }}
                                                        >
                                                            <div className="flex items-center justify-between mb-2">
                                                                <span className="text-xs text-[#00f3ff] font-bold">OPÇÃO {i + 1}</span>
                                                                <ClipboardIcon className="w-4 h-4 text-gray-600 group-hover:text-[#00f3ff] transition-colors" />
                                                            </div>
                                                            <p className="text-sm text-gray-300">{opt}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-xs text-gray-500 text-center py-4 border border-dashed border-white/10 rounded-lg">
                                                    Clique em "Auto-Fix Bio" para gerar sugestões otimizadas pela IA
                                                </p>
                                            )}
                                        </StitchCard>
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* SPY TAB */}
                        {activeTab === 'SPY' && (
                            <motion.div
                                key="spy"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="max-w-3xl mx-auto space-y-8"
                            >
                                <div className="bg-[#13111a] p-8 rounded-2xl border border-white/10 text-center">
                                    <h3 className="text-2xl font-bold mb-2">Espionagem Industrial</h3>
                                    <p className="text-gray-400 mb-6">Insira o @ do concorrente para revelar suas táticas.</p>
                                    <div className="flex gap-2 max-w-md mx-auto">
                                        <input
                                            type="text"
                                            placeholder="@concorrente"
                                            value={competitorHandle}
                                            onChange={e => setCompetitorHandle(e.target.value)}
                                            className="flex-1 bg-black text-white px-4 rounded-lg border border-white/20 focus:border-[#00f3ff] outline-none"
                                        />
                                        <NeonButton onClick={runSpy} disabled={loading}>
                                            {loading ? "Infiltrando..." : "Hackear"}
                                        </NeonButton>
                                    </div>
                                </div>

                                {spyResult && (
                                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
                                        {/* Target Profile Header */}
                                        <StitchCard className="p-6 bg-gradient-to-r from-red-900/20 to-transparent border-l-4 border-l-red-500">
                                            <div className="flex items-center justify-between flex-wrap gap-4">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center text-3xl">🎯</div>
                                                    <div>
                                                        <p className="text-xs text-red-400 uppercase font-bold">DOSSIÊ CONFIDENCIAL</p>
                                                        <h3 className="text-2xl font-black text-white">@{spyResult.scraped_data?.username}</h3>
                                                        <p className="text-sm text-gray-400">{spyResult.analysis?.niche}</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-6">
                                                    <div className="text-center">
                                                        <p className="text-3xl font-black text-red-400">{spyResult.analysis?.competitor_score || 50}</p>
                                                        <p className="text-xs text-gray-500">THREAT SCORE</p>
                                                    </div>
                                                    <div className={clsx(
                                                        "px-4 py-2 rounded-full text-sm font-bold",
                                                        spyResult.analysis?.threat_level === "Crítico" ? "bg-red-500/20 text-red-400" :
                                                            spyResult.analysis?.threat_level === "Alto" ? "bg-orange-500/20 text-orange-400" :
                                                                spyResult.analysis?.threat_level === "Médio" ? "bg-yellow-500/20 text-yellow-400" :
                                                                    "bg-green-500/20 text-green-400"
                                                    )}>
                                                        {spyResult.analysis?.threat_level || "Médio"}
                                                    </div>
                                                </div>
                                            </div>
                                        </StitchCard>

                                        {/* Metrics Grid */}
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                            {[
                                                { label: "Seguidores", value: spyResult.scraped_data?.followers?.toLocaleString(), icon: "👥" },
                                                { label: "Likes Totais", value: spyResult.scraped_data?.likes?.toLocaleString(), icon: "❤️" },
                                                { label: "Vídeos", value: spyResult.scraped_data?.videos, icon: "🎬" },
                                                { label: "Engajamento", value: `${spyResult.scraped_data?.engagement_rate}%`, icon: "📊" },
                                            ].map((metric, i) => (
                                                <StitchCard key={i} className="p-4 text-center">
                                                    <span className="text-2xl">{metric.icon}</span>
                                                    <p className="text-xl font-bold text-white mt-2">{metric.value}</p>
                                                    <p className="text-xs text-gray-500 uppercase">{metric.label}</p>
                                                </StitchCard>
                                            ))}
                                        </div>

                                        {/* Strategy & Weaknesses Grid */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            {/* Strengths */}
                                            <StitchCard className="p-5">
                                                <h4 className="font-bold text-green-400 mb-3 flex items-center gap-2">
                                                    <span>💪</span> Pontos Fortes
                                                </h4>
                                                <ul className="space-y-2">
                                                    {spyResult.analysis?.strengths?.map((s: string, i: number) => (
                                                        <li key={i} className="flex items-start gap-2 text-sm">
                                                            <span className="text-green-400 mt-0.5">✓</span>
                                                            <span className="text-gray-300">{s}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </StitchCard>

                                            {/* Weaknesses */}
                                            <StitchCard className="p-5 bg-red-900/5">
                                                <h4 className="font-bold text-red-400 mb-3 flex items-center gap-2">
                                                    <span>🎯</span> Fraquezas Exploráveis
                                                </h4>
                                                <ul className="space-y-2">
                                                    {spyResult.analysis?.weaknesses?.map((w: string, i: number) => (
                                                        <li key={i} className="flex items-start gap-2 text-sm">
                                                            <span className="text-red-400 mt-0.5">!</span>
                                                            <span className="text-gray-300">{w}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </StitchCard>
                                        </div>

                                        {/* Content Strategy */}
                                        {spyResult.analysis?.content_strategy && (
                                            <StitchCard className="p-5">
                                                <h4 className="font-bold text-[#00f3ff] mb-4 flex items-center gap-2">
                                                    <span>📈</span> Estratégia de Conteúdo
                                                </h4>
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                    <div>
                                                        <p className="text-gray-500 text-xs uppercase">Frequência</p>
                                                        <p className="text-white font-bold">{spyResult.analysis.content_strategy.posting_frequency}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-500 text-xs uppercase">Formato</p>
                                                        <p className="text-white font-bold">{spyResult.analysis.content_strategy.format_preference}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-500 text-xs uppercase">Estilo de Hook</p>
                                                        <p className="text-white font-bold">{spyResult.analysis.content_strategy.hook_style}</p>
                                                    </div>
                                                    <div>
                                                        <p className="text-gray-500 text-xs uppercase">Uso de CTA</p>
                                                        <p className="text-white font-bold">{spyResult.analysis.content_strategy.cta_usage}</p>
                                                    </div>
                                                </div>
                                                {spyResult.analysis.content_strategy.content_pillars && (
                                                    <div className="mt-4 flex flex-wrap gap-2">
                                                        {spyResult.analysis.content_strategy.content_pillars.map((pillar: string, i: number) => (
                                                            <span key={i} className="px-3 py-1 bg-[#00f3ff]/10 text-[#00f3ff] text-xs rounded-full">{pillar}</span>
                                                        ))}
                                                    </div>
                                                )}
                                            </StitchCard>
                                        )}

                                        {/* Hooks to Steal */}
                                        <StitchCard className="p-5 bg-gradient-to-r from-[#8b5cf6]/10 to-transparent">
                                            <h4 className="font-bold text-[#8b5cf6] mb-4 flex items-center gap-2">
                                                <span>🪝</span> Hooks para Roubar
                                            </h4>
                                            <div className="space-y-3">
                                                {spyResult.analysis?.content_hooks_to_steal?.map((hook: string, i: number) => (
                                                    <div key={i} className="p-3 bg-black/30 rounded-lg flex items-start gap-3 cursor-pointer hover:bg-black/50 transition-all group"
                                                        onClick={() => { navigator.clipboard.writeText(hook); toast.success("Hook copiado!"); }}
                                                    >
                                                        <span className="w-6 h-6 rounded-full bg-[#8b5cf6]/20 text-[#8b5cf6] flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</span>
                                                        <p className="text-sm text-gray-300 flex-1">{hook}</p>
                                                        <ClipboardIcon className="w-4 h-4 text-gray-600 group-hover:text-[#8b5cf6] transition-colors" />
                                                    </div>
                                                ))}
                                            </div>
                                        </StitchCard>

                                        {/* Battle Plan */}
                                        {spyResult.analysis?.battle_plan && (
                                            <StitchCard className="p-5 bg-gradient-to-r from-yellow-900/10 to-transparent border-l-4 border-l-yellow-500">
                                                <h4 className="font-bold text-yellow-400 mb-4 flex items-center gap-2">
                                                    <span>⚔️</span> Plano de Batalha
                                                </h4>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div>
                                                        <p className="text-xs text-gray-500 uppercase mb-2">Ações Imediatas</p>
                                                        <ul className="space-y-2">
                                                            {spyResult.analysis.battle_plan.immediate_actions?.map((action: string, i: number) => (
                                                                <li key={i} className="flex items-start gap-2 text-sm">
                                                                    <span className="text-yellow-400">→</span>
                                                                    <span className="text-gray-300">{action}</span>
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-gray-500 uppercase mb-2">Ideias de Conteúdo</p>
                                                        <ul className="space-y-2">
                                                            {spyResult.analysis.battle_plan.content_ideas?.map((idea: string, i: number) => (
                                                                <li key={i} className="flex items-start gap-2 text-sm">
                                                                    <span className="text-yellow-400">💡</span>
                                                                    <span className="text-gray-300">{idea}</span>
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                </div>
                                                {spyResult.analysis.battle_plan.differentiation_strategy && (
                                                    <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg">
                                                        <p className="text-xs text-yellow-400 font-bold mb-1">ESTRATÉGIA DE DIFERENCIAÇÃO</p>
                                                        <p className="text-sm text-gray-300">{spyResult.analysis.battle_plan.differentiation_strategy}</p>
                                                    </div>
                                                )}
                                            </StitchCard>
                                        )}

                                        {/* Killer Bio */}
                                        {spyResult.analysis?.killer_bio && (
                                            <StitchCard className="p-5">
                                                <h4 className="font-bold text-white mb-3 flex items-center gap-2">
                                                    <span>✍️</span> Bio Otimizada (Sugestão)
                                                </h4>
                                                <div className="p-4 bg-black/30 rounded-lg cursor-pointer hover:bg-black/50 transition-all group"
                                                    onClick={() => { navigator.clipboard.writeText(spyResult.analysis.killer_bio); toast.success("Bio copiada!"); }}
                                                >
                                                    <p className="text-gray-300">{spyResult.analysis.killer_bio}</p>
                                                    <p className="text-xs text-gray-500 mt-2 group-hover:text-[#00f3ff]">Clique para copiar</p>
                                                </div>
                                            </StitchCard>
                                        )}
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* DISCOVERY TAB */}
                        {activeTab === 'DISCOVERY' && (
                            <motion.div
                                key="discovery"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="max-w-4xl mx-auto"
                            >
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <StitchCard className="p-6">
                                        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                            <ArrowPathIcon className="w-5 h-5 text-[#00f3ff]" />
                                            Gerador de Hashtags
                                        </h3>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="text-xs text-gray-500 font-bold block mb-1">NICHO</label>
                                                <input type="text" placeholder="Ex: Marketing Digital"
                                                    className="w-full bg-black/50 border border-white/10 px-3 py-2 rounded-lg text-white"
                                                    value={hashtagForm.niche}
                                                    onChange={e => setHashtagForm({ ...hashtagForm, niche: e.target.value })}
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs text-gray-500 font-bold block mb-1">TÓPICO</label>
                                                <input type="text" placeholder="Ex: Como ganhar dinheiro"
                                                    className="w-full bg-black/50 border border-white/10 px-3 py-2 rounded-lg text-white"
                                                    value={hashtagForm.topic}
                                                    onChange={e => setHashtagForm({ ...hashtagForm, topic: e.target.value })}
                                                />
                                            </div>
                                            <NeonButton className="w-full justify-center" onClick={runHashtags} disabled={loading}>
                                                {loading ? "Minerando..." : "Gerar Hashtags"}
                                            </NeonButton>
                                        </div>
                                    </StitchCard>

                                    <div className="space-y-4">
                                        {hashtagResult ? (
                                            <>
                                                {['broad', 'niche', 'trending'].map((cat) => (
                                                    <div key={cat} className="p-4 rounded-xl bg-[#13111a] border border-white/10">
                                                        <div className="flex justify-between items-center mb-2">
                                                            <h4 className="text-sm font-bold capitalize text-gray-300">{cat} Tags</h4>
                                                            <button className="text-xs text-[#00f3ff] hover:underline"
                                                                onClick={() => navigator.clipboard.writeText(hashtagResult[cat]?.join(' ') || '')}
                                                            >
                                                                Copy
                                                            </button>
                                                        </div>
                                                        <div className="flex flex-wrap gap-2">
                                                            {hashtagResult[cat]?.map((tag: string) => (
                                                                <span key={tag} className="px-2 py-0.5 rounded bg-white/5 text-xs text-gray-400 border border-white/5">
                                                                    {tag}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                ))}
                                            </>
                                        ) : (
                                            <div className="h-full flex items-center justify-center border border-dashed border-white/10 rounded-xl text-gray-600 min-h-[200px]">
                                                Resultados aparecerão aqui...
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </motion.div>
                        )}



                    </AnimatePresence >

                </div >
            </main >
        </div >
    );
}
