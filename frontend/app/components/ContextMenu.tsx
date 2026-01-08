'use client';

import { useState, useEffect, useRef, ReactNode } from 'react';

interface ContextMenuItem {
    id: string;
    label: string;
    icon?: ReactNode;
    shortcut?: string;
    danger?: boolean;
    disabled?: boolean;
    action: () => void;
}

interface ContextMenuProps {
    items: ContextMenuItem[];
    children: ReactNode;
}

export default function ContextMenu({ items, children }: ContextMenuProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const menuRef = useRef<HTMLDivElement>(null);

    const handleContextMenu = (e: React.MouseEvent) => {
        e.preventDefault();
        setPosition({ x: e.clientX, y: e.clientY });
        setIsOpen(true);
    };

    // Close on click outside
    useEffect(() => {
        if (!isOpen) return;

        const handleClick = () => setIsOpen(false);
        const handleEsc = (e: KeyboardEvent) => e.key === 'Escape' && setIsOpen(false);

        window.addEventListener('click', handleClick);
        window.addEventListener('keydown', handleEsc);

        return () => {
            window.removeEventListener('click', handleClick);
            window.removeEventListener('keydown', handleEsc);
        };
    }, [isOpen]);

    return (
        <>
            <div onContextMenu={handleContextMenu}>
                {children}
            </div>

            {isOpen && (
                <div
                    ref={menuRef}
                    style={{
                        position: 'fixed',
                        left: position.x,
                        top: position.y,
                        minWidth: '180px',
                        backgroundColor: '#161b22',
                        border: '1px solid #30363d',
                        borderRadius: '10px',
                        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                        padding: '6px',
                        zIndex: 10000,
                        animation: 'fadeIn 0.1s ease-out',
                    }}
                    onClick={(e) => e.stopPropagation()}
                >
                    <style jsx>{`
            @keyframes fadeIn {
              from { opacity: 0; transform: scale(0.95); }
              to { opacity: 1; transform: scale(1); }
            }
          `}</style>

                    {items.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => { item.action(); setIsOpen(false); }}
                            disabled={item.disabled}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                width: '100%',
                                padding: '10px 12px',
                                backgroundColor: 'transparent',
                                border: 'none',
                                borderRadius: '6px',
                                color: item.danger ? '#f85149' : item.disabled ? '#6e7681' : '#c9d1d9',
                                fontSize: '13px',
                                cursor: item.disabled ? 'not-allowed' : 'pointer',
                                textAlign: 'left',
                                transition: 'background-color 0.15s',
                            }}
                            onMouseEnter={(e) => !item.disabled && (e.currentTarget.style.backgroundColor = '#21262d')}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                            {item.icon && <span style={{ opacity: 0.8 }}>{item.icon}</span>}
                            <span style={{ flex: 1 }}>{item.label}</span>
                            {item.shortcut && (
                                <span style={{
                                    fontSize: '11px',
                                    color: '#6e7681',
                                    fontFamily: 'monospace',
                                }}>
                                    {item.shortcut}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
            )}
        </>
    );
}
