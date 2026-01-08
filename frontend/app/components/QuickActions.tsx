'use client';

import { ReactNode } from 'react';
import Tooltip from './Tooltip';

interface QuickAction {
    id: string;
    icon: ReactNode;
    label: string;
    shortcut?: string;
    onClick: () => void;
}

interface QuickActionsProps {
    actions: QuickAction[];
}

export default function QuickActions({ actions }: QuickActionsProps) {
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
        }}>
            {actions.map(action => (
                <Tooltip key={action.id} content={action.label} shortcut={action.shortcut}>
                    <button
                        onClick={action.onClick}
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '36px',
                            height: '36px',
                            backgroundColor: 'transparent',
                            border: '1px solid transparent',
                            borderRadius: '8px',
                            color: '#8b949e',
                            cursor: 'pointer',
                            transition: 'all 0.15s',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = '#21262d';
                            e.currentTarget.style.borderColor = '#30363d';
                            e.currentTarget.style.color = '#c9d1d9';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'transparent';
                            e.currentTarget.style.borderColor = 'transparent';
                            e.currentTarget.style.color = '#8b949e';
                        }}
                        aria-label={action.label}
                        title={action.shortcut ? `${action.label} (${action.shortcut})` : action.label}
                    >
                        {action.icon}
                    </button>
                </Tooltip>
            ))}
        </div>
    );
}
