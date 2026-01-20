'use client';
import { useEffect, useState } from 'react';
import { useWebSocketContext } from '../context/WebSocketContext';
import { BackendStatus, TikTokProfile, ScheduleEvent, PendingVideo } from '../types';

interface LogEntry {
    id: string;
    timestamp: string;
    level: 'info' | 'success' | 'warning' | 'error';
    message: string;
    source: string;
}

interface UseWebSocketOptions {
    onPipelineUpdate?: (data: BackendStatus) => void;
    onLogEntry?: (data: LogEntry) => void;
    onProfileChange?: (data: TikTokProfile) => void;
    onScheduleUpdate?: (data: ScheduleEvent[]) => void;
    onQueueUpdate?: (data: PendingVideo[]) => void;
}

/**
 * Hook to subscribe to WebSocket events from the global connection.
 * This replaces the old useWebSocket hook that created individual connections.
 */
export default function useWebSocket(options: UseWebSocketOptions = {}) {
    const { isConnected, subscribe } = useWebSocketContext();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    useEffect(() => {
        if (!mounted) return;

        // Subscribe to the global WebSocket
        const unsubscribe = subscribe(options);

        // Cleanup: unsubscribe when component unmounts
        return unsubscribe;
    }, [mounted, subscribe, options.onPipelineUpdate, options.onLogEntry, options.onProfileChange, options.onScheduleUpdate, options.onQueueUpdate]);

    return { isConnected };
}
