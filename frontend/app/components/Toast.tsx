'use client';

import { useEffect, useState } from 'react';
import { CheckCircleIcon, XCircleIcon, InformationCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface ToastProps {
    message: string;
    type: 'success' | 'error' | 'info' | 'warning';
    duration?: number;
    onClose: () => void;
}

export default function Toast({ message, type, duration = 3000, onClose }: ToastProps) {
    const [isVisible, setIsVisible] = useState(false);
    const [isLeaving, setIsLeaving] = useState(false);

    useEffect(() => {
        // Animate in
        requestAnimationFrame(() => setIsVisible(true));

        // Auto-close
        const timer = setTimeout(() => {
            setIsLeaving(true);
            setTimeout(onClose, 300);
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    const colors = {
        success: { bg: 'rgba(63,185,80,0.15)', border: 'rgba(63,185,80,0.4)', text: '#3fb950', icon: CheckCircleIcon },
        error: { bg: 'rgba(248,81,73,0.15)', border: 'rgba(248,81,73,0.4)', text: '#f85149', icon: XCircleIcon },
        info: { bg: 'rgba(88,166,255,0.15)', border: 'rgba(88,166,255,0.4)', text: '#58a6ff', icon: InformationCircleIcon },
        warning: { bg: 'rgba(240,136,62,0.15)', border: 'rgba(240,136,62,0.4)', text: '#f0883e', icon: InformationCircleIcon },
    };

    const config = colors[type];
    const Icon = config.icon;

    return (
        <div
            style={{
                position: 'fixed',
                bottom: '24px',
                right: '24px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '14px 18px',
                borderRadius: '10px',
                backgroundColor: config.bg,
                border: `1px solid ${config.border}`,
                backdropFilter: 'blur(12px)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                transform: isVisible && !isLeaving ? 'translateY(0)' : 'translateY(100px)',
                opacity: isVisible && !isLeaving ? 1 : 0,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                zIndex: 9999,
                maxWidth: '400px',
            }}
        >
            <Icon style={{ width: '20px', height: '20px', color: config.text, flexShrink: 0 }} />
            <span style={{ fontSize: '14px', color: config.text, fontWeight: 500, flex: 1 }}>
                {message}
            </span>
            <button
                onClick={() => { setIsLeaving(true); setTimeout(onClose, 300); }}
                style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    opacity: 0.7,
                }}
                aria-label="Fechar notificação"
                title="Fechar"
            >
                <XMarkIcon style={{ width: '16px', height: '16px', color: config.text }} />
            </button>
        </div>
    );
}
