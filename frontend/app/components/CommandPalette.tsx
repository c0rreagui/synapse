'use client';

import { useState, useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, DocumentIcon } from '@heroicons/react/24/outline';

interface CommandItem {
    id: string;
    title: string;
    description?: string;
    icon?: React.ReactNode;
    shortcut?: string;
    action: () => void;
    category?: string;
}

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
    commands: CommandItem[];
}

export default function CommandPalette({ isOpen, onClose, commands }: CommandPaletteProps) {
    const [query, setQuery] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);

    // Filter commands based on query
    const filteredCommands = commands.filter(cmd =>
        cmd.title.toLowerCase().includes(query.toLowerCase()) ||
        cmd.description?.toLowerCase().includes(query.toLowerCase()) ||
        cmd.category?.toLowerCase().includes(query.toLowerCase())
    );

    // Reset handled by component mounting/unmounting
    // useEffect(() => {
    //     if (isOpen) {
    //         setQuery('');
    //         setSelectedIndex(0);
    //         setTimeout(() => inputRef.current?.focus(), 50);
    //     }
    // }, [isOpen]);

    // Focus input on mount
    useEffect(() => {
        setTimeout(() => inputRef.current?.focus(), 50);
    }, []);

    // Keyboard navigation
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    setSelectedIndex(prev => Math.max(prev - 1, 0));
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (filteredCommands[selectedIndex]) {
                        filteredCommands[selectedIndex].action();
                        onClose();
                    }
                    break;
                case 'Escape':
                    onClose();
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, selectedIndex, filteredCommands, onClose]);

    if (!isOpen) return null;

    // Group commands by category
    const grouped = filteredCommands.reduce((acc, cmd) => {
        const cat = cmd.category || 'Geral';
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(cmd);
        return acc;
    }, {} as { [key: string]: CommandItem[] });

    return (
        <div
            style={{
                position: 'fixed',
                inset: 0,
                display: 'flex',
                justifyContent: 'center',
                paddingTop: '15vh',
                backgroundColor: 'rgba(0,0,0,0.7)',
                backdropFilter: 'blur(4px)',
                zIndex: 10000,
            }}
            onClick={onClose}
        >
            <div
                style={{
                    width: '100%',
                    maxWidth: '560px',
                    maxHeight: '400px',
                    backgroundColor: '#161b22',
                    borderRadius: '12px',
                    border: '1px solid #30363d',
                    boxShadow: '0 16px 48px rgba(0,0,0,0.5)',
                    overflow: 'hidden',
                    animation: 'slideDown 0.15s ease-out',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <style jsx>{`
          @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>

                {/* Search input */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '14px 16px',
                    borderBottom: '1px solid #30363d',
                }}>
                    <MagnifyingGlassIcon style={{ width: '20px', height: '20px', color: '#8b949e' }} />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
                        placeholder="Digite um comando..."
                        style={{
                            flex: 1,
                            background: 'none',
                            border: 'none',
                            outline: 'none',
                            fontSize: '15px',
                            color: '#c9d1d9',
                        }}
                    />
                    <span style={{ fontSize: '11px', color: '#6e7681', padding: '2px 6px', backgroundColor: '#21262d', borderRadius: '4px' }}>ESC</span>
                </div>

                {/* Results */}
                <div style={{ maxHeight: '320px', overflowY: 'auto', padding: '8px' }}>
                    {Object.entries(grouped).map(([category, items]) => (
                        <div key={category}>
                            <div style={{
                                fontSize: '11px',
                                color: '#8b949e',
                                padding: '8px 8px 6px',
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                            }}>
                                {category}
                            </div>
                            {items.map((cmd) => {
                                const globalIndex = filteredCommands.indexOf(cmd);
                                return (
                                    <div
                                        key={cmd.id}
                                        onClick={() => { cmd.action(); onClose(); }}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '12px',
                                            padding: '10px 12px',
                                            borderRadius: '8px',
                                            cursor: 'pointer',
                                            backgroundColor: globalIndex === selectedIndex ? '#21262d' : 'transparent',
                                            border: globalIndex === selectedIndex ? '1px solid #30363d' : '1px solid transparent',
                                        }}
                                    >
                                        <div style={{ color: '#8b949e', flexShrink: 0 }}>
                                            {cmd.icon || <DocumentIcon style={{ width: '18px', height: '18px' }} />}
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: '14px', color: '#c9d1d9' }}>{cmd.title}</div>
                                            {cmd.description && (
                                                <div style={{ fontSize: '12px', color: '#8b949e' }}>{cmd.description}</div>
                                            )}
                                        </div>
                                        {cmd.shortcut && (
                                            <span style={{
                                                fontSize: '11px',
                                                color: '#6e7681',
                                                padding: '2px 6px',
                                                backgroundColor: '#21262d',
                                                borderRadius: '4px',
                                                fontFamily: 'monospace',
                                            }}>
                                                {cmd.shortcut}
                                            </span>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    ))}
                    {filteredCommands.length === 0 && (
                        <div style={{ padding: '24px', textAlign: 'center', color: '#8b949e' }}>
                            Nenhum comando encontrado
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
