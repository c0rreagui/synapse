'use client';

import { ReactNode, useRef, useEffect, useState } from 'react';

interface ParallaxProps {
    children: ReactNode;
    speed?: number; // 0.1 = slow, 0.5 = normal, 1 = fast
    direction?: 'up' | 'down';
}

export default function Parallax({
    children,
    speed = 0.3,
    direction = 'up',
}: ParallaxProps) {
    const ref = useRef<HTMLDivElement>(null);
    const [offset, setOffset] = useState(0);

    useEffect(() => {
        const handleScroll = () => {
            if (!ref.current) return;

            const rect = ref.current.getBoundingClientRect();
            const scrolled = window.innerHeight - rect.top;
            const parallax = scrolled * speed * (direction === 'up' ? -1 : 1);

            setOffset(parallax);
        };

        window.addEventListener('scroll', handleScroll);
        handleScroll();

        return () => window.removeEventListener('scroll', handleScroll);
    }, [speed, direction]);

    return (
        <div
            ref={ref}
            style={{
                transform: `translateY(${offset}px)`,
                willChange: 'transform',
            }}
        >
            {children}
        </div>
    );
}
