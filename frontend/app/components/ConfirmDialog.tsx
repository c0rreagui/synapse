'use client';

import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: 'danger' | 'warning' | 'info';
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmDialog({
    isOpen,
    title,
    message,
    confirmLabel = 'Confirmar',
    cancelLabel = 'Cancelar',
    variant = 'danger',
    onConfirm,
    onCancel,
}: ConfirmDialogProps) {
    if (!isOpen) return null;

    const colors = {
        danger: { bg: '#da3633', hover: '#f85149' },
        warning: { bg: '#9e6a03', hover: '#f0883e' },
        info: { bg: '#1f6feb', hover: '#58a6ff' },
    };

    return (
        <div
            style={{
                position: 'fixed',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'rgba(0,0,0,0.7)',
                backdropFilter: 'blur(4px)',
                zIndex: 10000,
            }}
            onClick={onCancel}
        >
            <div
                style={{
                    width: '100%',
                    maxWidth: '400px',
                    backgroundColor: '#161b22',
                    borderRadius: '12px',
                    border: '1px solid #30363d',
                    boxShadow: '0 16px 48px rgba(0,0,0,0.5)',
                    animation: 'fadeIn 0.2s ease-out',
                }}
                onClick={(e) => e.stopPropagation()}
            >
                <style jsx>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
          }
        `}</style>

                {/* Header */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '16px 20px',
                    borderBottom: '1px solid #30363d',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <ExclamationTriangleIcon style={{
                            width: '20px',
                            height: '20px',
                            color: variant === 'danger' ? '#f85149' : variant === 'warning' ? '#f0883e' : '#58a6ff',
                        }} />
                        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#fff' }}>
                            {title}
                        </h3>
                    </div>
                    <button
                        onClick={onCancel}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}
                        aria-label="Fechar"
                        title="Fechar"
                    >
                        <XMarkIcon style={{ width: '20px', height: '20px', color: '#8b949e' }} />
                    </button>
                </div>

                {/* Body */}
                <div style={{ padding: '20px' }}>
                    <p style={{ margin: 0, fontSize: '14px', color: '#c9d1d9', lineHeight: 1.6 }}>
                        {message}
                    </p>
                </div>

                {/* Footer */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'flex-end',
                    gap: '12px',
                    padding: '16px 20px',
                    borderTop: '1px solid #30363d',
                }}>
                    <button
                        onClick={onCancel}
                        style={{
                            padding: '10px 16px',
                            fontSize: '13px',
                            fontWeight: 500,
                            color: '#c9d1d9',
                            backgroundColor: '#21262d',
                            border: '1px solid #30363d',
                            borderRadius: '6px',
                            cursor: 'pointer',
                        }}
                    >
                        {cancelLabel}
                    </button>
                    <button
                        onClick={onConfirm}
                        style={{
                            padding: '10px 16px',
                            fontSize: '13px',
                            fontWeight: 500,
                            color: '#fff',
                            backgroundColor: colors[variant].bg,
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                        }}
                    >
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}
