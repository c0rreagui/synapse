'use client';

import { useState, useRef, useEffect } from 'react';

interface AutocompleteProps {
    value: string;
    onChange: (value: string) => void;
    suggestions: string[];
    placeholder?: string;
    label?: string;
}

export default function Autocomplete({
    value,
    onChange,
    suggestions,
    placeholder,
    label,
}: AutocompleteProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [filtered, setFiltered] = useState<string[]>([]);
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (value) {
            const matches = suggestions.filter(s =>
                s.toLowerCase().includes(value.toLowerCase()) && s.toLowerCase() !== value.toLowerCase()
            );
            setFiltered(matches.slice(0, 8));
            setIsOpen(matches.length > 0);
        } else {
            setFiltered([]);
            setIsOpen(false);
        }
        setSelectedIndex(-1);
    }, [value, suggestions]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isOpen) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => Math.min(prev + 1, filtered.length - 1));
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => Math.max(prev - 1, -1));
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && filtered[selectedIndex]) {
                    onChange(filtered[selectedIndex]);
                    setIsOpen(false);
                }
                break;
            case 'Escape':
                setIsOpen(false);
                break;
        }
    };

    return (
        <div style={{ position: 'relative' }}>
            {label && (
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', color: 'var(--cmd-text)' }}>
                    {label}
                </label>
            )}

            <input
                ref={inputRef}
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => filtered.length > 0 && setIsOpen(true)}
                onBlur={() => setTimeout(() => setIsOpen(false), 150)}
                placeholder={placeholder}
                style={{
                    width: '100%',
                    padding: '10px 14px',
                    fontSize: '14px',
                    color: 'var(--cmd-text)',
                    backgroundColor: 'var(--cmd-bg)',
                    border: '1px solid var(--cmd-border)',
                    borderRadius: 'var(--radius-md)',
                    outline: 'none',
                }}
            />

            {isOpen && filtered.length > 0 && (
                <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    marginTop: '4px',
                    backgroundColor: 'var(--cmd-surface)',
                    border: '1px solid var(--cmd-border)',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: 'var(--shadow-md)',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    zIndex: 100,
                }}>
                    {filtered.map((item, i) => (
                        <div
                            key={item}
                            onClick={() => { onChange(item); setIsOpen(false); }}
                            style={{
                                padding: '10px 14px',
                                fontSize: '13px',
                                color: 'var(--cmd-text)',
                                backgroundColor: i === selectedIndex ? 'var(--cmd-card)' : 'transparent',
                                cursor: 'pointer',
                            }}
                            onMouseEnter={() => setSelectedIndex(i)}
                        >
                            {item}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
