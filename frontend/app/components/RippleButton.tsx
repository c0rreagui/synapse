'use client';

import { ReactNode, useState } from 'react';

interface RippleButtonProps {
    children: ReactNode;
    onClick?: () => void;
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    fullWidth?: boolean;
    icon?: ReactNode;
    loading?: boolean;
}

export default function RippleButton({
    children,
    onClick,
    variant = 'primary',
    size = 'md',
    disabled = false,
    fullWidth = false,
    icon,
    loading = false,
}: RippleButtonProps) {
    const [ripples, setRipples] = useState<{ x: number; y: number; id: number }[]>([]);

    const variants = {
        primary: { bg: 'var(--gradient-green)', color: '#fff', border: 'none' },
        secondary: { bg: '#21262d', color: 'var(--cmd-text)', border: '1px solid var(--cmd-border)' },
        danger: { bg: 'var(--cmd-red)', color: '#fff', border: 'none' },
        ghost: { bg: 'transparent', color: 'var(--cmd-text-muted)', border: 'none' },
    };

    const sizes = {
        sm: { padding: '6px 12px', fontSize: '12px', gap: '6px' },
        md: { padding: '10px 18px', fontSize: '13px', gap: '8px' },
        lg: { padding: '14px 24px', fontSize: '14px', gap: '10px' },
    };

    const v = variants[variant];
    const s = sizes[size];

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
        if (disabled || loading) return;

        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const id = Date.now();

        setRipples(prev => [...prev, { x, y, id }]);
        setTimeout(() => setRipples(prev => prev.filter(r => r.id !== id)), 600);

        onClick?.();
    };

    return (
        <button
            onClick={handleClick}
            disabled={disabled || loading}
            style={{
                position: 'relative',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: s.gap,
                padding: s.padding,
                fontSize: s.fontSize,
                fontWeight: 500,
                color: v.color,
                background: v.bg,
                border: v.border,
                borderRadius: 'var(--radius-md)',
                cursor: disabled || loading ? 'not-allowed' : 'pointer',
                opacity: disabled ? 0.5 : 1,
                overflow: 'hidden',
                transition: 'all 0.2s',
                width: fullWidth ? '100%' : 'auto',
            }}
        >
            {loading && (
                <span style={{
                    width: '14px',
                    height: '14px',
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTopColor: '#fff',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                }} />
            )}
            {!loading && icon}
            {children}

            {/* Ripple effects */}
            {ripples.map(ripple => (
                <span
                    key={ripple.id}
                    style={{
                        position: 'absolute',
                        left: ripple.x,
                        top: ripple.y,
                        width: '4px',
                        height: '4px',
                        backgroundColor: 'rgba(255,255,255,0.4)',
                        borderRadius: '50%',
                        transform: 'translate(-50%, -50%)',
                        animation: 'ripple 0.6s ease-out forwards',
                    }}
                />
            ))}

            <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes ripple {
          to { 
            width: 200px; 
            height: 200px; 
            opacity: 0; 
          }
        }
      `}</style>
        </button>
    );
}
