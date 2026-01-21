'use client';

import { Fragment, useState, useEffect, useRef } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, MagnifyingGlassIcon, PlayIcon, PauseIcon, MusicalNoteIcon, SparklesIcon, FireIcon, ArrowTrendingUpIcon, FunnelIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export interface ViralSound {
    id: string;
    title: string;
    author: string;
    cover_url: string;
    preview_url: string;
    duration: number;
    usage_count: number;
    category: string;
    // Campos de IA
    viral_score?: number;
    status?: string;  // normal, rising, exploding
    niche?: string;
    growth_rate?: number;
}

interface ViralSoundPickerProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (sound: ViralSound) => void;
    initialCategory?: string;
}

const CATEGORIES = [
    { id: 'General', label: 'Trending', icon: '🔥', color: 'from-orange-500 to-red-500' },
    { id: 'Dance', label: 'Dance', icon: '💃', color: 'from-pink-500 to-purple-500' },
    { id: 'Tech', label: 'Tech', icon: '🤖', color: 'from-cyan-500 to-blue-500' },
    { id: 'Meme', label: 'Meme', icon: '😂', color: 'from-yellow-500 to-orange-500' },
    { id: 'Lipsync', label: 'Lipsync', icon: '🎤', color: 'from-purple-500 to-pink-500' },
];

const NICHES = [
    { id: null, label: 'Todos', icon: '🌐' },
    { id: 'tech', label: 'Tech', icon: '💻' },
    { id: 'fitness', label: 'Fitness', icon: '💪' },
    { id: 'meme', label: 'Meme', icon: '🎭' },
    { id: 'dance', label: 'Dance', icon: '🕺' },
    { id: 'music', label: 'Música', icon: '🎵' },
    { id: 'lifestyle', label: 'Lifestyle', icon: '✨' },
];

