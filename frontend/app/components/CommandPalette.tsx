'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, FileText } from 'lucide-react';

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
            className="fixed inset-0 flex justify-center pt-[15vh] bg-black/70 backdrop-blur-sm z-[10000]"
            onClick={onClose}
        >
            <div
                className="w-full max-w-[560px] max-h-[400px] bg-[#161b22] rounded-xl border border-[#30363d] shadow-2xl overflow-hidden animate-in fade-in slide-in-from-top-4 duration-150"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Search input */}
                <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[#30363d]">
                    <Search className="w-5 h-5 text-[#8b949e]" />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
                        placeholder="Digite um comando..."
                        className="flex-1 bg-transparent border-none outline-none text-[15px] text-[#c9d1d9] placeholder-[#484f58]"
                        autoFocus
                    />
                    <kbd className="text-[11px] text-[#8b949e] px-1.5 py-0.5 bg-[#21262d] rounded border border-[#30363d] font-mono">
                        ESC
                    </kbd>
                </div>

                {/* Results */}
                <div className="max-h-[320px] overflow-y-auto p-2 custom-scrollbar">
                    {Object.entries(grouped).map(([category, items]) => (
                        <div key={category}>
                            <div className="text-[11px] text-[#8b949e] px-2 py-1.5 uppercase tracking-wider font-semibold">
                                {category}
                            </div>
                            {items.map((cmd) => {
                                const globalIndex = filteredCommands.indexOf(cmd);
                                const isSelected = globalIndex === selectedIndex;
                                return (
                                    <div
                                        key={cmd.id}
                                        onClick={() => { cmd.action(); onClose(); }}
                                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${isSelected
                                                ? 'bg-[#21262d] text-white'
                                                : 'text-[#c9d1d9] hover:bg-[#21262d]/50'
                                            }`}
                                    >
                                        <div className={`flex-shrink-0 ${isSelected ? 'text-white' : 'text-[#8b949e]'}`}>
                                            {cmd.icon || <FileText className="w-4.5 h-4.5" />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm font-medium">{cmd.title}</div>
                                            {cmd.description && (
                                                <div className={`text-xs truncate ${isSelected ? 'text-[#8b949e]' : 'text-[#8b949e]/80'}`}>
                                                    {cmd.description}
                                                </div>
                                            )}
                                        </div>
                                        {cmd.shortcut && (
                                            <span className="text-[11px] text-[#8b949e] px-1.5 py-0.5 bg-[#21262d] rounded border border-[#30363d] font-mono">
                                                {cmd.shortcut}
                                            </span>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    ))}
                    {filteredCommands.length === 0 && (
                        <div className="py-8 text-center text-[#8b949e]">
                            <p>Nenhum comando encontrado</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
