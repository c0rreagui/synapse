import React, { useState } from 'react';
import { useBatch } from './BatchContext';
import { Clock, Calendar, SlidersHorizontal, ChevronUp, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import { format } from 'date-fns';
import { NeonButton } from '../NeonButton';
import { TikTokTimePicker } from '../TikTokTimePicker';

export function BatchFooter({ onClose }: { onClose: () => void }) {
    const {
        handleUpload,
        files,
        selectedProfiles,
        strategy, setStrategy,
        intervalMinutes, setIntervalMinutes,
        startDate, setStartDate,
        startTime, setStartTime,
        validationResult,
        isValidating,
        isUploading
    } = useBatch();

    const [showStrategyMenu, setShowStrategyMenu] = useState(false);
    const [showConflicts, setShowConflicts] = useState(false);
    const [mounted, setMounted] = useState(false);

    React.useEffect(() => {
        setMounted(true);
    }, []);

    // Formatted display
    const dateDisplay = startDate ? format(new Date(startDate), 'dd/MM/yyyy') : 'Data';
    let frequencyDisplay = '';

    if (strategy === 'ORACLE') {
        frequencyDisplay = 'Oracle AI (Smart)';
    } else if (strategy === 'QUEUE') {
        frequencyDisplay = 'Apenas Fila (Sem Agendar)';
    } else {
        // Interval Strategy
        if (intervalMinutes === 1440) frequencyDisplay = '1x / Dia';
        else if (intervalMinutes === 720) frequencyDisplay = '2x / Dia';
        else if (intervalMinutes === 480) frequencyDisplay = '3x / Dia';
        else if (intervalMinutes === 360) frequencyDisplay = '4x / Dia';
        else frequencyDisplay = `${intervalMinutes / 60}h Intervalo`;
    }

    // Derived state
    const canSchedule = files.length > 0 && selectedProfiles.length > 0 && !isValidating && !isUploading;
    const totalPosts = files.length * selectedProfiles.length;
    const isApprovalMode = files.some(f => f.isRemote);

    return (
        <div className="absolute bottom-0 left-0 right-0 h-20 bg-[#0c0c0c]/90 backdrop-blur-2xl border-t border-white/5 flex items-center justify-between px-8 z-50">
            {/* Left: Strategy Selector (Opus Style "Pill") */}
            <div className="relative">
                <button
                    onClick={() => setShowStrategyMenu(!showStrategyMenu)}
                    className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all group"
                >
                    <div className="p-1.5 rounded-lg bg-synapse-purple/20 text-synapse-purple group-hover:text-white transition-colors">
                        <SlidersHorizontal className="w-4 h-4" />
                    </div>
                    <div className="text-left">
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Frequência</p>
                        <p className="text-xs font-medium text-white">{strategy === 'ORACLE' ? 'Oracle AI (Smart)' : frequencyDisplay}</p>
                    </div>
                    <ChevronUp className={clsx("w-3 h-3 text-gray-500 transition-transform", showStrategyMenu && "rotate-180")} />
                </button>

                {/* Strategy Popover */}
                {showStrategyMenu && mounted && (
                    <div className="absolute bottom-full mb-3 left-0 w-64 bg-[#1a1a1a] border border-white/10 rounded-2xl shadow-2xl p-2 animate-in slide-in-from-bottom-2 fade-in">
                        <div className="space-y-1">
                            <div className="px-3 py-2 text-[10px] uppercase text-gray-500 font-bold tracking-wider border-b border-white/5 mb-1">
                                Frequência Diária
                            </div>

                            {/* Daily Options */}
                            {[
                                { label: '1 Post / Dia', val: 1440 },
                                { label: '2 Posts / Dia', val: 720 },
                                { label: '3 Posts / Dia', val: 480 },
                                { label: '4 Posts / Dia', val: 360 }
                            ].map(opt => (
                                <button
                                    key={opt.val}
                                    onClick={() => { setIntervalMinutes(opt.val); setStrategy('INTERVAL'); setShowStrategyMenu(false); }}
                                    className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors text-left"
                                >
                                    <span className="text-xs text-gray-300">{opt.label}</span>
                                    {strategy === 'INTERVAL' && intervalMinutes === opt.val && (
                                        <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
                                    )}
                                </button>
                            ))}

                            <div className="h-px bg-white/5 my-1" />

                            <button
                                onClick={() => { setStrategy('ORACLE'); setShowStrategyMenu(false); }}
                                className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-synapse-purple/20 transition-colors text-left group"
                            >
                                <div className="flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-purple-400 group-hover:text-purple-300" />
                                    <span className="text-xs text-gray-300 group-hover:text-white">Oracle AI (Smart)</span>
                                </div>
                                {strategy === 'ORACLE' && (
                                    <div className="w-2 h-2 rounded-full bg-purple-400 shadow-[0_0_8px_rgba(168,85,247,0.5)]" />
                                )}
                            </button>

                            <button
                                onClick={() => { setStrategy('QUEUE'); setShowStrategyMenu(false); }}
                                className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors text-left group"
                            >
                                <div className="flex items-center gap-2">
                                    <span className="text-xl">📥</span>
                                    <span className="text-xs text-gray-300 group-hover:text-white">Apenas Fila</span>
                                </div>
                                {strategy === 'QUEUE' && (
                                    <div className="w-2 h-2 rounded-full bg-white shadow-[0_0_8px_rgba(255,255,255,0.5)]" />
                                )}
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Center: Date/Time Picker (Hidden if QUEUE) */}
            {strategy !== 'QUEUE' && (
                <div className="flex items-center gap-4 animate-in fade-in zoom-in duration-300">
                    {/* Date Picker */}
                    <div
                        onClick={() => (document.getElementById('date-input') as HTMLInputElement)?.showPicker()}
                        className="flex items-center gap-3 px-4 py-2 bg-black/40 border border-white/5 rounded-full cursor-pointer hover:bg-white/5 transition-colors group"
                    >
                        <Calendar className="w-4 h-4 text-gray-500 group-hover:text-white transition-colors" />
                        <input
                            id="date-input"
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="bg-transparent border-none text-xs text-white focus:ring-0 p-0 font-mono cursor-pointer [&::-webkit-calendar-picker-indicator]:hidden"
                        />
                    </div>

                    <div className="h-8 w-px bg-white/5" />

                    <TikTokTimePicker
                        value={startTime}
                        onChange={setStartTime}
                    />
                </div>
            )}

            {/* Right: Action */}
            <div className="flex items-center gap-4">
                {/* Conflict Error Message (Mini) */}
                {validationResult && validationResult.issues.length > 0 && (
                    <div className="relative">
                        <button
                            onMouseEnter={() => setShowConflicts(true)}
                            onMouseLeave={() => setShowConflicts(false)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 cursor-help transition-colors hover:bg-red-500/20"
                        >
                            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                            <span className="text-[10px] text-red-400 font-medium">
                                {validationResult.issues.length} conflitos detectados
                            </span>
                        </button>

                        {/* Conflicts Popover */}
                        {showConflicts && (
                            <div className="absolute bottom-full mb-2 right-0 w-80 bg-[#1a1a1a] border border-red-500/30 rounded-xl shadow-2xl p-4 animate-in slide-in-from-bottom-2 fade-in z-50">
                                <h4 className="text-xs font-bold text-white mb-3 flex items-center gap-2">
                                    <span className="text-red-500">⚠</span> Detalhes do Conflito
                                </h4>
                                <div className="space-y-3 max-h-60 overflow-y-auto custom-scrollbar">
                                    {validationResult.issues.map((issue: any, idx: number) => (
                                        <div key={idx} className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/10">
                                            <p className="text-xs font-medium text-white mb-1">{issue.message}</p>
                                            {issue.suggested_fix && (
                                                <p className="text-[10px] text-red-300 flex items-center gap-1">
                                                    💡 Sugestão: {issue.suggested_fix}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <button
                    onClick={onClose}
                    className="text-xs text-gray-500 hover:text-white transition-colors"
                >
                    Cancelar
                </button>
                <NeonButton
                    onClick={handleUpload}
                    disabled={!canSchedule}
                    variant="primary"
                    className="px-8 py-2.5 text-xs font-bold uppercase tracking-wider"
                >
                    {isValidating ? 'Validando...' :
                        strategy === 'QUEUE' ? `Enviar ${totalPosts > 0 ? totalPosts : ''} para Fila`
                            : isApprovalMode ? `Aprovar ${totalPosts > 0 ? totalPosts : ''} Vídeo(s)`
                                : `Agendar ${totalPosts > 0 ? totalPosts : ''} Posts`
                    }
                </NeonButton>
            </div>
        </div>
    );
}

// Helper for icon removed (using Lucide)
