'use client';

import { useState, useCallback } from 'react';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

interface RetryCounterProps {
    maxRetries?: number;
    onRetry: () => Promise<boolean>; // returns true if successful
    onMaxRetriesReached?: () => void;
    children: React.ReactNode;
}

export default function RetryCounter({
    maxRetries = 3,
    onRetry,
    onMaxRetriesReached,
    children,
}: RetryCounterProps) {
    const [retryCount, setRetryCount] = useState(0);
    const [isRetrying, setIsRetrying] = useState(false);
    const [showRetry, setShowRetry] = useState(false);

    const handleRetry = useCallback(async () => {
        if (retryCount >= maxRetries) {
            onMaxRetriesReached?.();
            return;
        }

        setIsRetrying(true);
        const success = await onRetry();
        setIsRetrying(false);

        if (success) {
            setShowRetry(false);
            setRetryCount(0);
        } else {
            setRetryCount(prev => prev + 1);
        }
    }, [retryCount, maxRetries, onRetry, onMaxRetriesReached]);

    // Expose method to show retry UI
    const triggerRetry = useCallback(() => {
        setShowRetry(true);
    }, []);

    if (!showRetry) {
        return <>{children}</>;
    }

    return (
        <div style={{
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--cmd-red-bg)',
            border: '1px solid var(--cmd-red-border)',
        }}>
            <div style={{ marginBottom: '12px' }}>
                {children}
            </div>

            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
            }}>
                <span style={{ fontSize: '12px', color: 'var(--cmd-red)' }}>
                    Tentativa {retryCount + 1}/{maxRetries}
                </span>

                <button
                    onClick={handleRetry}
                    disabled={isRetrying || retryCount >= maxRetries}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 14px',
                        fontSize: '12px',
                        fontWeight: 500,
                        color: '#fff',
                        backgroundColor: 'var(--cmd-red)',
                        border: 'none',
                        borderRadius: 'var(--radius-sm)',
                        cursor: retryCount >= maxRetries ? 'not-allowed' : 'pointer',
                        opacity: retryCount >= maxRetries ? 0.5 : 1,
                    }}
                >
                    <ArrowPathIcon style={{
                        width: '14px',
                        height: '14px',
                        animation: isRetrying ? 'spin 1s linear infinite' : 'none',
                    }} />
                    {retryCount >= maxRetries ? 'Limite atingido' : 'Tentar novamente'}
                </button>
            </div>

            <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}
