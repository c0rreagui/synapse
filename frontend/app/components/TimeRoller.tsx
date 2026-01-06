import React, { useState, useRef, useEffect } from 'react';

interface TimeRollerProps {
    onChange: (time: string, isScheduled: boolean) => void;
}

export default function TimeRoller({ onChange }: TimeRollerProps) {
    const [isScheduled, setIsScheduled] = useState(false);
    const [selectedHour, setSelectedHour] = useState("18");
    const [selectedMinute, setSelectedMinute] = useState("00");

    const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0'));
    const minutes = Array.from({ length: 12 }, (_, i) => (i * 5).toString().padStart(2, '0')); // 5 min intervals

    useEffect(() => {
        if (isScheduled) {
            onChange(`${selectedHour}:${selectedMinute}`, true);
        } else {
            onChange("", false);
        }
    }, [isScheduled, selectedHour, selectedMinute, onChange]);

    return (
        <div className="flex flex-col gap-4">
            {/* Toggle */}
            <div className="flex items-center justify-between bg-slate-900/40 p-1 rounded-full border border-white/5 relative">
                <button
                    onClick={() => setIsScheduled(false)}
                    className={`flex-1 py-2 px-4 rounded-full text-xs font-bold transition-all duration-300 ${!isScheduled ? 'bg-cyan-500 text-white shadow-[0_0_15px_rgba(6,182,212,0.4)]' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    POSTAR AGORA
                </button>
                <button
                    onClick={() => setIsScheduled(true)}
                    className={`flex-1 py-2 px-4 rounded-full text-xs font-bold transition-all duration-300 ${isScheduled ? 'bg-purple-500 text-white shadow-[0_0_15px_rgba(168,85,247,0.4)]' : 'text-slate-500 hover:text-slate-300'}`}
                >
                    AGENDAR
                </button>
            </div>

            {/* Roller Area */}
            <div className={`transition-all duration-500 overflow-hidden ${isScheduled ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'}`}>
                <div className="flex items-center gap-2 justify-center bg-slate-950/50 rounded-2xl p-4 border border-white/5 shadow-inner">
                    {/* Hours */}
                    <div className="h-32 overflow-y-scroll no-scrollbar snap-y snap-mandatory w-16 text-center relative mask-gradient">
                        <div className="h-[40%]" /> {/* Spacer */}
                        {hours.map(h => (
                            <div
                                key={h}
                                onClick={() => setSelectedHour(h)}
                                className={`snap-center py-2 text-xl font-mono font-bold cursor-pointer transition-all duration-200 ${selectedHour === h ? 'text-white scale-110' : 'text-slate-700'}`}
                            >
                                {h}
                            </div>
                        ))}
                        <div className="h-[40%]" /> {/* Spacer */}
                    </div>

                    <span className="text-slate-600 text-xl font-bold">:</span>

                    {/* Minutes */}
                    <div className="h-32 overflow-y-scroll no-scrollbar snap-y snap-mandatory w-16 text-center relative mask-gradient">
                        <div className="h-[40%]" /> {/* Spacer */}
                        {minutes.map(m => (
                            <div
                                key={m}
                                onClick={() => setSelectedMinute(m)}
                                className={`snap-center py-2 text-xl font-mono font-bold cursor-pointer transition-all duration-200 ${selectedMinute === m ? 'text-white scale-110' : 'text-slate-700'}`}
                            >
                                {m}
                            </div>
                        ))}
                        <div className="h-[40%]" /> {/* Spacer */}
                    </div>
                </div>
                <p className="text-center text-[10px] text-slate-500 mt-2 font-mono uppercase tracking-widest">
                    Horário do Servidor
                </p>
            </div>
        </div>
    );
}

// Add simple scrollbar hide utility to globals if needed, or inline style
