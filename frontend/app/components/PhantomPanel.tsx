'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient } from '../lib/api';
import { toast } from 'sonner';
import clsx from 'clsx';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PhantomStatus {
    enabled: boolean;
    persona_key?: string;
    trust_score?: number;
    trust_status?: 'nascent' | 'warming' | 'building' | 'established' | 'trusted' | 'organic';
    actions_today?: number;
    last_session?: string | null;
}

interface Persona {
    key: string;
    name: string;
    description: string;
    engagement_style: string;
    primary_niches: string[];
    avg_daily_sessions: number;
    avg_session_minutes: number;
}

interface PhantomPanelProps {
    profileDbId: number;
    /** Pre-fetched status from the bulk /all-status call. Pass null if not yet loaded. */
    initialStatus: PhantomStatus | null;
    onStatusChange?: () => void;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const TRUST_COLORS: Record<string, { text: string; bg: string; border: string; dot: string }> = {
    nascent:     { text: 'text-slate-400',   bg: 'bg-slate-400/10',   border: 'border-slate-400/20',   dot: 'bg-slate-400' },
    warming:     { text: 'text-blue-400',    bg: 'bg-blue-400/10',    border: 'border-blue-400/20',    dot: 'bg-blue-400' },
    building:    { text: 'text-cyan-400',    bg: 'bg-cyan-400/10',    border: 'border-cyan-400/20',    dot: 'bg-cyan-400' },
    established: { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20', dot: 'bg-emerald-400' },
    trusted:     { text: 'text-violet-400',  bg: 'bg-violet-400/10',  border: 'border-violet-400/20',  dot: 'bg-violet-400' },
    organic:     { text: 'text-fuchsia-400', bg: 'bg-fuchsia-400/10', border: 'border-fuchsia-400/20', dot: 'bg-fuchsia-400' },
};

const PERSONA_EMOJI: Record<string, string> = {
    aesthetic_curator: '🎨',
    meme_agent:        '💀',
    study_tok:         '📚',
    music_head:        '🎵',
    brazilian_viral:   '🇧🇷',
    fitness_girlie:    '💪',
};

function formatLastSession(iso: string | null | undefined): string {
    if (!iso) return 'nunca';
    const diff = Date.now() - new Date(iso).getTime();
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    if (h >= 24) return `${Math.floor(h / 24)}d atrás`;
    if (h > 0)   return `${h}h atrás`;
    if (m > 0)   return `${m}m atrás`;
    return 'agora';
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function PhantomPanel({ profileDbId, initialStatus, onStatusChange }: PhantomPanelProps) {
    const [status, setStatus] = useState<PhantomStatus | null>(initialStatus);
    const [expanded, setExpanded] = useState(false);
    const [personas, setPersonas] = useState<Persona[]>([]);
    const [selectedPersona, setSelectedPersona] = useState<string>('brazilian_viral');
    const [loading, setLoading] = useState(false);
    const [dispatching, setDispatching] = useState(false);
    // Guard against concurrent fetches — useRef avoids stale-closure race condition
    const personasFetchedRef = useRef(false);

    // Sync initialStatus once it arrives from parent
    useEffect(() => {
        if (initialStatus !== null) setStatus(initialStatus);
    }, [initialStatus]);

    const loadPersonas = useCallback(async () => {
        if (personasFetchedRef.current) return;
        personasFetchedRef.current = true;
        try {
            const data = await apiClient.get<{ personas: Persona[] }>('/api/v1/phantom/personas');
            setPersonas(data.personas);
        } catch {
            // non-critical — fallback personas are used
            personasFetchedRef.current = false; // allow retry on next expand
        }
    }, []);

    const isActive = status?.enabled === true;
    const trustColors = TRUST_COLORS[status?.trust_status ?? 'nascent'];

    const handleExpand = () => {
        // Only load personas when opening the inactive state (persona selector is only shown there)
        if (!expanded && !isActive) loadPersonas();
        setExpanded(v => !v);
    };

    const handleEnable = async () => {
        setLoading(true);
        try {
            await apiClient.post('/api/v1/phantom/assign-persona', {
                profile_id: profileDbId,
                persona_key: selectedPersona,
            });
            setStatus({
                enabled: true,
                persona_key: selectedPersona,
                trust_score: 0,
                trust_status: 'nascent',
                actions_today: 0,
                last_session: null,
            });
            setExpanded(false);
            toast.success('Phantom ativado', {
                description: `Persona ${selectedPersona} atribuída.`,
            });
            onStatusChange?.();
        } catch (e: any) {
            toast.error('Erro ao ativar Phantom', {
                description: e?.data?.detail || 'Erro desconhecido',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleDisable = async () => {
        setLoading(true);
        try {
            await apiClient.delete(`/api/v1/phantom/persona/${profileDbId}`);
            setStatus({ enabled: false });
            setExpanded(false);
            toast.success('Phantom desativado');
            onStatusChange?.();
        } catch (e: any) {
            toast.error('Erro ao desativar Phantom', {
                description: e?.data?.detail || 'Erro desconhecido',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleTriggerSession = async () => {
        setDispatching(true);
        try {
            await apiClient.post('/api/v1/phantom/simulate', { profile_id: profileDbId });
            toast.success('Sessão Phantom disparada', {
                description: 'Rodando em background. Trust score atualiza ao concluir.',
            });
        } catch (e: any) {
            const detail = e?.data?.detail || 'Erro desconhecido';
            if (detail.includes('disabled')) {
                toast.error('Phantom desabilitado', { description: 'Defina PHANTOM_ENABLED=true no .env' });
            } else {
                toast.error('Erro ao disparar sessão', { description: detail });
            }
        } finally {
            setDispatching(false);
        }
    };

    // ─── Inactive bar ─────────────────────────────────────────────────────────
    if (!isActive) {
        return (
            <div className="px-4 pb-3" onClick={e => e.stopPropagation()}>
                {!expanded ? (
                    <button
                        onClick={handleExpand}
                        className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-md border border-dashed border-white/10 text-white/25 hover:border-violet-500/30 hover:text-violet-400/60 transition-all text-[9px] font-mono uppercase tracking-widest"
                    >
                        <span className="text-[11px]">👻</span>
                        ativar phantom
                    </button>
                ) : (
                    <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-3 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-violet-300 font-mono text-[9px] uppercase tracking-widest font-bold">Phantom — Escolha uma persona</span>
                            <button onClick={() => setExpanded(false)} className="text-white/30 hover:text-white text-[10px]">✕</button>
                        </div>

                        <div className="grid grid-cols-2 gap-1.5">
                            {(personas.length > 0 ? personas : FALLBACK_PERSONAS).map(p => (
                                <button
                                    key={p.key}
                                    onClick={() => setSelectedPersona(p.key)}
                                    className={clsx(
                                        'text-left p-2 rounded-md border text-[9px] transition-all',
                                        selectedPersona === p.key
                                            ? 'border-violet-500/60 bg-violet-500/15 text-violet-200'
                                            : 'border-white/8 bg-white/3 text-white/40 hover:border-white/20 hover:text-white/60'
                                    )}
                                >
                                    <div className="flex items-center gap-1 mb-0.5">
                                        <span>{PERSONA_EMOJI[p.key] ?? '🎭'}</span>
                                        <span className="font-bold uppercase">{p.name}</span>
                                    </div>
                                    <div className="text-[8px] opacity-70 leading-tight line-clamp-2">{p.description}</div>
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={handleEnable}
                            disabled={loading}
                            className="w-full py-1.5 rounded-md bg-violet-500/20 hover:bg-violet-500/30 border border-violet-500/40 text-violet-300 text-[9px] font-bold uppercase tracking-widest transition-all disabled:opacity-50"
                        >
                            {loading ? 'Ativando...' : `Ativar com ${PERSONA_EMOJI[selectedPersona] ?? ''} ${selectedPersona}`}
                        </button>
                    </div>
                )}
            </div>
        );
    }

    // ─── Active bar ───────────────────────────────────────────────────────────
    return (
        <div className="px-4 pb-3" onClick={e => e.stopPropagation()}>
            {/* Compact bar */}
            <div
                className={clsx(
                    'flex items-center gap-2 px-3 py-1.5 rounded-md border cursor-pointer transition-all',
                    trustColors.bg, trustColors.border,
                    expanded && 'rounded-b-none border-b-0'
                )}
                onClick={handleExpand}
            >
                <span className={clsx('w-1.5 h-1.5 rounded-full shrink-0 animate-pulse', trustColors.dot)} />
                <span className="text-white/40 font-mono text-[8px] uppercase tracking-widest">👻 Phantom</span>
                <span className="flex-1" />

                {/* Trust score chip */}
                <span className={clsx('font-mono text-[9px] font-bold', trustColors.text)}>
                    {status.trust_score?.toFixed(0) ?? '0'} pts
                </span>
                <span className={clsx('font-mono text-[8px] uppercase px-1.5 py-0.5 rounded', trustColors.bg, trustColors.text, trustColors.border, 'border')}>
                    {status.trust_status}
                </span>
                <span className="text-white/20 text-[9px] font-mono">{PERSONA_EMOJI[status.persona_key ?? ''] ?? '🎭'}</span>
                <span className="material-symbols-outlined text-[12px] text-white/20">
                    {expanded ? 'expand_less' : 'expand_more'}
                </span>
            </div>

            {/* Expanded details */}
            {expanded && (
                <div className={clsx(
                    'rounded-b-md border px-3 py-3 space-y-3',
                    trustColors.bg, trustColors.border
                )}>
                    {/* Stats row */}
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div>
                            <div className={clsx('font-mono text-sm font-bold', trustColors.text)}>
                                {status.trust_score?.toFixed(1) ?? '0.0'}
                            </div>
                            <div className="text-white/30 text-[8px] uppercase tracking-widest">Trust</div>
                        </div>
                        <div>
                            <div className="font-mono text-sm font-bold text-white/70">
                                {status.actions_today ?? 0}
                            </div>
                            <div className="text-white/30 text-[8px] uppercase tracking-widest">Ações hoje</div>
                        </div>
                        <div>
                            <div className="font-mono text-xs font-bold text-white/70">
                                {formatLastSession(status.last_session)}
                            </div>
                            <div className="text-white/30 text-[8px] uppercase tracking-widest">Última sessão</div>
                        </div>
                    </div>

                    {/* Trust progress bar */}
                    <div className="space-y-1">
                        <div className="flex justify-between items-center">
                            <span className="text-white/30 text-[8px] uppercase tracking-widest">Progresso</span>
                            <span className={clsx('text-[8px] font-mono uppercase', trustColors.text)}>
                                {status.trust_status}
                            </span>
                        </div>
                        <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                            <div
                                className={clsx('h-full rounded-full transition-all duration-700', trustColors.dot)}
                                style={{ width: `${Math.min(100, status.trust_score ?? 0)}%` }}
                            />
                        </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2">
                        <button
                            onClick={handleTriggerSession}
                            disabled={dispatching}
                            className={clsx(
                                'flex-1 py-1.5 rounded-md border text-[9px] font-bold uppercase tracking-widest transition-all disabled:opacity-50',
                                trustColors.bg, trustColors.border, trustColors.text,
                                'hover:brightness-125'
                            )}
                        >
                            {dispatching ? (
                                <span className="flex items-center justify-center gap-1">
                                    <span className="material-symbols-outlined text-[10px] animate-spin">hourglass_empty</span>
                                    Disparando...
                                </span>
                            ) : (
                                <span className="flex items-center justify-center gap-1">
                                    <span className="material-symbols-outlined text-[10px]">play_arrow</span>
                                    Rodar agora
                                </span>
                            )}
                        </button>
                        <button
                            onClick={handleDisable}
                            disabled={loading}
                            className="px-3 py-1.5 rounded-md border border-red-500/20 bg-red-500/5 text-red-400/60 hover:text-red-400 hover:border-red-500/40 text-[9px] font-bold uppercase tracking-widest transition-all disabled:opacity-50"
                        >
                            Desativar
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

// Fallback while personas API loads
const FALLBACK_PERSONAS: Persona[] = [
    { key: 'brazilian_viral', name: 'BR Viral Watcher', description: 'Humor, cortes, funk, drama. PT-BR nativo.', engagement_style: 'reactor', primary_niches: [], avg_daily_sessions: 6, avg_session_minutes: 25 },
    { key: 'meme_agent', name: 'Meme Chaos Agent', description: 'Vive por memes e conteúdo caótico. Comenta muito.', engagement_style: 'reactor', primary_niches: [], avg_daily_sessions: 7, avg_session_minutes: 25 },
    { key: 'aesthetic_curator', name: 'Aesthetic Curator', description: 'Salva tudo, comenta pouco. Fashion e design.', engagement_style: 'lurker', primary_niches: [], avg_daily_sessions: 5, avg_session_minutes: 20 },
    { key: 'study_tok', name: 'StudyTok Scholar', description: 'Produtividade e educação. Uso estruturado.', engagement_style: 'socializer', primary_niches: [], avg_daily_sessions: 4, avg_session_minutes: 15 },
    { key: 'music_head', name: 'Music Discovery Head', description: 'Obcecado com novos sons e artistas underground.', engagement_style: 'socializer', primary_niches: [], avg_daily_sessions: 6, avg_session_minutes: 30 },
    { key: 'fitness_girlie', name: 'Fitness Girlie', description: 'Gym, receitas saudáveis, wellness.', engagement_style: 'lurker', primary_niches: [], avg_daily_sessions: 4, avg_session_minutes: 18 },
];
