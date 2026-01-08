'use client';

import { WifiIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface ConnectionStatusProps {
    isOnline: boolean;
    lastUpdate?: string;
}

export default function ConnectionStatus({ isOnline, lastUpdate }: ConnectionStatusProps) {
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '20px',
                backgroundColor: isOnline ? 'rgba(63,185,80,0.15)' : 'rgba(248,81,73,0.15)',
                border: `1px solid ${isOnline ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}`,
                transition: 'all 0.3s ease',
            }}
        >
            {isOnline ? (
                <WifiIcon style={{ width: '14px', height: '14px', color: '#3fb950' }} />
            ) : (
                <ExclamationTriangleIcon style={{ width: '14px', height: '14px', color: '#f85149' }} />
            )}
            <span style={{
                fontSize: '11px',
                color: isOnline ? '#3fb950' : '#f85149',
                fontWeight: 500,
            }}>
                {isOnline ? 'Online' : 'Offline'}
            </span>
            {lastUpdate && isOnline && (
                <span style={{
                    fontSize: '10px',
                    color: '#8b949e',
                    marginLeft: '4px',
                }}>
                    · {lastUpdate}
                </span>
            )}
        </div>
    );
}
