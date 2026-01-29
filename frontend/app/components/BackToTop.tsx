'use client';

import { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

interface BackToTopProps {
    threshold?: number; // pixels before showing
    smooth?: boolean;
}

export default function BackToTop({ threshold = 300, smooth = true }: BackToTopProps) {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setIsVisible(window.scrollY > threshold);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [threshold]);

    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: smooth ? 'smooth' : 'auto',
        });
    };

    return (
        <button
            onClick={scrollToTop}
            style={{
                position: 'fixed',
                bottom: '24px',
                right: '24px',
                width: '44px',
                height: '44px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'var(--cmd-surface)',
                border: '1px solid var(--cmd-border)',
                borderRadius: '50%',
                color: 'var(--cmd-text)',
                cursor: 'pointer',
                boxShadow: 'var(--shadow-md)',
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
                pointerEvents: isVisible ? 'auto' : 'none',
                transition: 'all 0.3s ease',
                zIndex: 100,
            }}
            aria-label="Voltar ao topo"
            title="Voltar ao topo"
        >
            <ArrowUp style={{ width: '20px', height: '20px' }} />
        </button>
    );
}
