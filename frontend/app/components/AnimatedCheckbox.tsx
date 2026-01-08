'use client';

import { useEffect, useState } from 'react';
import { CheckIcon } from '@heroicons/react/24/outline';

interface AnimatedCheckboxProps {
    checked: boolean;
    onChange: (checked: boolean) => void;
    label?: string;
    disabled?: boolean;
}

export default function AnimatedCheckbox({
    checked,
    onChange,
    label,
    disabled = false,
}: AnimatedCheckboxProps) {
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        if (checked) {
            setAnimate(true);
            setTimeout(() => setAnimate(false), 300);
        }
    }, [checked]);

    return (
        <label style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '10px',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.5 : 1,
        }}>
            <div
                onClick={() => !disabled && onChange(!checked)}
                style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '6px',
                    border: `2px solid ${checked ? 'var(--cmd-green)' : 'var(--cmd-border)'}`,
                    backgroundColor: checked ? 'var(--cmd-green)' : 'transparent',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s ease',
                    transform: animate ? 'scale(1.1)' : 'scale(1)',
                }}
            >
                {checked && (
                    <CheckIcon style={{
                        width: '14px',
                        height: '14px',
                        color: '#fff',
                        animation: 'checkIn 0.2s ease-out',
                    }} />
                )}
            </div>

            {label && (
                <span style={{
                    fontSize: '14px',
                    color: 'var(--cmd-text)',
                    textDecoration: checked ? 'line-through' : 'none',
                    opacity: checked ? 0.7 : 1,
                    transition: 'all 0.2s',
                }}>
                    {label}
                </span>
            )}

            <style jsx>{`
        @keyframes checkIn {
          from { transform: scale(0); }
          to { transform: scale(1); }
        }
      `}</style>
        </label>
    );
}
