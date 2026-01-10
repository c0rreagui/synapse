'use client';

import { CpuChipIcon, BoltIcon, ExclamationTriangleIcon, PauseIcon } from '@heroicons/react/24/outline';

export interface BotProps {
    id: string;
    name: string;
    role: 'UPLOADER' | 'FACTORY' | 'MONITOR' | 'SCHEDULER';
    status: 'online' | 'offline' | 'error' | 'sleeping';
    currentTask?: string;
    uptime?: string;
}

export default function BotCard({ name, role, status, currentTask, uptime }: BotProps) {
    const isOnline = status === 'online';
    const isError = status === 'error';

    // Cores baseadas no status
    const statusColor = isError ? 'var(--cmd-red)' : isOnline ? 'var(--cmd-green)' : 'var(--cmd-text-muted)';
    const borderColor = isOnline ? 'var(--cmd-purple)' : 'var(--cmd-border)';
    const bgGlow = isOnline ? 'rgba(167, 139, 250, 0.05)' : 'transparent';

    return (
        <div className="relative group overflow-hidden rounded-xl border border-cmd-border bg-cmd-surface p-4 transition-all duration-300 hover:border-cmd-purple hover:shadow-[0_0_20px_rgba(167,139,250,0.15)]">

            {/* Status Indicator Line */}
            <div className="absolute top-0 left-0 w-full h-1" style={{ backgroundColor: statusColor }} />

            <div className="flex items-start gap-4">
                {/* Avatar / Icon Container */}
                <div className={`
                    w-12 h-12 rounded-lg flex items-center justify-center border
                    ${isOnline ? 'border-cmd-purple animate-pulse-slow' : 'border-cmd-border'}
                `} style={{ backgroundColor: bgGlow }}>
                    {role === 'UPLOADER' && <BoltIcon className="w-6 h-6 text-cmd-purple" />}
                    {role === 'FACTORY' && <CpuChipIcon className="w-6 h-6 text-cmd-blue" />}
                    {role === 'MONITOR' && <ExclamationTriangleIcon className="w-6 h-6 text-cmd-yellow" />}
                    {role === 'SCHEDULER' && <PauseIcon className="w-6 h-6 text-cmd-green" />}
                </div>

                {/* Info */}
                <div className="flex-1">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-cmd-text font-bold text-sm tracking-wide">{name}</h3>
                            <span className="text-[10px] font-mono text-cmd-text-muted bg-cmd-card px-1.5 py-0.5 rounded border border-cmd-border/50">
                                {role}
                            </span>
                        </div>

                        {/* Status Badge */}
                        <div className="flex items-center gap-1.5">
                            <div className={`w-2 h-2 rounded-full ${isOnline ? 'animate-ping' : ''}`} style={{ backgroundColor: statusColor }} />
                            <span className="text-[10px] font-bold uppercase" style={{ color: statusColor }}>
                                {status}
                            </span>
                        </div>
                    </div>

                    {/* Task Display */}
                    <div className="mt-3">
                        <p className="text-[11px] text-cmd-text-muted mb-1">CURRENT_TASK:</p>
                        <div className="bg-black/50 rounded p-2 border border-cmd-border/30 h-8 flex items-center">
                            <code className="text-[10px] text-cmd-green font-mono truncate w-full">
                                {isOnline ? `> ${currentTask || 'IDLE_WAITING_QUEUE...'}` : 'OFFLINE'}
                            </code>
                        </div>
                    </div>

                    {/* Footer / Uptime */}
                    {uptime && (
                        <div className="mt-2 flex justify-end">
                            <span className="text-[9px] text-cmd-text-muted font-mono">UPTIME: {uptime}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
