'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

interface WebSocketMessage {
    type: string;
    data: unknown;
}

interface UseWebSocketOptions {
    onPipelineUpdate?: (data: unknown) => void;
    onLogEntry?: (data: unknown) => void;
    onProfileChange?: (data: unknown) => void;
}

export default function useWebSocket(options: UseWebSocketOptions = {}) {
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        // Limpa timeout de reconexão se existir
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        // Fecha conexão existente
        if (wsRef.current) {
            wsRef.current.close();
        }

        const ws = new WebSocket('ws://localhost:8000/ws/updates');

        ws.onopen = () => {
            console.log('🔌 WebSocket conectado');
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);

                switch (message.type) {
                    case 'pipeline_update':
                        options.onPipelineUpdate?.(message.data);
                        break;
                    case 'log_entry':
                        options.onLogEntry?.(message.data);
                        break;
                    case 'profile_change':
                        options.onProfileChange?.(message.data);
                        break;
                    case 'ping':
                        ws.send('pong');
                        break;
                    case 'connected':
                        console.log('✅ WebSocket pronto para receber updates');
                        break;
                }
            } catch (err) {
                console.error('Erro ao processar mensagem WebSocket:', err);
            }
        };

        ws.onclose = () => {
            console.log('❌ WebSocket desconectado');
            setIsConnected(false);

            // Reconectar após 3 segundos
            reconnectTimeoutRef.current = setTimeout(() => {
                console.log('🔄 Tentando reconectar...');
                connect();
            }, 3000);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        wsRef.current = ws;
    }, [options]);

    useEffect(() => {
        connect();

        // Cleanup
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return { isConnected };
}
