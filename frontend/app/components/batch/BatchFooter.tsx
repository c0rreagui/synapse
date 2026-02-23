import React, { useState, useEffect } from 'react';
import { useBatch } from './BatchContext';
import { Clock, Calendar, SlidersHorizontal, ChevronUp, Sparkles, Plus, Minus, Settings2 } from 'lucide-react';
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
        customTimes, setCustomTimes, // [SYN-CUSTOM]
        validationResult,
        isValidating,
        isUploading,
        bypassConflicts,
        setBypassConflicts,
        // [SYN-67] Auto-Schedule
        postsPerDay, setPostsPerDay,
        autoStartHour, setAutoStartHour,
        handleAutoSchedule,
    } = useBatch();

    const [showStrategyMenu, setShowStrategyMenu] = useState(false);
    const [showConflicts, setShowConflicts] = useState(false);
    const [mounted, setMounted] = useState(false);

    React.useEffect(() => {
        setMounted(true);
    }, []);

    // [SYN-CUSTOM] Ensure custom times has defaults if empty
    useEffect(() => {
        if (strategy === 'CUSTOM' && customTimes.length === 0) {
            setCustomTimes(['12:00', '18:00']);
        }
    }, [strategy]);

    const updateCustomTime = (index: number, val: string) => {
        const newTimes = [...customTimes];
        newTimes[index] = val;
        setCustomTimes(newTimes);
    };

    const addCustomSlot = () => {
        if (customTimes.length >= 10) return;
        setCustomTimes([...customTimes, '12:00']);
    };

    const removeCustomSlot = () => {
        if (customTimes.length <= 1) return;
        setCustomTimes(prev => prev.slice(0, -1));
    };

    // Formatted display
    const dateDisplay = startDate ? format(new Date(startDate), 'dd/MM/yyyy') : 'Data';
    let frequencyDisplay = '';

    if (strategy === 'ORACLE') {
        frequencyDisplay = 'Oracle AI (Smart)';
    } else if (strategy === 'QUEUE') {
        frequencyDisplay = 'Apenas Fila (Sem Agendar)';
    } else if (strategy === 'CUSTOM') {
        frequencyDisplay = `${customTimes.length} Posts / Dia (Fixo)`;
    } else if (strategy === 'AUTO_SCHEDULE') {
        frequencyDisplay = `Auto: ${postsPerDay}x / Dia as ${String(autoStartHour).padStart(2, '0')}:00`;
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
    const isApprovalMode = files.some(f => f.isRemote);
    const totalPosts = isApprovalMode ? files.length : files.length * selectedProfiles.length;
    const isAutoScheduleMode = strategy === 'AUTO_SCHEDULE';

    return (
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-[#0c0c0c]/95 backdrop-blur-2xl border-t border-white/5 flex items-center justify-between px-8 z-50 shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
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

                            <button
                                onClick={() => { setStrategy('CUSTOM'); setShowStrategyMenu(false); }}
                                className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors text-left group"
                            >
                                <div className="flex items-center gap-2">
                                    <Settings2 className="w-4 h-4 text-gray-500 group-hover:text-white" />
                                    <span className="text-xs text-gray-300 group-hover:text-white">Horários Fixos (Custom)</span>
                                </div>
                                {strategy === 'CUSTOM' && (
                                    <div className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
                                )}
                            </button>

                            <div className="h-px bg-white/5 my-1" />

                            {/* [SYN-67] Auto-Schedule */}
                            <button
                                onClick={() => { setStrategy('AUTO_SCHEDULE'); setShowStrategyMenu(false); }}
                                className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-emerald-500/10 transition-colors text-left group"
                            >
                                <div className="flex items-center gap-2">
                                    <span className="text-emerald-400 text-base">&#9654;</span>
                                    <span className="text-xs text-gray-300 group-hover:text-white">Auto-Agendar (Studio)</span>
                                </div>
                                {strategy === 'AUTO_SCHEDULE' && (
                                    <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" />
                                )}
                            </button>

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

            {/* Center: Date/Time Picker Logic */}
            {strategy !== 'QUEUE' && strategy !== 'AUTO_SCHEDULE' && (
                <div className="flex items-center gap-6 animate-in fade-in zoom-in duration-300 mx-auto">
                    {/* Common Date Picker */}
                    <div
                        onClick={() => (document.getElementById('date-input') as HTMLInputElement)?.showPicker()}
                        className="flex items-center gap-3 px-5 py-2.5 bg-black/40 border border-white/10 rounded-xl cursor-pointer hover:bg-white/5 transition-colors group"
                    >
                        <Calendar className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                        <input
                            id="date-input"
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="bg-transparent border-none text-sm text-gray-200 group-hover:text-white focus:ring-0 p-0 font-mono cursor-pointer [&::-webkit-calendar-picker-indicator]:hidden w-24"
                        />
                    </div>

                    <div className="h-10 w-px bg-white/10" />

                    {/* [SYN-CUSTOM] Custom Time Slots UI */}
                    {strategy === 'CUSTOM' ? (
                        <div className="flex items-center gap-4">
                            {/* Counter */}
                            <div className="flex flex-col items-center gap-1">
                                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Quantidade</span>
                                <div className="flex items-center bg-white/5 rounded-lg border border-white/5 px-1 py-0.5">
                                    <button onClick={removeCustomSlot} className="p-1.5 hover:text-white text-gray-500 disabled:opacity-30 hover:bg-white/5 rounded-md transition-colors" disabled={customTimes.length <= 1}>
                                        <Minus className="w-3 h-3" />
                                    </button>
                                    <span className="text-sm font-mono w-8 text-center text-white">{customTimes.length}</span>
                                    <button onClick={addCustomSlot} className="p-1.5 hover:text-white text-gray-500 disabled:opacity-30 hover:bg-white/5 rounded-md transition-colors" disabled={customTimes.length >= 10}>
                                        <Plus className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>

                            {/* Slots List */}
                            <div className="flex flex-col gap-1">
                                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider pl-1">Horários</span>
                                <div className="flex items-center gap-2 max-w-[450px] overflow-x-auto custom-scrollbar pb-2 px-1">
                                    {customTimes.map((time, idx) => (
                                        <TikTokTimePicker
                                            key={idx}
                                            value={time}
                                            onChange={(val) => updateCustomTime(idx, val)}
                                            className="flex-shrink-0"
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        /* Standard Single Time Picker */
                        <div className="flex items-center gap-3">
                            <span className="text-xs text-gray-500 font-bold uppercase tracking-wider">Início</span>
                            <TikTokTimePicker
                                value={startTime}
                                onChange={setStartTime}
                            />
                        </div>
                    )}
                </div>
            )}

            {/* [SYN-67] Auto-Schedule Config Panel */}
            {isAutoScheduleMode && (
                <div className="flex items-center gap-6 animate-in fade-in zoom-in duration-300 mx-auto">
                    {/* Posts per day */}
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Posts / Dia</span>
                        <div className="flex items-center bg-white/5 rounded-lg border border-white/5 px-1 py-0.5">
                            <button onClick={() => setPostsPerDay(Math.max(1, postsPerDay - 1))} className="p-1.5 hover:text-white text-gray-500 disabled:opacity-30 hover:bg-white/5 rounded-md transition-colors" disabled={postsPerDay <= 1}>
                                <Minus className="w-3 h-3" />
                            </button>
                            <span className="text-sm font-mono w-8 text-center text-white">{postsPerDay}</span>
                            <button onClick={() => setPostsPerDay(Math.min(3, postsPerDay + 1))} className="p-1.5 hover:text-white text-gray-500 disabled:opacity-30 hover:bg-white/5 rounded-md transition-colors" disabled={postsPerDay >= 3}>
                                <Plus className="w-3 h-3" />
                            </button>
                        </div>
                    </div>

                    <div className="h-10 w-px bg-white/10" />

                    {/* Start hour */}
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Horario Base</span>
                        <div className="flex items-center bg-white/5 rounded-lg border border-white/5 px-1 py-0.5">
                            <button onClick={() => setAutoStartHour(autoStartHour === 0 ? 23 : autoStartHour - 1)} className="p-1.5 hover:text-white text-gray-500 hover:bg-white/5 rounded-md transition-colors">
                                <Minus className="w-3 h-3" />
                            </button>
                            <span className="text-sm font-mono w-16 text-center text-emerald-300">{String(autoStartHour).padStart(2, '0')}:00</span>
                            <button onClick={() => setAutoStartHour((autoStartHour + 1) % 24)} className="p-1.5 hover:text-white text-gray-500 hover:bg-white/5 rounded-md transition-colors">
                                <Plus className="w-3 h-3" />
                            </button>
                        </div>
                    </div>

                    <div className="h-10 w-px bg-white/10" />

                    {/* Info badge */}
                    <div className="flex flex-col items-center">
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Lote Inicial</span>
                        <span className="text-xs text-emerald-400 font-mono mt-1">10 videos</span>
                    </div>
                </div>
            )}

            {/* Right: Action */}
            <div className="flex items-center gap-4">
                {/* Conflict Error Message (Mini) */}
                {validationResult && validationResult.issues.length > 0 && (
                    <div className="relative">
                        <button
                            onClick={() => setShowConflicts(!showConflicts)}
                            className={clsx(
                                "flex items-center gap-2 px-3 py-1.5 rounded-lg border cursor-help transition-colors",
                                bypassConflicts
                                    ? "bg-orange-500/10 border-orange-500/20 hover:bg-orange-500/20"
                                    : "bg-red-500/10 border-red-500/20 hover:bg-red-500/20"
                            )}
                        >
                            <div className={clsx(
                                "w-2 h-2 rounded-full animate-pulse",
                                bypassConflicts ? "bg-orange-500" : "bg-red-500"
                            )} />
                            <span className={clsx(
                                "text-[10px] font-medium",
                                bypassConflicts ? "text-orange-400" : "text-red-400"
                            )}>
                                {validationResult.issues.length} conflitos {bypassConflicts ? '(Ignorados)' : 'detectados'}
                            </span>
                        </button>

                        {/* Conflicts Popover */}
                        {showConflicts && (
                            <div className={clsx(
                                "absolute bottom-full mb-2 right-0 w-80 bg-[#1a1a1a] border rounded-xl shadow-2xl p-4 animate-in slide-in-from-bottom-2 fade-in z-50",
                                bypassConflicts ? "border-orange-500/30" : "border-red-500/30"
                            )}>
                                <h4 className={clsx("text-xs font-bold mb-3 flex items-center gap-2", bypassConflicts ? "text-orange-400" : "text-white")}>
                                    <span className={bypassConflicts ? "text-orange-500" : "text-red-500"}>⚠</span>
                                    {bypassConflicts ? "Conflitos Ignorados" : "Bloqueio de Horário"}
                                </h4>

                                <div className="space-y-3 max-h-60 overflow-y-auto custom-scrollbar mb-3">
                                    {validationResult.issues.map((issue: any, idx: number) => (
                                        <div key={idx} className={clsx("p-2.5 rounded-lg border", bypassConflicts ? "bg-orange-500/10 border-orange-500/10" : "bg-red-500/10 border-red-500/10")}>
                                            <p className="text-xs font-medium text-white mb-1">{issue.message}</p>
                                            {issue.suggested_fix && (
                                                <p className={clsx("text-[10px] flex items-center gap-1", bypassConflicts ? "text-orange-300" : "text-red-300")}>
                                                    💡 Sugestão: {issue.suggested_fix}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>

                                {/* Bypass Switch */}
                                <div className="pt-3 border-t border-white/10 flex items-center justify-between group cursor-pointer" onClick={() => setBypassConflicts(!bypassConflicts)}>
                                    <div className="flex flex-col">
                                        <span className="text-xs font-bold text-white">Forçar Agendamento</span>
                                        <span className="text-[10px] text-gray-400">Ignorar conflitos de horário</span>
                                    </div>
                                    <div className={clsx("w-9 h-5 rounded-full transition-colors relative", bypassConflicts ? "bg-orange-500" : "bg-gray-700")}>
                                        <div className={clsx(
                                            "absolute top-1 left-1 w-3 h-3 rounded-full bg-white transition-transform shadow-sm",
                                            bypassConflicts ? "translate-x-4" : "translate-x-0"
                                        )} />
                                    </div>
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
                    onClick={isAutoScheduleMode ? handleAutoSchedule : handleUpload}
                    disabled={!canSchedule}
                    variant="primary"
                    className={`px-8 py-2.5 text-xs font-bold uppercase tracking-wider${isAutoScheduleMode ? ' !border-emerald-500/50 !text-emerald-400' : ''}`}
                >
                    {isUploading ? 'Enviando...' :
                        isAutoScheduleMode ? `Auto-Agendar ${files.length > 0 ? files.length : ''} Videos` :
                            isValidating ? 'Validando...' :
                                isApprovalMode ? `Aprovar ${totalPosts > 0 ? totalPosts : ''} Video(s)`
                                    : `Agendar ${totalPosts > 0 ? totalPosts : ''} Posts`
                    }
                </NeonButton>
            </div>
        </div>
    );
}

// Helper for icon removed (using Lucide)
