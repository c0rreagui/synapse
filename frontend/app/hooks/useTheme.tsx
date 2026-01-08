'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextType {
    theme: Theme;
    toggleTheme: () => void;
    setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setThemeState] = useState<Theme>('dark');

    const applyTheme = (t: Theme) => {
        if (typeof document !== 'undefined') {
            document.documentElement.setAttribute('data-theme', t);
        }
    };

    // Load from localStorage on mount - using useEffect correctly
    useEffect(() => {
        const saved = localStorage.getItem('synapse-theme') as Theme;
        if (saved) {
            setThemeState(saved);
            applyTheme(saved);
        }
    }, []);

    const setTheme = (t: Theme) => {
        setThemeState(t);
        localStorage.setItem('synapse-theme', t);
        applyTheme(t);
    };

    const toggleTheme = () => {
        setTheme(theme === 'dark' ? 'light' : 'dark');
    };

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('useTheme must be used within ThemeProvider');
    }
    return context;
}

// Theme toggle button component
export function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                borderRadius: '8px',
                backgroundColor: '#21262d',
                border: '1px solid #30363d',
                color: '#c9d1d9',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.2s',
            }}
            title={`Tema: ${theme === 'dark' ? 'Escuro' : 'Claro'}`}
        >
            {theme === 'dark' ? '🌙' : '☀️'}
            <span>{theme === 'dark' ? 'Escuro' : 'Claro'}</span>
        </button>
    );
}
