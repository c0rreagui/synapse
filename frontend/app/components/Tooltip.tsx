'use client';

import { useState, useRef, ReactNode } from 'react';

interface TooltipProps {
    content: ReactNode;
    shortcut?: string;
    children: ReactNode;
    position?: 'top' | 'bottom' | 'left' | 'right';
    delay?: number;
}

export default function Tooltip({
    content,
    shortcut,
    children,
    position = 'top',
    delay = 300,
}: TooltipProps) {
    const [isVisible, setIsVisible] = useState(false);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

    const show = () => {
        timeoutRef.current = setTimeout(() => setIsVisible(true), delay);
    };

    const hide = () => {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        setIsVisible(false);
    };

    const positions = {
        top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px' },
        bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '8px' },
        left: { right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: '8px' },
        right: { left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: '8px' },
    };

    return (
        <div
            style={{ position: 'relative', display: 'inline-flex' }}
            onMouseEnter={show}
            onMouseLeave={hide}
        >
            {children}
            {isVisible && (
                <div
                    style={{
                        position: 'absolute',
                        ...positions[position],
                        padding: '8px 12px',
                        backgroundColor: '#1c2128',
                        border: '1px solid #30363d',
                        borderRadius: '8px',
                        boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                        whiteSpace: 'nowrap',
                        zIndex: 1000,
                        animation: 'fadeIn 0.15s ease-out',
                    }}
                >
                    <style jsx>{`
            @keyframes fadeIn {
              from { opacity: 0; transform: translateX(-50%) translateY(4px); }
              to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
          `}</style>
                    <div style={{ fontSize: '12px', color: '#c9d1d9' }}>{content}</div>
                    {shortcut && (
                        <div style={{
                            marginTop: '4px',
                            fontSize: '10px',
                            color: '#6e7681',
                            fontFamily: 'monospace',
                            padding: '2px 6px',
                            backgroundColor: '#21262d',
                            borderRadius: '4px',
                            display: 'inline-block',
                        }}>
                            {shortcut}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
