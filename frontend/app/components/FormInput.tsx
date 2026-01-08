'use client';

import { useState } from 'react';

interface FormInputProps {
    label: string;
    value: string;
    onChange: (value: string) => void;
    onBlur?: () => void;
    error?: string | null;
    placeholder?: string;
    type?: 'text' | 'email' | 'password' | 'number' | 'date' | 'time';
    required?: boolean;
    maxLength?: number;
    disabled?: boolean;
}

export default function FormInput({
    label,
    value,
    onChange,
    onBlur,
    error,
    placeholder,
    type = 'text',
    required = false,
    maxLength,
    disabled = false,
}: FormInputProps) {
    const [focused, setFocused] = useState(false);

    const hasError = error && error.length > 0;

    return (
        <div style={{ marginBottom: '16px' }}>
            <label style={{
                display: 'block',
                marginBottom: '6px',
                fontSize: '13px',
                fontWeight: 500,
                color: hasError ? '#f85149' : '#c9d1d9',
            }}>
                {label}
                {required && <span style={{ color: '#f85149', marginLeft: '4px' }}>*</span>}
            </label>

            <input
                type={type}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => { setFocused(false); onBlur?.(); }}
                placeholder={placeholder}
                maxLength={maxLength}
                disabled={disabled}
                style={{
                    width: '100%',
                    padding: '10px 14px',
                    fontSize: '14px',
                    color: '#c9d1d9',
                    backgroundColor: '#0d1117',
                    border: `1px solid ${hasError ? '#f85149' : focused ? '#58a6ff' : '#30363d'}`,
                    borderRadius: '8px',
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    boxShadow: focused ? `0 0 0 3px ${hasError ? 'rgba(248,81,73,0.15)' : 'rgba(88,166,255,0.15)'}` : 'none',
                    opacity: disabled ? 0.6 : 1,
                }}
            />

            {/* Error message with animation */}
            <div style={{
                height: hasError ? '20px' : '0',
                overflow: 'hidden',
                transition: 'height 0.2s ease',
            }}>
                {hasError && (
                    <p style={{
                        margin: '6px 0 0',
                        fontSize: '12px',
                        color: '#f85149',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                    }}>
                        <span>⚠</span> {error}
                    </p>
                )}
            </div>

            {/* Character counter */}
            {maxLength && (
                <div style={{
                    marginTop: '4px',
                    fontSize: '11px',
                    color: value.length > maxLength * 0.9 ? '#f0883e' : '#8b949e',
                    textAlign: 'right',
                }}>
                    {value.length}/{maxLength}
                </div>
            )}
        </div>
    );
}
