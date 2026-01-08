'use client';

import { ReactNode } from 'react';

interface DividerProps {
    orientation?: 'horizontal' | 'vertical';
    spacing?: 'sm' | 'md' | 'lg';
    label?: ReactNode;
}

export default function Divider({
    orientation = 'horizontal',
    spacing = 'md',
    label,
}: DividerProps) {
    const spacingValues = {
        sm: '8px',
        md: '16px',
        lg: '24px',
    };

    const s = spacingValues[spacing];

    if (orientation === 'vertical') {
        return (
            <div style={{
                width: '1px',
                backgroundColor: 'var(--cmd-border)',
                margin: `0 ${s}`,
                alignSelf: 'stretch',
            }} />
        );
    }

    if (label) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                margin: `${s} 0`,
            }}>
                <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--cmd-border)' }} />
                <span style={{ fontSize: '12px', color: 'var(--cmd-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    {label}
                </span>
                <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--cmd-border)' }} />
            </div>
        );
    }

    return (
        <div style={{
            height: '1px',
            backgroundColor: 'var(--cmd-border)',
            margin: `${s} 0`,
        }} />
    );
}
