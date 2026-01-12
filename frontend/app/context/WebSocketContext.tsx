'use client';
import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { BackendStatus, TikTokProfile } from '../types';

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
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const handlersRef = useRef<Set<WebSocketHandler>>(new Set());
    const isConnectingRef = useRef(false);

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
        const ws = new WebSocket('ws://localhost:8000/ws/updates');

        ws.onopen = () => {
            setIsConnected(true);
            isConnectingRef.current = false;
        };

        ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);

                // Broadcast to all subscribers
                handlersRef.current.forEach(handler => {
                    switch (message.type) {
                        case 'pipeline_update':
                            handler.onPipelineUpdate?.(message.data as BackendStatus);
                            break;
                        case 'log_entry':
                            handler.onLogEntry?.(message.data as LogEntry);
                            break;
                        case 'profile_change':
                            handler.onProfileChange?.(message.data as TikTokProfile);
                            break;
                        case 'ping':
                            ws.send('pong');
                            break;
                    }
                });
            } catch (err) {
                // Silently ignore parse errors to avoid cluttering console
            }
        };

        ws.onclose = () => {
            setIsConnected(false);
            isConnectingRef.current = false;

            // Reconnect after 3 seconds
            reconnectTimeoutRef.current = setTimeout(() => {
                connect();
            }, 3000);
        };

        ws.onerror = () => {
            // Error details are not available in browser WebSocket API
            // Silently handle to avoid empty error logs
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