function formatUsageCount(count: number): string {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(0)}K`;
    return count.toString();
}

function getStatusConfig(status?: string) {
    if (status === 'exploding') {
        return {
            badge: { emoji: '🔥', label: 'EXPLODING', bgClass: 'bg-gradient-to-r from-orange-500 to-red-500' },
            cardClass: 'ring-2 ring-orange-500/50 shadow-lg shadow-orange-500/20',
            glow: 'after:absolute after:inset-0 after:bg-gradient-to-r after:from-orange-500/10 after:to-red-500/10 after:rounded-xl after:animate-pulse'
        };
    }
    if (status === 'rising') {
        return {
            badge: { emoji: '📈', label: 'RISING', bgClass: 'bg-gradient-to-r from-green-500 to-emerald-500' },
            cardClass: 'ring-1 ring-green-500/30',
            glow: ''
        };
    }
    return { badge: null, cardClass: '', glow: '' };
}

function ViralScoreBar({ score }: { score: number }) {
    const getColor = () => {
        if (score >= 85) return 'from-orange-500 via-red-500 to-pink-500';
        if (score >= 60) return 'from-green-500 to-emerald-500';
        return 'from-blue-500 to-cyan-500';
    };

    return (
        <div className="relative h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
            <div
                className={clsx(
                    "absolute inset-y-0 left-0 bg-gradient-to-r rounded-full transition-all duration-500",
                    getColor(),
                    score >= 85 && "animate-pulse"
                )}
                style={{ width: `${Math.min(100, score)}%` }}
            />
            <div className="absolute right-0 top-1/2 -translate-y-1/2 text-[8px] font-bold text-white/60 pr-1">
                {score.toFixed(0)}
            </div>
        </div>
    );
}

function GrowthIndicator({ rate }: { rate: number }) {
    if (!rate || rate === 0) return null;

    const isPositive = rate > 0;

    return (
        <span className={clsx(
            "inline-flex items-center gap-0.5 text-[10px] font-bold",
            isPositive ? "text-green-400" : "text-red-400"
        )}>
            <ArrowTrendingUpIcon className={clsx("w-3 h-3", !isPositive && "rotate-180")} />
            {isPositive ? '+' : ''}{rate.toFixed(0)}%
        </span>
    );
}

export default function ViralSoundPicker({
    isOpen,
    onClose,
    onSelect,
    initialCategory = 'General'
}: ViralSoundPickerProps) {
    const [sounds, setSounds] = useState<ViralSound[]>([]);
    const [loading, setLoading] = useState(false);
    const [category, setCategory] = useState(initialCategory);
    const [niche, setNiche] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [playingId, setPlayingId] = useState<string | null>(null);
    const [showFilters, setShowFilters] = useState(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    // Fetch sounds when category/niche changes
    useEffect(() => {
        if (!isOpen) return;

        const fetchSounds = async () => {
            setLoading(true);
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                let endpoint: string;

                if (searchQuery) {
                    endpoint = `${API_URL}/api/v1/viral-sounds/search?query=${encodeURIComponent(searchQuery)}`;
                } else {
                    endpoint = `${API_URL}/api/v1/viral-sounds/trending?category=${category}`;
                    if (niche) {
                        endpoint += `&niche=${niche}`;
                    }
                }

                const res = await fetch(endpoint);
                if (res.ok) {
                    const data = await res.json();
                    setSounds(data.sounds || []);
                }
            } catch (e) {
                console.error('Error fetching sounds:', e);
            } finally {
                setLoading(false);
            }
        };

        const debounce = setTimeout(fetchSounds, searchQuery ? 300 : 0);
        return () => clearTimeout(debounce);
    }, [isOpen, category, niche, searchQuery]);

    // Stop audio when closing
    useEffect(() => {
        if (!isOpen && audioRef.current) {
            audioRef.current.pause();
            setPlayingId(null);
        }
    }, [isOpen]);

    const handlePlayPreview = (sound: ViralSound) => {
        if (playingId === sound.id) {
            audioRef.current?.pause();
            setPlayingId(null);
        } else {
            if (audioRef.current) {
                audioRef.current.pause();
            }
            audioRef.current = new Audio(sound.preview_url);
            audioRef.current.play().catch(() => {
                console.log('Preview not available');
            });
            audioRef.current.onended = () => setPlayingId(null);
            setPlayingId(sound.id);
        }
    };

    const handleSelect = (sound: ViralSound) => {
        if (audioRef.current) {
            audioRef.current.pause();
        }
        onSelect(sound);
        onClose();
    };

    // Contagem de sons por status
    const explodingCount = sounds.filter(s => s.status === 'exploding').length;
    const risingCount = sounds.filter(s => s.status === 'rising').length;

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/90 backdrop-blur-md" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-3xl transform overflow-hidden rounded-3xl bg-gradient-to-b from-[#1a1025] to-[#0d0a12] border border-white/10 shadow-2xl shadow-purple-500/10 transition-all">
                                {/* Header Premium */}
                                <div className="relative p-6 border-b border-white/5">
                                    {/* Background Glow */}
                                    <div className="absolute inset-0 bg-gradient-to-r from-synapse-purple/10 via-transparent to-synapse-cyan/10" />

                                    <div className="relative flex justify-between items-center mb-4">
                                        <Dialog.Title className="text-xl font-bold text-white flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-synapse-purple to-synapse-cyan flex items-center justify-center">
                                                <SparklesIcon className="w-5 h-5 text-white" />
                                            </div>
                                            <div>
                                                <span>Seletor de Música Viral</span>
                                                <p className="text-xs font-normal text-gray-400 mt-0.5">
                                                    Sons com potencial de viralização detectados por IA
                                                </p>
                                            </div>
                                        </Dialog.Title>
                                        <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-white/5 rounded-lg">
                                            <XMarkIcon className="w-5 h-5" />
                                        </button>
                                    </div>

                                    {/* Stats Bar */}
                                    {sounds.length > 0 && (
                                        <div className="flex gap-4 mb-4 text-sm">
                                            {explodingCount > 0 && (
                                                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/30">
                                                    <FireIcon className="w-4 h-4 text-orange-400" />
                                                    <span className="text-orange-300 font-medium">{explodingCount} explodindo</span>
                                                </div>
                                            )}
                                            {risingCount > 0 && (
                                                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30">
                                                    <ArrowTrendingUpIcon className="w-4 h-4 text-green-400" />
                                                    <span className="text-green-300 font-medium">{risingCount} em alta</span>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Search + Filter Toggle */}
                                    <div className="flex gap-2">
                                        <div className="relative flex-1">
                                            <MagnifyingGlassIcon className="absolute left-4 top-3 w-5 h-5 text-gray-500 pointer-events-none" />
                                            <input
                                                type="text"
                                                placeholder="Buscar por título ou artista..."
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-11 pr-4 text-sm text-white placeholder:text-gray-500 focus:border-synapse-purple focus:ring-2 focus:ring-synapse-purple/20 outline-none transition-all"
                                            />
                                        </div>
                                        <button
                                            onClick={() => setShowFilters(!showFilters)}
                                            className={clsx(
                                                "flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-all",
                                                showFilters
                                                    ? "bg-synapse-purple/20 border-synapse-purple text-synapse-purple"
                                                    : "bg-white/5 border-white/10 text-gray-400 hover:text-white hover:border-white/20"
                                            )}
                                        >
                                            <FunnelIcon className="w-5 h-5" />
                                            <span className="text-sm font-medium">Filtros</span>
                                        </button>
                                    </div>

                                    {/* Filters Panel */}
                                    {showFilters && (
                                        <div className="mt-4 p-4 bg-white/5 rounded-xl border border-white/5 space-y-4">
                                            {/* Nichos */}
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                                                    Filtrar por Nicho
                                                </label>
                                                <div className="flex flex-wrap gap-2">
                                                    {NICHES.map((n) => (
                                                        <button
                                                            key={n.id || 'all'}
                                                            onClick={() => setNiche(n.id)}
                                                            className={clsx(
                                                                "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                                                                niche === n.id
                                                                    ? "bg-synapse-purple text-white shadow-lg shadow-synapse-purple/30"
                                                                    : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white"
                                                            )}
                                                        >
                                                            {n.icon} {n.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Category Tabs */}
                                    {!searchQuery && (
                                        <div className="flex gap-2 mt-4 overflow-x-auto pb-2 custom-scrollbar">
                                            {CATEGORIES.map((cat) => (
                                                <button
                                                    key={cat.id}
                                                    onClick={() => setCategory(cat.id)}
                                                    className={clsx(
                                                        "px-5 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all flex items-center gap-2",
                                                        category === cat.id
                                                            ? `bg-gradient-to-r ${cat.color} text-white shadow-lg`
                                                            : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/5"
                                                    )}
                                                >
                                                    <span>{cat.icon}</span>
                                                    {cat.label}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Sound Grid */}
                                <div className="p-6 max-h-[450px] overflow-y-auto custom-scrollbar">
                                    {loading ? (
                                        <div className="flex flex-col items-center justify-center py-16">
                                            <div className="relative w-16 h-16">
                                                <div className="absolute inset-0 border-4 border-synapse-purple/20 rounded-full" />
                                                <div className="absolute inset-0 border-4 border-synapse-purple border-t-transparent rounded-full animate-spin" />
                                            </div>
                                            <p className="text-sm text-gray-400 mt-4">Analisando tendências...</p>
                                        </div>
                                    ) : sounds.length === 0 ? (
                                        <div className="text-center py-16">
                                            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-white/5 flex items-center justify-center">
                                                <MusicalNoteIcon className="w-8 h-8 text-gray-500" />
                                            </div>
                                            <p className="text-gray-400 font-medium">Nenhuma música encontrada</p>
                                            <p className="text-xs text-gray-500 mt-1">Tente outra categoria ou termo de busca</p>
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            {sounds.map((sound, index) => {
                                                const statusConfig = getStatusConfig(sound.status);

                                                return (
                                                    <div
                                                        key={sound.id}
                                                        className={clsx(
                                                            "relative flex items-center gap-4 p-4 rounded-2xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.06] hover:border-white/10 transition-all group cursor-pointer",
                                                            statusConfig.cardClass,
                                                            statusConfig.glow
                                                        )}
                                                        onClick={() => handleSelect(sound)}
                                                        style={{ animationDelay: `${index * 50}ms` }}
                                                    >
                                                        {/* Rank Number */}
                                                        <div className="absolute -left-2 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center text-[10px] font-bold text-gray-400">
                                                            {index + 1}
                                                        </div>

                                                        {/* Cover / Play Button */}
                                                        <div className="relative w-16 h-16 rounded-xl bg-gradient-to-br from-synapse-purple/30 to-synapse-cyan/30 flex items-center justify-center overflow-hidden flex-shrink-0 shadow-lg">
                                                            {sound.cover_url && sound.cover_url.startsWith('http') ? (
                                                                <img
                                                                    src={sound.cover_url}
                                                                    alt={sound.title}
                                                                    className="w-full h-full object-cover"
                                                                    onError={(e) => {
                                                                        (e.target as HTMLImageElement).style.display = 'none';
                                                                    }}
                                                                />
                                                            ) : (
                                                                <MusicalNoteIcon className="w-8 h-8 text-white/50" />
                                                            )}
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    handlePlayPreview(sound);
                                                                }}
                                                                className={clsx(
                                                                    "absolute inset-0 flex items-center justify-center transition-all",
                                                                    playingId === sound.id
                                                                        ? "bg-synapse-purple/90"
                                                                        : "bg-black/50 opacity-0 group-hover:opacity-100"
                                                                )}
                                                            >
                                                                {playingId === sound.id ? (
                                                                    <PauseIcon className="w-7 h-7 text-white" />
                                                                ) : (
                                                                    <PlayIcon className="w-7 h-7 text-white" />
                                                                )}
                                                            </button>
                                                        </div>

                                                        {/* Info */}
                                                        <div className="flex-1 min-w-0 space-y-2">
                                                            <div className="flex items-center gap-2">
                                                                <p className="text-sm font-semibold text-white truncate group-hover:text-synapse-cyan transition-colors">
                                                                    {sound.title}
                                                                </p>
                                                                {statusConfig.badge && (
                                                                    <span className={clsx(
                                                                        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold text-white shadow-lg",
                                                                        statusConfig.badge.bgClass
                                                                    )}>
                                                                        {statusConfig.badge.emoji} {statusConfig.badge.label}
                                                                    </span>
                                                                )}
                                                            </div>
                                                            <p className="text-xs text-gray-500 truncate">
                                                                {sound.author}
                                                            </p>
                                                            {/* Viral Score Bar */}
                                                            {sound.viral_score !== undefined && (
                                                                <ViralScoreBar score={sound.viral_score} />
                                                            )}
                                                        </div>

                                                        {/* Stats */}
                                                        <div className="text-right flex-shrink-0 space-y-1">
                                                            <div className="flex items-center justify-end gap-2">
                                                                <span className="text-sm font-bold text-synapse-cyan">
                                                                    {formatUsageCount(sound.usage_count)}
                                                                </span>
                                                                <GrowthIndicator rate={sound.growth_rate || 0} />
                                                            </div>
                                                            <div className="flex items-center justify-end gap-2 text-[10px] text-gray-500">
                                                                <span>{sound.duration}s</span>
                                                                {sound.niche && sound.niche !== 'general' && (
                                                                    <span className="px-1.5 py-0.5 rounded bg-white/5 text-gray-400">
                                                                        #{sound.niche}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Select indicator */}
                                                        <div className="w-10 h-10 rounded-xl border border-white/10 flex items-center justify-center opacity-0 group-hover:opacity-100 group-hover:border-synapse-purple/50 group-hover:bg-synapse-purple/10 transition-all">
                                                            <span className="text-synapse-purple text-xl font-light">+</span>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>

                                {/* Footer Premium */}
                                <div className="p-4 border-t border-white/5 bg-gradient-to-r from-black/40 via-transparent to-black/40">
                                    <div className="flex items-center justify-between">
                                        <p className="text-[10px] text-gray-500 font-mono flex items-center gap-2">
                                            <SparklesIcon className="w-3 h-3" />
                                            Powered by Synapse AI • Atualizado a cada 30 min
                                        </p>
                                        <div className="flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                            <span className="text-[10px] text-gray-400">Live Data</span>
                                        </div>
                                    </div>
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
