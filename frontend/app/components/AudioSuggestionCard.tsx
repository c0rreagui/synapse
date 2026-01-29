'use client';

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Music,
    Play,
    Pause,
    Sparkles,
    Flame,
    Check,
    X
} from 'lucide-react';

export interface AudioSuggestion {
    sound_id: string;
    title: string;
    author: string;
    viral_score: number;
    reason: 'exploding' | 'niche_match' | 'high_score' | 'trending' | 'content_match';
    confidence: number;
    preview_url?: string;
    cover_url?: string;
    niche: string;
    status: string;
    usage_count: number;
}

interface AudioSuggestionCardProps {
    suggestion: AudioSuggestion;
    onSelect: (suggestion: AudioSuggestion) => void;
    onDismiss: () => void;
    compact?: boolean;
}

const reasonLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
    exploding: {
        label: 'EXPLODINDO 🚀',
        icon: <Flame className="w-3 h-3" />,
        color: 'bg-gradient-to-r from-orange-500 to-red-500'
    },
    niche_match: {
        label: 'MATCH DE NICHO',
        icon: <Sparkles className="w-3 h-3" />,
        color: 'bg-gradient-to-r from-purple-500 to-pink-500'
    },
    high_score: {
        label: 'ALTO POTENCIAL',
        icon: <Sparkles className="w-3 h-3" />,
        color: 'bg-gradient-to-r from-cyan-500 to-blue-500'
    },
    trending: {
        label: 'TRENDING',
        icon: <Music className="w-3 h-3" />,
        color: 'bg-gradient-to-r from-green-500 to-emerald-500'
    },
    content_match: {
        label: 'MATCH CONTEÚDO',
        icon: <Sparkles className="w-3 h-3" />,
        color: 'bg-gradient-to-r from-violet-500 to-purple-500'
    }
};

export default function AudioSuggestionCard({
    suggestion,
    onSelect,
    onDismiss,
    compact = false
}: AudioSuggestionCardProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isHovered, setIsHovered] = useState(false);
    const audioRef = useRef<HTMLAudioElement>(null);

    const handlePlayPause = () => {
        if (!audioRef.current || !suggestion.preview_url) return;

        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    const reasonInfo = reasonLabels[suggestion.reason] || reasonLabels.trending;

    if (compact) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-3 p-3 bg-[#0d1117] border border-purple-500/30 rounded-xl"
            >
                {/* Cover */}
                <div className="relative w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center overflow-hidden">
                    {suggestion.cover_url ? (
                        <img src={suggestion.cover_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                        <Music className="w-5 h-5 text-purple-400" />
                    )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{suggestion.title}</p>
                    <p className="text-xs text-gray-500 truncate">{suggestion.author}</p>
                </div>

                {/* Badge */}
                <span className={`px-2 py-0.5 text-[10px] font-bold text-white rounded-full ${reasonInfo.color}`}>
                    {reasonInfo.label}
                </span>

                {/* Actions */}
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => onSelect(suggestion)}
                        className="p-1.5 rounded-full bg-purple-500 text-white hover:bg-purple-400 transition-colors"
                    >
                        <Check className="w-4 h-4" />
                    </button>
                    <button
                        onClick={onDismiss}
                        className="p-1.5 rounded-full bg-gray-700 text-gray-400 hover:bg-gray-600 transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onHoverStart={() => setIsHovered(true)}
            onHoverEnd={() => setIsHovered(false)}
            className="relative bg-gradient-to-br from-[#0d1117] to-[#161b22] border border-purple-500/30 rounded-2xl p-4 overflow-hidden group"
        >
            {/* Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 via-transparent to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Hidden Audio */}
            {suggestion.preview_url && (
                <audio
                    ref={audioRef}
                    src={suggestion.preview_url}
                    onEnded={() => setIsPlaying(false)}
                />
            )}

            {/* Header with Badge */}
            <div className="flex items-start justify-between mb-3">
                <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold text-white ${reasonInfo.color} shadow-lg`}>
                    {reasonInfo.icon}
                    <span>{reasonInfo.label}</span>
                </div>
                <div className="text-right">
                    <div className="text-xs text-gray-500">Viral Score</div>
                    <div className="text-lg font-bold text-purple-400">{suggestion.viral_score.toFixed(0)}</div>
                </div>
            </div>

            {/* Content */}
            <div className="flex gap-4">
                {/* Cover with Play Button */}
                <div className="relative w-20 h-20 rounded-xl bg-purple-500/20 flex items-center justify-center overflow-hidden shrink-0">
                    {suggestion.cover_url ? (
                        <img src={suggestion.cover_url} alt="" className="w-full h-full object-cover" />
                    ) : (
                        <Music className="w-8 h-8 text-purple-400" />
                    )}

                    {/* Play Overlay */}
                    {suggestion.preview_url && (
                        <motion.button
                            initial={{ opacity: 0 }}
                            animate={{ opacity: isHovered ? 1 : 0 }}
                            onClick={handlePlayPause}
                            className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm"
                        >
                            {isPlaying ? (
                                <Pause className="w-8 h-8 text-white" />
                            ) : (
                                <Play className="w-8 h-8 text-white" />
                            )}
                        </motion.button>
                    )}

                    {/* Playing Indicator */}
                    <AnimatePresence>
                        {isPlaying && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="absolute bottom-1 right-1 flex items-center gap-0.5"
                            >
                                {[0, 1, 2].map((i) => (
                                    <motion.div
                                        key={i}
                                        animate={{ height: [4, 12, 4] }}
                                        transition={{
                                            duration: 0.5,
                                            repeat: Infinity,
                                            delay: i * 0.1
                                        }}
                                        className="w-1 bg-purple-400 rounded-full"
                                    />
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <h4 className="text-white font-semibold truncate">{suggestion.title}</h4>
                    <p className="text-sm text-gray-400 truncate">{suggestion.author}</p>

                    {/* Stats */}
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-purple-500" />
                            {suggestion.niche}
                        </span>
                        <span>
                            {suggestion.usage_count.toLocaleString()} usos
                        </span>
                    </div>

                    {/* Confidence Bar */}
                    <div className="mt-2">
                        <div className="flex items-center justify-between text-[10px] text-gray-500 mb-1">
                            <span>Confiança IA</span>
                            <span>{(suggestion.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${suggestion.confidence * 100}%` }}
                                transition={{ duration: 0.5 }}
                                className="h-full bg-gradient-to-r from-purple-500 to-cyan-500"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-4">
                <button
                    onClick={() => onSelect(suggestion)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white font-medium rounded-xl transition-all shadow-lg shadow-purple-500/20"
                >
                    <Check className="w-5 h-5" />
                    Usar Esta Música
                </button>
                <button
                    onClick={onDismiss}
                    className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-400 font-medium rounded-xl transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>
        </motion.div>
    );
}
