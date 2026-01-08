'use client';

import { useState, useEffect } from 'react';

interface EstimatedTimeProps {
    startTime: Date;
    totalItems: number;
    completedItems: number;
    showRemaining?: boolean;
}

export default function EstimatedTime({
    startTime,
    totalItems,
    completedItems,
    showRemaining = true,
}: EstimatedTimeProps) {
    const [eta, setEta] = useState<string | null>(null);
    const [remaining, setRemaining] = useState<string | null>(null);

    useEffect(() => {
        requestAnimationFrame(() => {
            if (completedItems === 0 || completedItems >= totalItems) {
                setEta(prev => prev ? null : prev);
                setRemaining(prev => prev ? null : prev);
                return;
            }

            const elapsed = Date.now() - startTime.getTime();
            const avgTimePerItem = elapsed / completedItems;
            const remainingItems = totalItems - completedItems;
            const remainingMs = avgTimePerItem * remainingItems;
            const etaDate = new Date(Date.now() + remainingMs);

            // Format ETA
            setEta(etaDate.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));

            // Format remaining time
            const remainingSec = Math.floor(remainingMs / 1000);
            const remainingMin = Math.floor(remainingSec / 60);

            if (remainingMin >= 60) {
                const hours = Math.floor(remainingMin / 60);
                const mins = remainingMin % 60;
                setRemaining(`~${hours}h ${mins}min`);
            } else if (remainingMin > 0) {
                setRemaining(`~${remainingMin}min`);
            } else {
                setRemaining(`~${remainingSec}s`);
            }
        });
    }, [startTime, totalItems, completedItems]);

    if (!eta) return null;

    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--cmd-text-muted)',
        }}>
            <span>⏱️ ETA: {eta}</span>
            {showRemaining && remaining && (
                <span style={{ color: 'var(--cmd-text-faint)' }}>({remaining})</span>
            )}
        </div>
    );
}
