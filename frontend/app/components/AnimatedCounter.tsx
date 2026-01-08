'use client';

import { useState, useEffect, useRef } from 'react';

interface AnimatedCounterProps {
    value: number;
    duration?: number;
    prefix?: string;
    suffix?: string;
    decimals?: number;
    style?: React.CSSProperties;
}

export default function AnimatedCounter({
    value,
    duration = 500,
    prefix = '',
    suffix = '',
    decimals = 0,
    style = {},
}: AnimatedCounterProps) {
    const [displayValue, setDisplayValue] = useState(0);
    const displayValueRef = useRef(0);

    useEffect(() => {
        const startValue = displayValueRef.current;
        const startTime = performance.now();

        const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (ease-out)
            const eased = 1 - Math.pow(1 - progress, 3);

            const current = startValue + (value - startValue) * eased;
            setDisplayValue(current);
            displayValueRef.current = current;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }, [value, duration]);

    const formatted = decimals > 0
        ? displayValue.toFixed(decimals)
        : Math.round(displayValue).toLocaleString();

    return (
        <span style={{ fontVariantNumeric: 'tabular-nums', ...style }}>
            {prefix}{formatted}{suffix}
        </span>
    );
}
