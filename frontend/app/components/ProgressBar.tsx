'use client';



interface ProgressBarProps {
    progress: number; // 0-100
    showPercent?: boolean;
    color?: string;
    height?: number;
    animated?: boolean;
}

export default function ProgressBar({
    progress,
    showPercent = true,
    color = '#3fb950',
    height = 8,
    animated = true,
}: ProgressBarProps) {
    // Simplified: CSS transition handles the animation smoothly
    const displayProgress = progress;

    return (
        <div style={{ width: '100%' }}>
            <div
                style={{
                    width: '100%',
                    height: height,
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    borderRadius: height / 2,
                    overflow: 'hidden',
                }}
            >
                <div
                    style={{
                        width: `${Math.min(100, Math.max(0, displayProgress))}%`,
                        height: '100%',
                        backgroundColor: color,
                        borderRadius: height / 2,
                        transition: animated ? 'width 0.3s ease-out' : 'none',
                        background: `linear-gradient(90deg, ${color}, ${color}dd)`,
                    }}
                />
            </div>
            {showPercent && (
                <div style={{
                    marginTop: '6px',
                    fontSize: '11px',
                    color: '#8b949e',
                    textAlign: 'right',
                    fontFamily: 'monospace',
                }}>
                    {Math.round(displayProgress)}%
                </div>
            )}
        </div>
    );
}
