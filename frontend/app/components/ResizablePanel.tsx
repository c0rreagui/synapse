'use client';

import { useState, useRef, ReactNode, useEffect } from 'react';

interface ResizablePanelProps {
    left: ReactNode;
    right: ReactNode;
    defaultLeftWidth?: number; // percentage
    minLeftWidth?: number;
    maxLeftWidth?: number;
}

export default function ResizablePanel({
    left,
    right,
    defaultLeftWidth = 50,
    minLeftWidth = 20,
    maxLeftWidth = 80,
}: ResizablePanelProps) {
    const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
    const [isDragging, setIsDragging] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const handleMouseDown = () => {
        setIsDragging(true);
    };

    useEffect(() => {
        if (!isDragging) return;

        const handleMouseMove = (e: MouseEvent) => {
            if (!containerRef.current) return;

            const rect = containerRef.current.getBoundingClientRect();
            const newWidth = ((e.clientX - rect.left) / rect.width) * 100;

            setLeftWidth(Math.min(maxLeftWidth, Math.max(minLeftWidth, newWidth)));
        };

        const handleMouseUp = () => {
            setIsDragging(false);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, minLeftWidth, maxLeftWidth]);

    return (
        <div
            ref={containerRef}
            style={{
                display: 'flex',
                height: '100%',
                position: 'relative',
                userSelect: isDragging ? 'none' : 'auto',
            }}
        >
            {/* Left Panel */}
            <div style={{ width: `${leftWidth}%`, overflow: 'auto' }}>
                {left}
            </div>

            {/* Resize Handle */}
            <div
                onMouseDown={handleMouseDown}
                style={{
                    width: '6px',
                    cursor: 'col-resize',
                    backgroundColor: isDragging ? 'var(--cmd-blue)' : 'transparent',
                    transition: 'background-color 0.15s',
                    position: 'relative',
                    flexShrink: 0,
                }}
                onMouseEnter={(e) => !isDragging && (e.currentTarget.style.backgroundColor = 'var(--cmd-border)')}
                onMouseLeave={(e) => !isDragging && (e.currentTarget.style.backgroundColor = 'transparent')}
            >
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '2px',
                    height: '40px',
                    backgroundColor: 'var(--cmd-text-faint)',
                    borderRadius: '1px',
                }} />
            </div>

            {/* Right Panel */}
            <div style={{ flex: 1, overflow: 'auto' }}>
                {right}
            </div>
        </div>
    );
}
