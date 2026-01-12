import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Activity, MessageCircleQuestion } from 'lucide-react';

interface SentimentPulse {
    score: number;
    dominant_emotion: string;
    top_questions: string[];
    lovers: string[];
    haters: string[];
    debate_topic?: string;
}

interface SentimentCardProps {
    data?: SentimentPulse;
    delay?: number;
}

export const SentimentCard: React.FC<SentimentCardProps> = ({ data, delay = 0 }) => {
    if (!data) return null;

    const isPositive = data.score >= 50;
    const pulseColor = isPositive ? 'text-[#00ff9d]' : 'text-[#ff0055]';
    const borderColor = isPositive ? 'border-[#00ff9d]/30' : 'border-[#ff0055]/30';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
            className={`col-span-1 md:col-span-2 bg-[#0a0a0f]/80 backdrop-blur-md border ${borderColor} rounded-xl p-6 relative overflow-hidden`}
        >
            {/* Background Pulse Effect */}
            <div className={`absolute top-0 right-0 w-32 h-32 ${isPositive ? 'bg-green-500' : 'bg-red-500'} opacity-5 blur-[80px] rounded-full pointer-events-none`} />

            <div className="flex flex-col md:flex-row gap-8">
                {/* Left: Score & Emotion */}
                <div className="flex-1 flex flex-col items-center justify-center md:border-r border-white/10 md:pr-8 border-b md:border-b-0 pb-6 md:pb-0">
                    <div className="relative">
                        <motion.div
                            animate={{ scale: [1, 1.1, 1] }}
                            transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                        >
                            <Heart size={64} className={`${pulseColor} ${isPositive ? 'fill-[#00ff9d]/10' : 'fill-[#ff0055]/10'}`} />
                        </motion.div>
                        <div className="absolute inset-0 flex items-center justify-center font-bold text-xl text-white">
                            {data.score}%
                        </div>
                    </div>
                    <div className="mt-4 text-center">
                        <h3 className="text-gray-400 text-sm uppercase tracking-wider">Sentiment Pulse</h3>
                        <p className={`text-xl font-bold ${pulseColor} mt-1 uppercase`}>{data.dominant_emotion}</p>
                    </div>
                </div>

                {/* Right: Questions & Insights */}
                <div className="flex-[2] space-y-4">
                    <div className="flex items-center gap-2 mb-2">
                        <MessageCircleQuestion className="text-[#00f3ff]" size={20} />
                        <h3 className="font-bold text-white">Top Dúvidas da Audiência</h3>
                    </div>

                    <div className="space-y-2">
                        {data.top_questions && data.top_questions.length > 0 ? (
                            data.top_questions.slice(0, 3).map((q, i) => (
                                <div key={i} className="bg-white/5 p-3 rounded-lg border border-white/5 text-gray-300 text-sm flex gap-2 items-start">
                                    <span className="text-[#00f3ff] mt-0.5">?</span>
                                    <span>{q}</span>
                                </div>
                            ))
                        ) : (
                            <p className="text-gray-500 text-sm italic">Nenhuma dúvida detectada neste ciclo.</p>
                        )}
                    </div>

                    {data.debate_topic && (
                        <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                            <div className="flex items-center gap-2 text-yellow-500 mb-1">
                                <Activity size={16} />
                                <span className="text-xs font-bold uppercase">Trending Debate</span>
                            </div>
                            <p className="text-gray-300 text-sm">{data.debate_topic}</p>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};
