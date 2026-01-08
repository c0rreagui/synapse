'use client';

import { useState, useRef, useEffect, ReactNode } from 'react';

interface LazyImageProps {
    src: string;
    alt: string;
    width?: number | string;
    height?: number | string;
    placeholder?: ReactNode;
    className?: string;
    style?: React.CSSProperties;
}

export default function LazyImage({
    src,
    alt,
    width,
    height,
    placeholder,
    className,
    style,
}: LazyImageProps) {
    const [isLoaded, setIsLoaded] = useState(false);
    const [isInView, setIsInView] = useState(false);
    const imgRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsInView(true);
                    observer.disconnect();
                }
            },
            { rootMargin: '100px' }
        );

        if (imgRef.current) {
            observer.observe(imgRef.current);
        }

        return () => observer.disconnect();
    }, []);

    return (
        <div
            ref={imgRef}
            className={className}
            style={{
                position: 'relative',
                width,
                height,
                overflow: 'hidden',
                backgroundColor: 'var(--cmd-surface)',
                borderRadius: 'var(--radius-md)',
                ...style,
            }}
        >
            {!isLoaded && (
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'var(--cmd-surface)',
                }}>
                    {placeholder || (
                        <div style={{
                            width: '32px',
                            height: '32px',
                            border: '2px solid var(--cmd-border)',
                            borderTopColor: 'var(--cmd-blue)',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite',
                        }} />
                    )}
                </div>
            )}

            {isInView && (
                <img
                    src={src}
                    alt={alt}
                    onLoad={() => setIsLoaded(true)}
                    style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        opacity: isLoaded ? 1 : 0,
                        transition: 'opacity 0.3s ease',
                    }}
                />
            )}

            <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}
