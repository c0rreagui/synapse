'use client';

import { ReactNode } from 'react';

interface BadgeProps {
    children: ReactNode;
    variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral';
    size?: 'sm' | 'md';
    dot?: boolean;
}

export default function Badge({
    children,
    variant = 'neutral',
    size = 'md',
    dot = false,
}: BadgeProps) {
    const colors = {
        success: { bg: 'var(--cmd-green-bg)', text: 'var(--cmd-green)', border: 'var(--cmd-green-border)' },
        error: { bg: 'var(--cmd-red-bg)', text: 'var(--cmd-red)', border: 'var(--cmd-red-border)' },
        warning: { bg: 'var(--cmd-yellow-bg)', text: 'var(--cmd-yellow)', border: 'var(--cmd-yellow-border)' },
        info: { bg: 'var(--cmd-blue-bg)', text: 'var(--cmd-blue)', border: 'var(--cmd-blue-border)' },
        neutral: { bg: '#21262d', text: '#8b949e', border: '#30363d' },
    };

    const sizes = {
        sm: { padding: '2px 6px', fontSize: '10px' },
        md: { padding: '4px 10px', fontSize: '11px' },
    };

    const c = colors[variant];
    const s = sizes[size];

    return (
        <span
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: s.padding,
                fontSize: s.fontSize,
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.03em',
                color: c.text,
                backgroundColor: c.bg,
                border: `1px solid ${c.border}`,
                borderRadius: '6px',
            }}
        >
            {dot && (
                <span style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: c.text,
                }} />
            )}
            {children}
        </span>
    );
}
