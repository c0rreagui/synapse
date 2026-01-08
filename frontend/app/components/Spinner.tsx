'use client';

interface SpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    color?: string;
}

export default function Spinner({ size = 'md', color = '#58a6ff' }: SpinnerProps) {
    const sizes = {
        sm: 16,
        md: 24,
        lg: 36,
    };

    const dim = sizes[size];

    return (
        <div
            style={{
                width: dim,
                height: dim,
                border: `2px solid ${color}20`,
                borderTopColor: color,
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
            }}
        >
            <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}
