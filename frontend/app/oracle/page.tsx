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
import axios from 'axios';

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
        fetch('http://localhost:8000/api/v1/profiles')
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
                    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
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
            const res = await fetch(`http://localhost:8000/api/v1/oracle/seo/audit/${selectedProfileId}`, { method: 'POST' });
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
            const res = await fetch(`http://localhost:8000/api/v1/oracle/seo/fix-bio`, {
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
            const res = await fetch(`http://localhost:8000/api/v1/oracle/seo/spy`, {
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
            const res = await fetch(`http://localhost:8000/api/v1/oracle/seo/hashtags`, {
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
                                    <div className="space-y-6">
                                        {/* Score Card */}
                                        <div className="flex justify-center">
                                            <div className="bg-[#0a0a0f]/60 backdrop-blur border border-white/5 rounded-2xl p-8 flex flex-col items-center max-w-2xl w-full text-center">
                                                <ViralScoreGauge score={analysis.analysis.virality_score} />
                                                <h2 className="text-3xl font-bold mt-4 text-white">@{analysis.profile}</h2>
                                                <p className="text-gray-400 text-sm mt-2">{analysis.analysis.summary}</p>
                                            </div>
                                        </div>

                                        {/* Insights Cards */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                            {analysis.analysis.sentiment_pulse && (
                                                <SentimentCard data={analysis.analysis.sentiment_pulse} delay={0.1} />
                                            )}
                                            <InsightCard title="Ganchos Virais" items={analysis.analysis.viral_hooks.map(h => h.description)} icon="⚡" delay={0.2} />
                                            <InsightCard title="Content Gaps" items={analysis.analysis.content_gaps} icon="🎯" delay={0.3} />
                                        </div>

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
                                        <span className="text-sm text-gray-400">Profile:</span>
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
                                        <p>Crunching Data...</p>
                                    </div>
                                ) : analyticsData ? (
                                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
                                        {/* KPI Grid */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                            <StatCard
                                                label="Total Views"
                                                value={formatNumber(analyticsData.summary.total_views)}
                                                icon={<EyeIcon className="w-6 h-6 text-white" />}
                                                color="purple"
                                                trend="up"
                                                trendValue="12%"
                                            />
                                            <StatCard
                                                label="Avg Engagement"
                                                value={analyticsData.summary.avg_engagement.toFixed(1)}
                                                icon={<HeartIcon className="w-6 h-6 text-white" />}
                                                color="pink"
                                                subValue="Likes + Comments per View"
                                            />
                                            <StatCard
                                                label="Followers"
                                                value={formatNumber(analyticsData.summary.followers)}
                                                icon={<SparklesIcon className="w-6 h-6 text-white" />}
                                                color="blue"
                                            />
                                            <StatCard
                                                label="Analyzed Posts"
                                                value={analyticsData.summary.posts_analyzed}
                                                icon={<ChatBubbleLeftIcon className="w-6 h-6 text-white" />}
                                                color="green"
                                            />
                                        </div>

                                        {/* Charts Area */}
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                            {/* Main Chart */}
                                            <div className="lg:col-span-2 bg-[#0f0a15] border border-white/5 rounded-2xl p-6">
                                                <h3 className="text-lg font-bold mb-6 text-gray-200">Views Growth</h3>
                                                <PerformanceChart data={analyticsData.history} />
                                            </div>

                                            {/* Insights */}
                                            <div className="bg-[#0f0a15] border border-white/5 rounded-2xl p-6">
                                                <h3 className="text-lg font-bold mb-6 text-gray-200">Oracle Insights</h3>
                                                <div className="space-y-4">
                                                    <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                                        <div className="text-sm text-gray-400 mb-1">Top Performing Day</div>
                                                        <div className="text-xl font-bold text-white">Friday</div>
                                                    </div>
                                                    <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                                        <div className="text-sm text-gray-400 mb-1">Viral Potential</div>
                                                        <div className="text-xl font-bold text-[#00f3ff]">High</div>
                                                    </div>
                                                    <div className="mt-4 p-4 rounded-xl bg-synapse-purple/10 border border-synapse-purple/20">
                                                        <p className="text-xs text-synapse-purple leading-relaxed">
                                                            💡 <strong>Tip:</strong> Your videos posted on Fridays get 2x more views than other days.
                                                        </p>
                                                    </div>
                                                </div>
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
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <StitchCard className="p-6">
                                            <h3 className="text-xl font-bold mb-4">Vision Score</h3>
                                            <div className="text-5xl font-bold text-[#00f3ff]">{auditResult.total_score}</div>
                                        </StitchCard>
                                        <StitchCard className="p-6">
                                            <h3 className="text-xl font-bold mb-4">Relatório</h3>
                                            <ul className="space-y-2">
                                                {auditResult.details?.slice(0, 5).map((item: any, idx: number) => (
                                                    <li key={idx} className="text-sm text-gray-400">{item.msg || item.data?.impression}</li>
                                                ))}
                                            </ul>
                                        </StitchCard>
                                        <StitchCard className="col-span-full p-6 bg-gradient-to-r from-synapse-purple/10 to-transparent">
                                            <div className="flex justify-between items-center mb-4">
                                                <h3 className="text-xl font-bold">Bio Optimizer</h3>
                                                <NeonButton onClick={fixBio} disabled={loading}>✨ Auto-Fix Bio</NeonButton>
                                            </div>
                                            {bioOptions.length > 0 && (
                                                <div className="grid grid-cols-3 gap-4 mt-4">
                                                    {bioOptions.map((opt, i) => (
                                                        <div key={i} className="p-4 rounded-xl bg-black/40 border border-white/10 cursor-pointer hover:border-[#00f3ff]/50"
                                                            onClick={() => { navigator.clipboard.writeText(opt); toast.success("Copiado!"); }}
                                                        >
                                                            <span className="text-xs text-[#00f3ff]">OPÇÃO {i + 1}</span>
                                                            <p className="text-sm mt-1">{opt}</p>
                                                        </div>
                                                    ))}
                                                </div>
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
                                    <StitchCard className="p-8 border-l-4 border-l-red-500 bg-red-900/5">
                                        <h3 className="text-2xl font-bold text-white mb-4">
                                            Dossiê: {spyResult.scraped_data?.username || competitorHandle}
                                        </h3>
                                        <div className="grid gap-4">
                                            <div className="bg-black/30 p-4 rounded-lg">
                                                <h4 className="font-bold text-gray-300 mb-2">🎯 Ponto Fraco</h4>
                                                <p className="text-white">{spyResult.analysis?.weakness_exposed}</p>
                                            </div>
                                            <div className="bg-black/30 p-4 rounded-lg">
                                                <h4 className="font-bold text-gray-300 mb-2">Hooks para Roubar</h4>
                                                <ul className="list-disc list-inside text-sm text-gray-400">
                                                    {spyResult.analysis?.content_hooks_to_steal?.map((hook: string, i: number) => (
                                                        <li key={i}>{hook}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>
                                    </StitchCard>
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
                    </AnimatePresence>

                </div>
            </main>
        </div>
    );
}
