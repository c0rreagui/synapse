'use client';

import { useEffect, useRef, useCallback } from 'react';

interface UseAutoSaveOptions {
    data: unknown;
    key: string;
    interval?: number; // ms
    onSave?: () => void;
    onRestore?: (data: unknown) => void;
}

export function useAutoSave({
    data,
    key,
    interval = 30000, // 30 seconds
    onSave,
    onRestore,
}: UseAutoSaveOptions) {
    const dataRef = useRef(data);

    useEffect(() => {
        dataRef.current = data;
    }, [data]);

    // Save to localStorage
    const save = useCallback(() => {
        try {
            localStorage.setItem(`synapse-draft-${key}`, JSON.stringify({
                data: dataRef.current,
                savedAt: new Date().toISOString(),
            }));
            onSave?.();
        } catch (e) {
            console.error('AutoSave failed:', e);
        }
    }, [key, onSave]);

    // Restore from localStorage
    const restore = useCallback(() => {
        try {
            const saved = localStorage.getItem(`synapse-draft-${key}`);
            if (saved) {
                const parsed = JSON.parse(saved);
                onRestore?.(parsed.data);
                return parsed;
            }
        } catch (e) {
            console.error('AutoSave restore failed:', e);
        }
        return null;
    }, [key, onRestore]);

    // Clear saved draft
    const clear = useCallback(() => {
        localStorage.removeItem(`synapse-draft-${key}`);
    }, [key]);

    // Check if draft exists
    const hasDraft = useCallback(() => {
        return localStorage.getItem(`synapse-draft-${key}`) !== null;
    }, [key]);

    // Auto-save on interval
    useEffect(() => {
        const timer = setInterval(save, interval);
        return () => clearInterval(timer);
    }, [save, interval]);

    // Save before unload
    useEffect(() => {
        const handleBeforeUnload = () => save();
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [save]);

    return { save, restore, clear, hasDraft };
}
