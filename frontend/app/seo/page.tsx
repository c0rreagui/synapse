'use client';

import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import { EyeIcon, MagnifyingGlassIcon, SparklesIcon, ArrowPathIcon, CheckIcon, ClipboardIcon } from '@heroicons/react/24/outline';
import { TikTokProfile } from '../types';
import { toast } from 'sonner';
import clsx from 'clsx';
import { motion } from 'framer-motion';

export default function SEOPage() {
    const [activeTab, setActiveTab] = useState<'AUDIT' | 'SPY' | 'DISCOVERY'>('AUDIT');
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
    const [selectedProfileId, setSelectedProfileId] = useState<string>('');
    const [loading, setLoading] = useState(false);

    // Audit State
    const [auditResult, setAuditResult] = useState<any>(null);
    const [bioOptions, setBioOptions] = useState<string[]>([]);

    // Spy State
    const [competitorHandle, setCompetitorHandle] = useState('');
    const [spyResult, setSpyResult] = useState<any>(null);

    // Discovery State
    const [hashtagForm, setHashtagForm] = useState({ niche: '', topic: '' });
    const [hashtagResult, setHashtagResult] = useState<any>(null);

    // Initial Load
    useEffect(() => {
        fetch('http://localhost:8000/api/v1/profiles')
            .then(res => res.json())
            .then(data => {
                setProfiles(data);
                if (data.length > 0) setSelectedProfileId(data[0].id);
            });
    }, []);

    // Actions
    const runAudit = async () => {
        if (!selectedProfileId) return;
        setLoading(true);
        setAuditResult(null);
        try {
            const res = await fetch(`http://localhost:8000/api/v1/oracle/seo/audit/${selectedProfileId}`, { method: 'POST' });
            if (!res.ok) throw new Error("Audit failed");
            const data = await res.json();
            setAuditResult(data);
            toast.success("Auditoria visionária concluída!");
        } catch (e) {
            toast.error("Erro na auditoria.");
        } finally {
            setLoading(false);
        }
    };

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
            toast.success("Dossiê gerado com sucesso!");
        } catch (e) {
            toast.error("Erro ao espionar.");
        } finally {
            setLoading(false);
        }
    };

    const fixBio = async () => {
        // if (!auditResult?.profile_overiew?.bio) return; // Allow empty bio fix
        setLoading(true);
        try {
            const currentBio = auditResult?.profile_overiew?.bio || "Nova conta, sem bio definida.";
            const res = await fetch(`http://localhost:8000/api/v1/oracle/seo/fix-bio`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_bio: currentBio,
                    niche: "General" // Could make this an input
                })
            });
            const data = await res.json();
            setBioOptions(data.options || []);
        } finally {
            setLoading(false);
        }
    };

    const runHastags = async () => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/v1/oracle/seo/hashtags`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(hashtagForm)
            });
            const data = await res.json();
            setHashtagResult(data);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-[#0f0a15] text-white font-sans overflow-hidden">
            <Sidebar />
            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern">

                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h2 className="text-3xl font-bold flex items-center gap-3">
                            <EyeIcon className="w-8 h-8 text-synapse-purple" />
                            SEO & Discovery <span className="text-xs bg-synapse-purple px-2 py-0.5 rounded text-white tracking-widest">TURBO</span>
                        </h2>
                        <p className="text-gray-500 font-mono mt-1">{'// ORACLE_VISION_MODULE_V2'}</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-4 mb-6 border-b border-white/10 pb-1">
                    {[
                        { id: 'AUDIT', label: 'My Audit', icon: SparklesIcon },
                        { id: 'SPY', label: 'Competitor Spy', icon: MagnifyingGlassIcon },
                        { id: 'DISCOVERY', label: 'Discovery Tools', icon: ArrowPathIcon }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={clsx(
                                "flex items-center gap-2 px-4 py-2 text-sm font-bold uppercase tracking-wide transition-all",
                                activeTab === tab.id
                                    ? "text-synapse-purple border-b-2 border-synapse-purple bg-synapse-purple/5"
                                    : "text-gray-500 hover:text-white"
                            )}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="min-h-[400px]">

                    {/* --- AUDIT TAB --- */}
                    {activeTab === 'AUDIT' && (
                        <div className="space-y-6 animate-fade-in">
                            <div className="flex gap-4 items-end bg-[#13111a] p-4 rounded-xl border border-white/5">
                                <div className="flex-1">
                                    <label className="text-xs text-gray-500 font-bold block mb-2">SELECIONE O PERFIL ALVO</label>
                                    <select
                                        value={selectedProfileId}
                                        onChange={(e) => setSelectedProfileId(e.target.value)}
                                        className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white outline-none focus:border-synapse-purple transition-all"
                                    >
                                        {profiles.map(p => (
                                            <option key={p.id} value={p.id}>{p.label || p.username} ({p.username})</option>
                                        ))}
                                    </select>
                                </div>
                                <NeonButton onClick={runAudit} disabled={loading} className="py-3 px-8">
                                    {loading ? "Analysando VIsual..." : "Executar Auditoria Visionária"}
                                </NeonButton>
                            </div>

                            {auditResult && (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {/* Score Card */}
                                    <StitchCard className="p-6 relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 p-4 opacity-50 font-mono text-6xl font-bold text-white/5 group-hover:text-synapse-purple/10 transition-colors">
                                            {auditResult.total_score}
                                        </div>
                                        <h3 className="text-xl font-bold mb-4">Vision Score</h3>
                                        <div className="flex items-center gap-6">
                                            <div className="relative w-32 h-32 flex items-center justify-center">
                                                <svg className="w-full h-full transform -rotate-90">
                                                    <circle cx="64" cy="64" r="60" stroke="#333" strokeWidth="8" fill="transparent" />
                                                    <circle cx="64" cy="64" r="60" stroke="#8b5cf6" strokeWidth="8" fill="transparent"
                                                        strokeDasharray={377}
                                                        strokeDashoffset={377 - (377 * auditResult.total_score) / 100}
                                                        className="transition-all duration-1000 ease-out"
                                                    />
                                                </svg>
                                                <span className="absolute text-3xl font-bold">{auditResult.total_score}</span>
                                            </div>
                                            <div>
                                                <p className="font-bold text-lg mb-1">{auditResult.vision_score > 70 ? "Estética Profissional" : "Estética Amadora"}</p>
                                                <p className="text-sm text-gray-400">Baseado na análise da Llama Vision 3.2 do seu Avatar e Bio.</p>
                                            </div>
                                        </div>
                                    </StitchCard>

                                    {/* Feedback List */}
                                    <StitchCard className="p-6">
                                        <h3 className="text-xl font-bold mb-4">Relatório Tático</h3>
                                        <ul className="space-y-3">
                                            {auditResult.details?.map((item: any, idx: number) => (
                                                <li key={idx} className={clsx(
                                                    "p-3 rounded-lg border text-sm flex gap-3",
                                                    item.type === 'vision' ? "bg-purple-900/10 border-purple-500/30 text-purple-200" :
                                                        item.type === 'error' ? "bg-red-900/10 border-red-500/30 text-red-200" :
                                                            item.type === 'warning' ? "bg-yellow-900/10 border-yellow-500/30 text-yellow-200" :
                                                                "bg-green-900/10 border-green-500/30 text-green-200"
                                                )}>
                                                    {item.type === 'vision' && <EyeIcon className="w-5 h-5 shrink-0" />}
                                                    {item.type === 'warning' && <span className="text-lg">⚠️</span>}
                                                    {item.type === 'success' && <CheckIcon className="w-5 h-5 shrink-0" />}

                                                    <div>
                                                        {item.type === 'vision' ? (
                                                            <>
                                                                <p className="font-bold">Análise Visual:</p>
                                                                <p className="italic">&quot;{item.data.impression}&quot;</p>
                                                                <p className="mt-1 text-xs opacity-70">Pros: {item.data.pros?.join(", ")}</p>
                                                            </>
                                                        ) : (
                                                            item.msg
                                                        )}
                                                    </div>
                                                </li>
                                            ))}
                                        </ul>
                                    </StitchCard>

                                    {/* Bio Fixer */}
                                    <StitchCard className="col-span-full p-6 bg-gradient-to-r from-synapse-purple/10 to-transparent">
                                        <div className="flex justify-between items-center mb-4">
                                            <div>
                                                <h3 className="text-xl font-bold">Bio Optimizer</h3>
                                                <p className="text-gray-400 text-sm">Atual: &quot;{auditResult.profile_overiew.bio}&quot;</p>
                                            </div>
                                            <NeonButton variant="primary" className="border-synapse-purple text-synapse-purple hover:bg-synapse-purple/10" onClick={fixBio} disabled={loading}>
                                                ✨ Auto-Fix Bio
                                            </NeonButton>
                                        </div>

                                        {bioOptions.length > 0 && (
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                                                {bioOptions.map((opt, i) => (
                                                    <div key={i} className="p-4 rounded-xl bg-black/40 border border-white/10 hover:border-synapse-purple/50 cursor-pointer group transition-all"
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(opt);
                                                            toast.success("Copiado!");
                                                        }}
                                                    >
                                                        <div className="flex justify-between mb-2">
                                                            <span className="text-xs font-mono text-synapse-purple">OPÇÃO {i + 1}</span>
                                                            <ClipboardIcon className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                                                        </div>
                                                        <p className="text-sm font-medium">{opt}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </StitchCard>
                                </div>
                            )}
                        </div>
                    )}

                    {/* --- SPY TAB --- */}
                    {activeTab === 'SPY' && (
                        <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
                            <div className="bg-[#13111a] p-8 rounded-2xl border border-white/10 text-center">
                                <h3 className="text-2xl font-bold mb-2">Espionagem Industrial</h3>
                                <p className="text-gray-400 mb-6">Insira o @ do concorrente para revelar suas táticas.</p>
                                <div className="flex gap-2 max-w-md mx-auto">
                                    <input
                                        type="text"
                                        placeholder="@concorrente"
                                        value={competitorHandle}
                                        onChange={e => setCompetitorHandle(e.target.value)}
                                        className="flex-1 bg-black text-white px-4 rounded-lg border border-white/20 focus:border-synapse-purple outline-none"
                                    />
                                    <NeonButton onClick={runSpy} disabled={loading}>
                                        {loading ? "Infiltrando..." : "Hackear"}
                                    </NeonButton>
                                </div>
                            </div>

                            {spyResult && (
                                <StitchCard className="p-8 border-l-4 border-l-red-500 bg-red-900/5">
                                    <div className="flex items-center gap-4 mb-6">
                                        <div className="p-3 bg-red-500/10 rounded-full text-red-500">
                                            <MagnifyingGlassIcon className="w-8 h-8" />
                                        </div>
                                        <div>
                                            <h3 className="text-2xl font-bold text-white flex items-center gap-3">
                                                Dossiê Confidencial: {spyResult.scraped_data.username}
                                                {spyResult.analysis.niche_detected && (
                                                    <span className="text-xs bg-synapse-purple/20 text-synapse-purple px-2 py-1 rounded border border-synapse-purple/50 uppercase tracking-widest">
                                                        {spyResult.analysis.niche_detected}
                                                    </span>
                                                )}
                                            </h3>
                                            <p className="text-red-400 font-mono text-xs uppercase tracking-widest">TOP SECRET // EYES ONLY</p>
                                        </div>
                                    </div>

                                    <div className="grid gap-6">
                                        <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                                            <h4 className="font-bold text-gray-300 mb-2 border-b border-white/10 pb-2">🎯 Ponto Fraco Exposto</h4>
                                            <p className="text-lg text-white max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">{spyResult.analysis.weakness_exposed}</p>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                                                <h4 className="font-bold text-gray-300 mb-2">Hooks para Roubar</h4>
                                                <ul className="list-disc list-inside text-sm text-gray-400 space-y-1 max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">
                                                    {spyResult.analysis.content_hooks_to_steal?.map((hook: string, i: number) => (
                                                        <li key={i} className="mb-2">{hook}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                            <div className="bg-black/30 p-4 rounded-lg border border-white/5">
                                                <h4 className="font-bold text-gray-300 mb-2">Estratégia de Crescimento</h4>
                                                <p className="text-sm text-gray-400 leading-relaxed max-h-[200px] overflow-y-auto pr-2 custom-scrollbar">{spyResult.analysis.growth_strategy_detected}</p>
                                            </div>
                                        </div>
                                    </div>
                                </StitchCard>
                            )}
                        </div>
                    )}

                    {/* --- DISCOVERY TAB --- */}
                    {activeTab === 'DISCOVERY' && (
                        <div className="max-w-4xl mx-auto animate-fade-in">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <StitchCard className="p-6">
                                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                        <ArrowPathIcon className="w-5 h-5 text-synapse-purple" />
                                        Gerador de Hashtags
                                    </h3>
                                    <div className="space-y-4">
                                        <div>
                                            <label className="text-xs text-gray-500 font-bold block mb-1">NICHO</label>
                                            <input type="text" placeholder="Ex: Marketing Digital" className="w-full bg-black/50 border border-white/10 px-3 py-2 rounded-lg text-white"
                                                value={hashtagForm.niche} onChange={e => setHashtagForm({ ...hashtagForm, niche: e.target.value })}
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-gray-500 font-bold block mb-1">TÓPICO DO VÍDEO</label>
                                            <input type="text" placeholder="Ex: Como ganhar dinheiro online" className="w-full bg-black/50 border border-white/10 px-3 py-2 rounded-lg text-white"
                                                value={hashtagForm.topic} onChange={e => setHashtagForm({ ...hashtagForm, topic: e.target.value })}
                                            />
                                        </div>
                                        <NeonButton className="w-full justify-center" onClick={runHastags} disabled={loading}>
                                            {loading ? "Minerando Tags..." : "Gerar Hashtags Otimizadas"}
                                        </NeonButton>
                                    </div>
                                </StitchCard>

                                <div className="space-y-4">
                                    {hashtagResult ? (
                                        <>
                                            {['broad', 'niche', 'trending'].map((cat) => (
                                                <motion.div
                                                    initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                                                    key={cat} className="p-4 rounded-xl bg-[#13111a] border border-white/10"
                                                >
                                                    <div className="flex justify-between items-center mb-2">
                                                        <h4 className="text-sm font-bold capitalize text-gray-300">{cat} Tags</h4>
                                                        <button className="text-xs text-synapse-purple hover:underline" onClick={() => navigator.clipboard.writeText(hashtagResult[cat].join(' '))}>Copy</button>
                                                    </div>
                                                    <div className="flex flex-wrap gap-2">
                                                        {hashtagResult[cat]?.map((tag: string) => (
                                                            <span key={tag} className="px-2 py-0.5 rounded bg-white/5 text-xs text-gray-400 border border-white/5 hover:border-synapse-purple/50 transition-colors">
                                                                {tag}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </>
                                    ) : (
                                        <div className="h-full flex items-center justify-center border border-dashed border-white/10 rounded-xl text-gray-600">
                                            Resultados aparecerão aqui...
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            </main>
        </div>
    );
}
