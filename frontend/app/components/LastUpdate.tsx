'use client';

import { useState, useEffect } from 'react';
import { ClockIcon } from '@heroicons/react/24/outline';

interface LastUpdateProps {
    timestamp: Date | string | null;
    prefix?: string;
    showIcon?: boolean;
    refreshInterval?: number; // ms to update relative time
}

export default function LastUpdate({
    timestamp,
    prefix = 'Atualizado',
    showIcon = true,
    refreshInterval = 30000, // 30 seconds
}: LastUpdateProps) {
    const [relativeTime, setRelativeTime] = useState('');

    useEffect(() => {
        if (!timestamp) return;

        const updateRelativeTime = () => {
            const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
            const now = new Date();
            const diffMs = now.getTime() - date.getTime();
            const diffSec = Math.floor(diffMs / 1000);
            const diffMin = Math.floor(diffSec / 60);
            const diffHour = Math.floor(diffMin / 60);

            if (diffSec < 10) {
                setRelativeTime('agora');
            } else if (diffSec < 60) {
                setRelativeTime(`há ${diffSec}s`);
            } else if (diffMin < 60) {
                setRelativeTime(`há ${diffMin}min`);
            } else if (diffHour < 24) {
                setRelativeTime(`há ${diffHour}h`);
            } else {
                setRelativeTime(date.toLocaleDateString('pt-BR'));
            }
        };

        updateRelativeTime();
        const interval = setInterval(updateRelativeTime, refreshInterval);
        return () => clearInterval(interval);
    }, [timestamp, refreshInterval]);

    if (!timestamp) return null;

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px',
            color: 'var(--cmd-text-muted)',
        }}>
            {showIcon && <ClockIcon style={{ width: '12px', height: '12px' }} />}
            <span>{prefix} {relativeTime}</span>
        </div>
    );
}
