'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Squares2X2Icon, UserGroupIcon, CubeTransparentIcon,
    DocumentTextIcon, ChartBarIcon, ClockIcon
} from '@heroicons/react/24/outline';

const navItems = [
    { href: '/', icon: Squares2X2Icon, label: 'Command Center' },
    { href: '/profiles', icon: UserGroupIcon, label: 'Perfis TikTok' },
    { href: '/factory', icon: CubeTransparentIcon, label: 'Factory Watcher' },
    { href: '/metrics', icon: ChartBarIcon, label: 'Métricas' },
    { href: '/logs', icon: DocumentTextIcon, label: 'Logs' },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside style={{ width: '256px', backgroundColor: 'var(--cmd-surface)', borderRight: '1px solid var(--cmd-border)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
            {/* Logo */}
            <div style={{ padding: '24px', borderBottom: '1px solid var(--cmd-border)' }}>
                <Link href="/" style={{ textDecoration: 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'var(--cmd-purple-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Squares2X2Icon style={{ width: '20px', height: '20px', color: 'var(--cmd-purple)' }} />
                        </div>
                        <div>
                            <h1 style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--cmd-text)', margin: 0, letterSpacing: '0.05em' }}>SYNAPSE</h1>
                            <p style={{ fontSize: '10px', color: 'var(--cmd-text-muted)', fontFamily: 'monospace', margin: 0, color: 'var(--cmd-purple)' }}>// CONTENT_AUTO</p>
                        </div>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <nav style={{ flex: 1, padding: '16px' }}>
                <p style={{ fontSize: '10px', color: 'var(--cmd-text-muted)', fontFamily: 'monospace', marginBottom: '12px', paddingLeft: '8px' }}>:: SYSTEM_MENU</p>
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link key={item.href} href={item.href} style={{ textDecoration: 'none' }}>
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: '12px',
                                padding: '10px 12px', borderRadius: '8px', marginBottom: '4px',
                                cursor: 'pointer',
                                backgroundColor: isActive ? 'var(--cmd-purple-bg)' : 'transparent',
                                color: isActive ? 'var(--cmd-purple)' : 'var(--cmd-text-muted)',
                                borderLeft: isActive ? '2px solid var(--cmd-purple)' : '2px solid transparent'
                            }}>
                                <item.icon style={{ width: '20px', height: '20px' }} />
                                <span style={{ fontSize: '14px' }}>{item.label}</span>
                            </div>
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div style={{ padding: '16px', borderTop: '1px solid var(--cmd-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--gradient-brand)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold', boxShadow: 'var(--shadow-glow-purple)' }}>S</div>
                    <div>
                        <p style={{ fontSize: '14px', color: '#fff', margin: 0 }}>Synapse Admin</p>
                        <p style={{ fontSize: '10px', color: '#8b949e', fontFamily: 'monospace', margin: 0 }}>v1.0.0</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
