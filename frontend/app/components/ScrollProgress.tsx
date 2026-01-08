'use client';

import { useState, useEffect } from 'react';

interface ScrollProgressProps {
    color?: string;
    height?: number;
    position?: 'top' | 'bottom';
}

export default function ScrollProgress({
    color = 'var(--cmd-blue)',
    height = 3,
    position = 'top',
}: ScrollProgressProps) {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const handleScroll = () => {
            const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrolled = (window.scrollY / scrollHeight) * 100;
            setProgress(Math.min(100, Math.max(0, scrolled)));
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <div
            style={{
                position: 'fixed',
                [position]: 0,
                left: 0,
                right: 0,
                height: height,
                backgroundColor: 'rgba(255,255,255,0.1)',
                zIndex: 9999,
            }}
        >
            <div
                style={{
                    width: `${progress}%`,
                    height: '100%',
                    backgroundColor: color,
                    transition: 'width 0.1s linear',
                }}
            />
        </div>
    );
}
