'use client';

import { useState, ReactNode, useRef, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface PopoverProps {
    trigger: ReactNode;
    content: ReactNode;
    position?: 'top' | 'bottom' | 'left' | 'right';
    title?: string;
    showClose?: boolean;
}

export default function Popover({
    trigger,
    content,
    position = 'bottom',
    title,
    showClose = false,
}: PopoverProps) {
    const [isOpen, setIsOpen] = useState(false);
    const popoverRef = useRef<HTMLDivElement>(null);
    const triggerRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        if (!isOpen) return;

        const handleClick = (e: MouseEvent) => {
            if (
                popoverRef.current &&
                !popoverRef.current.contains(e.target as Node) &&
                triggerRef.current &&
                !triggerRef.current.contains(e.target as Node)
            ) {
                setIsOpen(false);
            }
        };

        document.addEventListener('click', handleClick);
        return () => document.removeEventListener('click', handleClick);
    }, [isOpen]);

    const positions = {
        top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px' },
        bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '8px' },
        left: { right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: '8px' },
        right: { left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: '8px' },
    };

    return (
        <div style={{ position: 'relative', display: 'inline-flex' }}>
            <div ref={triggerRef} onClick={() => setIsOpen(!isOpen)}>
                {trigger}
            </div>

            {isOpen && (
                <div
                    ref={popoverRef}
                    style={{
                        position: 'absolute',
                        ...positions[position],
                        minWidth: '200px',
                        maxWidth: '320px',
                        backgroundColor: 'var(--cmd-surface)',
                        border: '1px solid var(--cmd-border)',
                        borderRadius: 'var(--radius-lg)',
                        boxShadow: 'var(--shadow-lg)',
                        zIndex: 1000,
                        animation: 'popIn 0.15s ease-out',
                    }}
                >
                    <style jsx>{`
            @keyframes popIn {
              from { opacity: 0; transform: translateX(-50%) scale(0.95); }
              to { opacity: 1; transform: translateX(-50%) scale(1); }
            }
          `}</style>

                    {(title || showClose) && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            padding: '12px 16px',
                            borderBottom: '1px solid var(--cmd-border)',
                        }}>
                            {title && (
                                <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--cmd-text)' }}>
                                    {title}
                                </span>
                            )}
                            {showClose && (
                                <button
                                    onClick={() => setIsOpen(false)}
                                    title="Fechar popover"
                                    aria-label="Fechar popover"
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}
                                >
                                    <XMarkIcon style={{ width: '16px', height: '16px', color: 'var(--cmd-text-muted)' }} />
                                </button>
                            )}
                        </div>
                    )}

                    <div style={{ padding: '12px 16px' }}>
                        {content}
                    </div>
                </div>
            )}
        </div>
    );
}
