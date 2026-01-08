'use client';

interface SkeletonProps {
    width?: string | number;
    height?: string | number;
    borderRadius?: number;
    style?: React.CSSProperties;
}

export default function Skeleton({
    width = '100%',
    height = 20,
    borderRadius = 6,
    style = {},
}: SkeletonProps) {
    return (
        <div
            style={{
                width,
                height,
                borderRadius,
                backgroundColor: '#30363d',
                background: 'linear-gradient(90deg, #30363d 0%, #3d444d 50%, #30363d 100%)',
                backgroundSize: '200% 100%',
                animation: 'shimmer 1.5s ease-in-out infinite',
                ...style,
            }}
        >
            <style jsx>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
        </div>
    );
}

// Card skeleton preset
export function CardSkeleton() {
    return (
        <div style={{
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: '#1c2128',
            border: '1px solid #30363d'
        }}>
            <Skeleton height={20} width="60%" style={{ marginBottom: 12 }} />
            <Skeleton height={14} width="90%" style={{ marginBottom: 8 }} />
            <Skeleton height={14} width="75%" />
        </div>
    );
}

// List item skeleton preset
export function ListItemSkeleton() {
    return (
        <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '10px',
            borderRadius: '8px',
            backgroundColor: '#161b22',
        }}>
            <Skeleton width={32} height={32} borderRadius={16} />
            <div style={{ flex: 1 }}>
                <Skeleton height={14} width="70%" style={{ marginBottom: 6 }} />
                <Skeleton height={10} width="40%" />
            </div>
        </div>
    );
}
