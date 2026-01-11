'use client';

import { CpuChipIcon, BoltIcon, ExclamationTriangleIcon, PauseIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { StitchCard } from './StitchCard';

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
    const isSleeping = status === 'sleeping';

    const statusColors = {
        online: 'text-synapse-emerald bg-synapse-emerald',
        offline: 'text-gray-500 bg-gray-500',
        error: 'text-red-500 bg-red-500',
        sleeping: 'text-synapse-amber bg-synapse-amber',
    };

    const [textColorClass, bgColorClass] = (statusColors[status] || statusColors.offline).split(' ');

    return (
        <StitchCard className="relative overflow-hidden p-4 group">
            {/* Status Indicator Line */}
            <div className={clsx("absolute top-0 left-0 w-full h-1 transition-colors", bgColorClass)} />

            <div className="flex items-start gap-4">
                {/* Avatar / Icon Container */}
                <div className={clsx(
                    "w-12 h-12 rounded-lg flex items-center justify-center border transition-all",
                    isOnline
                        ? "border-synapse-primary bg-synapse-primary/5 animate-pulse-slow shadow-[0_0_15px_rgba(139,92,246,0.2)]"
                        : "border-white/10 bg-black/20"
                )}>
                    {role === 'UPLOADER' && <BoltIcon className="w-6 h-6 text-synapse-primary" />}
                    {role === 'FACTORY' && <CpuChipIcon className="w-6 h-6 text-synapse-cyan" />}
                    {role === 'MONITOR' && <ExclamationTriangleIcon className="w-6 h-6 text-synapse-amber" />}
                    {role === 'SCHEDULER' && <PauseIcon className="w-6 h-6 text-synapse-emerald" />}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-white font-bold text-sm tracking-wide truncate">{name}</h3>
                            <span className="text-[10px] font-mono text-gray-400 bg-white/5 px-1.5 py-0.5 rounded border border-white/10 inline-block mt-1">
                                {role}
                            </span>
                        </div>

                        {/* Status Badge */}
                        <div className="flex items-center gap-1.5 shrink-0">
                            <div className={clsx("w-2 h-2 rounded-full", bgColorClass, isOnline && 'animate-ping')} />
                            <span className={clsx("text-[10px] font-bold uppercase", textColorClass)}>
                                {status}
                            </span>
                        </div>
                    </div>

                    {/* Task Display */}
                    <div className="mt-3">
                        <p className="text-[11px] text-gray-500 mb-1 font-mono uppercase tracking-wider">Current_Task:</p>
                        <div className="bg-black/50 rounded p-2 border border-white/10 h-8 flex items-center overflow-hidden">
                            <code className={clsx("text-[10px] font-mono truncate w-full", isOnline ? "text-synapse-emerald" : "text-gray-600")}>
                                {isOnline || isSleeping ? `> ${currentTask || 'IDLE_WAITING_QUEUE...'}` : 'OFFLINE'}
                            </code>
                        </div>
                    </div>

                    {/* Footer / Uptime */}
                    {uptime && (
                        <div className="mt-2 flex justify-end">
                            <span className="text-[9px] text-gray-500 font-mono">UPTIME: {uptime}</span>
                        </div>
                    )}
                </div>
            </div>
        </StitchCard>
    );
}
