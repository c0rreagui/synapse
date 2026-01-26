import { StitchCard } from '../StitchCard';
import clsx from 'clsx';
import { SparklesIcon, ExclamationCircleIcon, CheckBadgeIcon } from '@heroicons/react/24/solid';

export type PatternType = 'VIRAL_HOOK' | 'TIMING' | 'FORMAT' | 'KEYWORD' | 'ANOMALY';

interface PatternCardProps {
    type: PatternType;
    title: string;
    description: string;
    confidence: number; // 0-100
    impact: 'HIGH' | 'MEDIUM' | 'LOW';
}

export function PatternCard({ type, title, description, confidence, impact }: PatternCardProps) {
    // Icons based on type
    const getIcon = () => {
        switch (type) {
            case 'VIRAL_HOOK': return <SparklesIcon className="w-5 h-5 text-yellow-400" />;
            case 'ANOMALY': return <ExclamationCircleIcon className="w-5 h-5 text-red-400" />;
            default: return <CheckBadgeIcon className="w-5 h-5 text-synapse-primary" />;
        }
    };

    // Color theme based on impact
    const themeColor = impact === 'HIGH' ? 'text-green-400' : impact === 'MEDIUM' ? 'text-blue-400' : 'text-gray-400';
    const borderColor = impact === 'HIGH' ? 'border-green-500/30' : 'border-white/5';

    return (
        <StitchCard className={clsx("p-5 flex flex-col gap-3 transition-all hover:bg-white/[0.03]", borderColor)}>
            <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-white/5 border border-white/5">
                        {getIcon()}
                    </div>
                    <div>
                        <h4 className="text-sm font-bold text-gray-200">{title}</h4>
                        <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">{type}</span>
                    </div>
                </div>
                <div className="flex flex-col items-end">
                    <span className={clsx("text-xs font-bold px-2 py-0.5 rounded-full bg-white/5", themeColor)}>
                        {impact} IMPACT
                    </span>
                </div>
            </div>

            <p className="text-sm text-gray-400 leading-relaxed bg-black/20 p-3 rounded-xl border border-white/5">
                {description}
            </p>

            {/* Confidence Meter */}
            <div className="mt-auto pt-2">
                <div className="flex justify-between text-[10px] text-gray-500 mb-1 font-mono uppercase">
                    <span>Probability</span>
                    <span className="text-white">{confidence}%</span>
                </div>
                <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                    <div
                        className={clsx("h-full rounded-full transition-all duration-1000",
                            confidence > 80 ? "bg-synapse-emerald shadow-[0_0_10px_#10b981]" : "bg-synapse-primary"
                        )}
                        style={{ width: `${confidence}%` }}
                    />
                </div>
            </div>
        </StitchCard>
    );
}
