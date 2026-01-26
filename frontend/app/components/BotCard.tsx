'use client';

import { CpuChipIcon, BoltIcon, ExclamationTriangleIcon, PauseIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
// Removing StitchCard dependency for this specific component to have full control over the aesthetic
// import { StitchCard } from './StitchCard'; 

export interface BotProps {
    id: string;
    name: string;
    role: 'UPLOADER' | 'FACTORY' | 'MONITOR' | 'SCHEDULER';
    status: 'online' | 'offline' | 'error' | 'sleeping';
    currentTask?: string;
    uptime?: string;
    description?: string;
    avatar?: string;
}

export default function BotCard({ name, role, status, currentTask, uptime, ...others }: BotProps) {
    const isOnline = status === 'online';
    const isError = status === 'error';
    const isSleeping = status === 'sleeping';

    return (
        <div className="relative group min-h-[200px] rounded-[32px] bg-[#0c0c0c]/80 overflow-hidden transition-all duration-500 hover:shadow-[0_0_60px_-15px_rgba(139,92,246,0.3)] backdrop-blur-2xl border border-white/5 hover:border-synapse-primary/40">

            {/* 1. CONTAINED CYBER GRID (Holographic Projection) */}
            <div className="absolute inset-0 z-0 opacity-[0.15] pointer-events-none mix-blend-color-dodge transition-opacity duration-700 group-hover:opacity-30"
                style={{ backgroundImage: 'linear-gradient(rgba(139, 92, 246, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(139, 92, 246, 0.4) 1px, transparent 1px)', backgroundSize: '32px 32px' }}>
            </div>

            {/* 2. SUBTLE SCANLINES (CRT Feel) */}
            <div className="absolute inset-0 z-10 opacity-10 pointer-events-none bg-[linear-gradient(rgba(0,0,0,0)_50%,rgba(0,0,0,0.4)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%]"></div>

            {/* 3. AMBIENT GLOW (Apple Style Soft Bloom) */}
            <div className={clsx(
                "absolute -top-1/2 -right-1/2 w-[120%] h-[120%] rounded-full blur-[120px] opacity-10 transition-all duration-1000 group-hover:opacity-30",
                isOnline ? "bg-[conic-gradient(at_top_right,_var(--tw-gradient-stops))] from-synapse-primary via-synapse-cyan to-transparent" : "bg-gray-800"
            )} />

            {/* CONTENT CONTAINER */}
            <div className="relative z-30 p-7 h-full flex flex-col justify-between">

                {/* HEADER SECTION */}
                <div className="flex items-start gap-5">
                    {/* AVATAR (Squircle - Glass Container) */}
                    <div className={clsx(
                        "w-[4.5rem] h-[4.5rem] rounded-[1.2rem] relative overflow-hidden transition-all duration-500 flex items-center justify-center bg-black/50 border shadow-inner shrink-0",
                        isOnline ? "border-synapse-primary/40 shadow-[0_0_30px_-5px_rgba(139,92,246,0.4)]" : "border-white/5 grayscale opacity-60"
                    )}>
                        {/* IMAGE */}
                        {others.avatar ? (
                            <img src={others.avatar} alt={name} className="w-full h-full object-cover transform transition-transform duration-700 group-hover:scale-110" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center">
                                {role === 'UPLOADER' && <BoltIcon className="w-8 h-8 text-synapse-primary drop-shadow-[0_0_8px_rgba(139,92,246,1)]" />}
                                {role === 'FACTORY' && <CpuChipIcon className="w-8 h-8 text-synapse-cyan drop-shadow-[0_0_8px_rgba(6,182,212,1)]" />}
                                {role === 'MONITOR' && <ExclamationTriangleIcon className="w-8 h-8 text-synapse-amber drop-shadow-[0_0_8px_rgba(245,158,11,1)]" />}
                                {role === 'SCHEDULER' && <PauseIcon className="w-8 h-8 text-synapse-emerald drop-shadow-[0_0_8px_rgba(16,185,129,1)]" />}
                            </div>
                        )}

                        {/* REFLECTION LAYER */}
                        <div className="absolute inset-0 bg-gradient-to-br from-white/20 via-transparent to-black/40 opacity-50 pointer-events-none mix-blend-overlay"></div>
                    </div>

                    {/* TEXT INFO */}
                    <div className="flex-1 min-w-0 pt-1">
                        <div className="flex flex-col items-start">
                            <h3 className="text-white font-sans text-2xl font-bold tracking-tight group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-synapse-primary transition-all duration-300">
                                {name}
                            </h3>

                            {/* ROLE BADGES */}
                            <div className="flex items-center gap-2 mt-2">
                                <span className={clsx(
                                    "text-[10px] px-3 py-1 rounded-full font-medium uppercase tracking-widest backdrop-blur-md border transition-colors",
                                    "bg-white/[0.03] border-white/[0.1] text-gray-300 group-hover:border-synapse-primary/30 group-hover:text-white"
                                )}>
                                    {role}
                                </span>
                            </div>
                        </div>

                        {/* DESCRIPTION */}
                        <p className="text-[13px] text-gray-400 mt-3 leading-relaxed font-light line-clamp-2 opacity-80 mix-blend-plus-lighter">
                            {/*@ts-ignore*/}
                            {(others as any).description || "System awaiting initialization sequence..."}
                        </p>
                    </div>
                </div>

                {/* FOOTER (Glass Pill) */}
                <div className="mt-6">
                    <div className="bg-black/30 rounded-2xl p-1.5 border border-white/[0.08] flex items-center justify-between group-hover:border-synapse-primary/30 transition-colors backdrop-blur-md shadow-lg pr-4">
                        <div className="flex items-center gap-3 overflow-hidden bg-white/[0.03] rounded-xl px-3 py-2">
                            {/* LIVE PULSE */}
                            <div className={clsx("w-2 h-2 rounded-full shrink-0 shadow-[0_0_10px_currentColor]", isOnline ? "bg-synapse-emerald text-synapse-emerald animate-pulse" : "bg-gray-600 text-gray-600")} />

                            <code className="text-xs text-gray-200 font-mono truncate tracking-tight">
                                {isOnline || isSleeping ? (currentTask || 'SYSTEM_READY') : 'OFFLINE'}
                            </code>
                        </div>

                        {uptime && (
                            <div className="flex items-center gap-2 pl-3 ml-auto shrink-0 opacity-70 group-hover:opacity-100 transition-opacity">
                                <span className="text-[9px] text-gray-500 font-mono uppercase tracking-widest">T-PLUS</span>
                                <span className="text-[11px] font-mono text-synapse-cyan shadow-[0_0_10px_rgba(6,182,212,0.3)]">
                                    {uptime.replace('0h ', '')}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* BOTTOM NEON LINE */}
            <div className={clsx(
                "absolute bottom-0 left-1/2 -translate-x-1/2 w-[60%] h-[1px] bg-gradient-to-r from-transparent via-synapse-primary to-transparent opacity-0 group-hover:opacity-100 transition-all duration-700 blur-[2px]",
                isOnline && "opacity-40"
            )} />
        </div>
    );
}
