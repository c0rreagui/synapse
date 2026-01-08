'use client';

interface EmptyStateProps {
    icon?: React.ReactNode;
    title: string;
    description?: string;
    action?: {
        label: string;
        onClick: () => void;
    };
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
    return (
        <div
            style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '40px 20px',
                textAlign: 'center',
            }}
        >
            {icon && (
                <div style={{ marginBottom: '16px', opacity: 0.5 }}>
                    {icon}
                </div>
            )}
            <h4 style={{
                fontSize: '16px',
                fontWeight: 600,
                color: '#c9d1d9',
                margin: '0 0 8px'
            }}>
                {title}
            </h4>
            {description && (
                <p style={{
                    fontSize: '13px',
                    color: '#8b949e',
                    margin: '0 0 20px',
                    maxWidth: '280px',
                    lineHeight: 1.5,
                }}>
                    {description}
                </p>
            )}
            {action && (
                <button
                    onClick={action.onClick}
                    style={{
                        padding: '10px 20px',
                        fontSize: '13px',
                        fontWeight: 500,
                        color: '#fff',
                        backgroundColor: '#238636',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2ea043'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#238636'}
                >
                    {action.label}
                </button>
            )}
        </div>
    );
}
