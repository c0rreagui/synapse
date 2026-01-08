'use client';

interface PasswordStrengthProps {
    password: string;
    showLabel?: boolean;
}

export default function PasswordStrength({ password, showLabel = true }: PasswordStrengthProps) {
    const getStrength = (pwd: string): { level: number; label: string; color: string } => {
        if (!pwd) return { level: 0, label: '', color: 'transparent' };

        let score = 0;

        // Length checks
        if (pwd.length >= 8) score += 1;
        if (pwd.length >= 12) score += 1;
        if (pwd.length >= 16) score += 1;

        // Character variety
        if (/[a-z]/.test(pwd)) score += 1;
        if (/[A-Z]/.test(pwd)) score += 1;
        if (/[0-9]/.test(pwd)) score += 1;
        if (/[^a-zA-Z0-9]/.test(pwd)) score += 1;

        // Common patterns (negative)
        if (/^[a-z]+$/i.test(pwd)) score -= 1;
        if (/^[0-9]+$/.test(pwd)) score -= 1;

        if (score <= 2) return { level: 1, label: 'Fraca', color: 'var(--cmd-red)' };
        if (score <= 4) return { level: 2, label: 'Média', color: 'var(--cmd-yellow)' };
        if (score <= 5) return { level: 3, label: 'Boa', color: 'var(--cmd-blue)' };
        return { level: 4, label: 'Forte', color: 'var(--cmd-green)' };
    };

    const { level, label, color } = getStrength(password);

    if (!password) return null;

    return (
        <div style={{ marginTop: '8px' }}>
            <div style={{ display: 'flex', gap: '4px', marginBottom: '4px' }}>
                {[1, 2, 3, 4].map(i => (
                    <div
                        key={i}
                        style={{
                            flex: 1,
                            height: '4px',
                            borderRadius: '2px',
                            backgroundColor: i <= level ? color : 'rgba(255,255,255,0.1)',
                            transition: 'background-color 0.2s',
                        }}
                    />
                ))}
            </div>
            {showLabel && label && (
                <span style={{ fontSize: '11px', color }}>
                    Senha {label}
                </span>
            )}
        </div>
    );
}
