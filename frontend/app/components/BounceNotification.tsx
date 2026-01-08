'use client';

import { ReactNode, useState, useRef, useEffect } from 'react';

interface BounceNotificationProps {
    children: ReactNode;
    show: boolean;
    onClose?: () => void;
    duration?: number;
    position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export default function BounceNotification({
    children,
    show,
    onClose,
    duration = 5000,
    position = 'top-right',
}: BounceNotificationProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (show) {
            setIsVisible(true);
            if (duration > 0) {
                const timer = setTimeout(() => {
                    setIsVisible(false);
                    setTimeout(() => onClose?.(), 300);
                }, duration);
                return () => clearTimeout(timer);
            }
        }
    }, [show, duration, onClose]);

    const positions = {
        'top-right': { top: '24px', right: '24px' },
        'top-left': { top: '24px', left: '24px' },
        'bottom-right': { bottom: '24px', right: '24px' },
        'bottom-left': { bottom: '24px', left: '24px' },
    };

    if (!show && !isVisible) return null;

    return (
        <div
            style={{
                position: 'fixed',
                ...positions[position],
                zIndex: 10000,
                animation: isVisible ? 'bounceIn 0.5s ease' : 'bounceOut 0.3s ease forwards',
            }}
        >
            {children}

            <style jsx>{`
        @keyframes bounceIn {
          0% { transform: scale(0); opacity: 0; }
          50% { transform: scale(1.1); }
          70% { transform: scale(0.95); }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes bounceOut {
          0% { transform: scale(1); opacity: 1; }
          100% { transform: scale(0); opacity: 0; }
        }
      `}</style>
        </div>
    );
}
