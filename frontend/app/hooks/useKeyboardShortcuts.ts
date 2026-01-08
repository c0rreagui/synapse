'use client';

import { useEffect, useCallback } from 'react';

interface Shortcut {
    key: string;
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    action: () => void;
    description: string;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
    const handleKeyDown = useCallback((e: KeyboardEvent) => {
        // Ignora se estiver digitando em input/textarea
        if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
            return;
        }

        for (const shortcut of shortcuts) {
            const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();
            const ctrlMatch = !!shortcut.ctrl === (e.ctrlKey || e.metaKey);
            const shiftMatch = !!shortcut.shift === e.shiftKey;
            const altMatch = !!shortcut.alt === e.altKey;

            if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
                e.preventDefault();
                shortcut.action();
                return;
            }
        }
    }, [shortcuts]);

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);
}

// Formata shortcut para exibição
export function formatShortcut(shortcut: Omit<Shortcut, 'action' | 'description'>): string {
    const parts = [];
    if (shortcut.ctrl) parts.push('Ctrl');
    if (shortcut.shift) parts.push('Shift');
    if (shortcut.alt) parts.push('Alt');
    parts.push(shortcut.key.toUpperCase());
    return parts.join('+');
}

// Exemplo de uso:
// useKeyboardShortcuts([
//   { key: 'k', ctrl: true, action: () => setShowPalette(true), description: 'Abrir Command Palette' },
//   { key: '/', action: () => inputRef.current?.focus(), description: 'Focar busca' },
//   { key: 'n', ctrl: true, shift: true, action: createNew, description: 'Novo item' },
// ]);
