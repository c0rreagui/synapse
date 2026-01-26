import { useRef, useEffect, useState } from 'react';
import { CommandLineIcon, TrashIcon, FunnelIcon } from '@heroicons/react/24/outline';

export interface LogEntry {
    timestamp: string;
    level: 'info' | 'warning' | 'error' | 'success';
    message: string;
}

interface Props {
    logs?: (string | LogEntry)[];
    className?: string;
    autoScroll?: boolean;
}

export default function LogTerminal({ logs = [], className = '', autoScroll = false }: Props) {
    const bottomRef = useRef<HTMLDivElement>(null);
    const [filter, setFilter] = useState<'all' | 'error'>('all');

    // Parse logs if they are strings
    const parsedLogs: LogEntry[] = logs.map(log => {
        if (typeof log === 'string') {
            // Try to deduce level from string content
            let level: LogEntry['level'] = 'info';
            if (log.toLowerCase().includes('error') || log.toLowerCase().includes('fail')) level = 'error';
            if (log.toLowerCase().includes('success') || log.toLowerCase().includes('done')) level = 'success';
            if (log.toLowerCase().includes('warn')) level = 'warning';
            return { timestamp: new Date().toLocaleTimeString(), level, message: log };
        }
        return log;
    });

    const filteredLogs = filter === 'all'
        ? parsedLogs
        : parsedLogs.filter(l => l.level === 'error');

    // Auto-scroll (Optional)
    useEffect(() => {
        if (autoScroll) {
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, autoScroll]);

    return (
        <div className={`bg-black border border-green-900/50 rounded-lg flex flex-col overflow-hidden font-mono text-xs ${className}`}>
            {/* Terminal Header */}
            <div className="flex items-center justify-between px-3 py-2 bg-green-900/10 border-b border-green-900/30">
                <div className="flex items-center gap-2 text-green-500">
                    <CommandLineIcon className="w-4 h-4" />
                    <span className="font-bold tracking-wider">TERMINAL_OUTPUT</span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setFilter(prev => prev === 'all' ? 'error' : 'all')}
                        className={`px-2 py-1 rounded flex items-center gap-1 transition-colors ${filter === 'error' ? 'bg-red-900/30 text-red-400' : 'text-green-700 hover:text-green-400'}`}
                    >
                        <FunnelIcon className="w-3 h-3" />
                        {filter === 'all' ? 'ALL_LOGS' : 'ERRORS_ONLY'}
                    </button>
                    <div className="w-px h-3 bg-green-900/50"></div>
                    <button className="text-green-700 hover:text-green-400 transition-colors" title="Clear Buffer">
                        <TrashIcon className="w-3 h-3" />
                    </button>
                </div>
            </div>

            {/* Logs Area */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin scrollbar-thumb-green-900 scrollbar-track-black">
                {filteredLogs.length === 0 && (
                    <div className="text-gray-700 opacity-50 italic text-center mt-10">
                      // WAITING_FOR_INPUT...
                    </div>
                )}

                {filteredLogs.map((log, i) => (
                    <div key={i} className="flex gap-2 group hover:bg-green-900/5 px-1 rounded-sm">
                        <span className="text-gray-600 shrink-0 select-none">[{log.timestamp}]</span>
                        <span className={`break-all ${log.level === 'error' ? 'text-red-500 font-bold' :
                            log.level === 'success' ? 'text-green-400' :
                                log.level === 'warning' ? 'text-yellow-500' :
                                    'text-gray-300'
                            }`}>
                            {log.level === 'error' && '❌ '}
                            {log.level === 'success' && '✅ '}
                            {log.level === 'warning' && '⚠️ '}
                            <span className="opacity-90 group-hover:opacity-100">{log.message}</span>
                        </span>
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    );
}
