'use client';
import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { BackendStatus, TikTokProfile, ScheduleEvent, PendingVideo } from '../types';
import { getApiUrl } from '../utils/apiClient';

interface LogEntry {
    id: string;
    timestamp: string;
    level: 'info' | 'success' | 'warning' | 'error';
    message: string;
    source: string;
}

interface WebSocketMessage {
    type: string;
    data: any;
}

interface WebSocketContextValue {
    isConnected: boolean;
    subscribe: (handler: WebSocketHandler) => () => void;
}

interface WebSocketHandler {
    onPipelineUpdate?: (data: BackendStatus) => void;
    onLogEntry?: (data: LogEntry) => void;
    onProfileChange?: (data: TikTokProfile) => void;
    onScheduleUpdate?: (data: ScheduleEvent[]) => void;
    onQueueUpdate?: (data: PendingVideo[]) => void;
}

export const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const handlersRef = useRef<Set<WebSocketHandler>>(new Set());
    const isConnectingRef = useRef(false);
    const [retryCount, setRetryCount] = useState(0);

    const connect = () => {
        // Prevent multiple simultaneous connection attempts
        if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
            return;
        }

        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        if (wsRef.current) {
            if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
                wsRef.current.close();
            }
        }

        isConnectingRef.current = true;
        const apiBase = getApiUrl().replace('http', 'ws').replace('https', 'wss');
        const ws = new WebSocket(`${apiBase}/ws/updates`);

        ws.onopen = () => {
            setIsConnected(true);
            isConnectingRef.current = false;
            setRetryCount(0); // Reset backoff on success
        };

        ws.onclose = () => {
            setIsConnected(false);
            isConnectingRef.current = false;

            // Exponential Backoff: 3s -> 6s -> 12s -> 24s -> 30s (max)
            const baseDelay = 3000;
            const delay = Math.min(baseDelay * Math.pow(2, retryCount), 30000);

            console.log(`🔌 WS Closed. Reconnecting in ${delay}ms (Attempt ${retryCount + 1})`);

            reconnectTimeoutRef.current = setTimeout(() => {
                setRetryCount(prev => prev + 1);
                connect();
            }, delay);
        };

        ws.onerror = () => {
            // Just let close handler trigger reconnect
            isConnectingRef.current = false;
        };

        wsRef.current = ws;
    };

    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, []);

    const subscribe = (handler: WebSocketHandler) => {
        handlersRef.current.add(handler);

        // Return unsubscribe function
        return () => {
            handlersRef.current.delete(handler);
        };
    };

    return (
        <WebSocketContext.Provider value={{ isConnected, subscribe }}>
            {children}
        </WebSocketContext.Provider>
    );
}

export function useWebSocketContext() {
    const context = useContext(WebSocketContext);
    if (!context) {
        throw new Error('useWebSocketContext must be used within WebSocketProvider');
    }
    return context;
}
