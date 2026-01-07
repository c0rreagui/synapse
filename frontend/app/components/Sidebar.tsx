'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Squares2X2Icon, UserGroupIcon, CubeTransparentIcon,
    DocumentTextIcon, ChartBarIcon
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
        <aside style={{ width: '256px', backgroundColor: '#161b22', borderRight: '1px solid #30363d', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
            {/* Logo */}
            <div style={{ padding: '24px', borderBottom: '1px solid #30363d' }}>
                <Link href="/" style={{ textDecoration: 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: 'rgba(63,185,80,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Squares2X2Icon style={{ width: '20px', height: '20px', color: '#3fb950' }} />
                        </div>
                        <div>
                            <h1 style={{ fontSize: '18px', fontWeight: 'bold', color: '#fff', margin: 0 }}>SYNAPSE</h1>
                            <p style={{ fontSize: '10px', color: '#8b949e', fontFamily: 'monospace', margin: 0 }}>CONTENT AUTOMATION</p>
                        </div>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <nav style={{ flex: 1, padding: '16px' }}>
                <p style={{ fontSize: '10px', color: '#8b949e', fontFamily: 'monospace', marginBottom: '12px', paddingLeft: '8px' }}>MENU</p>
                {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link key={item.href} href={item.href} style={{ textDecoration: 'none' }}>
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: '12px',
                                padding: '10px 12px', borderRadius: '8px', marginBottom: '4px',
                                cursor: 'pointer',
                                backgroundColor: isActive ? 'rgba(56,139,253,0.1)' : 'transparent',
                                color: isActive ? '#58a6ff' : '#8b949e'
                            }}>
                                <item.icon style={{ width: '20px', height: '20px' }} />
                                <span style={{ fontSize: '14px' }}>{item.label}</span>
                            </div>
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div style={{ padding: '16px', borderTop: '1px solid #30363d' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(135deg, #a371f7, #58a6ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 'bold' }}>S</div>
                    <div>
                        <p style={{ fontSize: '14px', color: '#fff', margin: 0 }}>Synapse Admin</p>
                        <p style={{ fontSize: '10px', color: '#8b949e', fontFamily: 'monospace', margin: 0 }}>v1.0.0</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
