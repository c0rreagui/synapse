'use client';

import { useState, useEffect, useCallback } from 'react';
import { ArrowUturnLeftIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface UndoToastProps {
    message: string;
    duration?: number;
    onUndo: () => void;
    onTimeout: () => void;
    onClose: () => void;
}

export default function UndoToast({
    message,
    duration = 5000,
    onUndo,
    onTimeout,
    onClose,
}: UndoToastProps) {
    const [timeLeft, setTimeLeft] = useState(duration);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        requestAnimationFrame(() => setIsVisible(true));
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 100) {
                    clearInterval(interval);
                    onTimeout();
                    return 0;
                }
                return prev - 100;
            });
        }, 100);

        return () => clearInterval(interval);
    }, [onTimeout]);

    const handleUndo = useCallback(() => {
        setIsVisible(false);
        setTimeout(onUndo, 200);
    }, [onUndo]);

    const handleClose = useCallback(() => {
        setIsVisible(false);
        setTimeout(onClose, 200);
    }, [onClose]);

    const progressPercent = (timeLeft / duration) * 100;

    return (
        <div
            style={{
                position: 'fixed',
                bottom: '24px',
                right: '24px',
                display: 'flex',
                flexDirection: 'column',
                minWidth: '320px',
                borderRadius: '12px',
                backgroundColor: 'rgba(28,33,40,0.95)',
                border: '1px solid #30363d',
                backdropFilter: 'blur(12px)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                overflow: 'hidden',
                transform: isVisible ? 'translateY(0)' : 'translateY(100px)',
                opacity: isVisible ? 1 : 0,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                zIndex: 9999,
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '14px 16px' }}>
                <span style={{ fontSize: '14px', color: '#c9d1d9', flex: 1 }}>
                    {message}
                </span>
                <button
                    onClick={handleUndo}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 12px',
                        fontSize: '13px',
                        fontWeight: 500,
                        color: '#58a6ff',
                        backgroundColor: 'rgba(88,166,255,0.1)',
                        border: '1px solid rgba(88,166,255,0.3)',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                    }}
                >
                    <ArrowUturnLeftIcon style={{ width: '14px', height: '14px' }} />
                    Desfazer
                </button>
                <button
                    onClick={handleClose}
                    style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: '4px',
                        opacity: 0.6,
                    }}
                    aria-label="Fechar"
                    title="Fechar"
                >
                    <XMarkIcon style={{ width: '16px', height: '16px', color: '#8b949e' }} />
                </button>
            </div>
            {/* Progress bar countdown */}
            <div style={{
                height: '3px',
                width: `${progressPercent}%`,
                backgroundColor: '#58a6ff',
                transition: 'width 0.1s linear',
            }} />
        </div>
    );
}
