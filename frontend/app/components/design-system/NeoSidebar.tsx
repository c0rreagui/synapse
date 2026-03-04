'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function NeoSidebar() {
    const pathname = usePathname() || '/';
    const [collapsed, setCollapsed] = useState(true);

    // Persist collapse state
    useEffect(() => {
        const stored = localStorage.getItem('synapse-sidebar-collapsed');
        if (stored !== null) setCollapsed(stored === 'true');
    }, []);

    // Auto-collapse on narrow viewports (split-screen ~960px)
    useEffect(() => {
        const mq = window.matchMedia('(max-width: 1024px)');
        const handler = (e: MediaQueryListEvent | MediaQueryList) => {
            if (e.matches) setCollapsed(true);
        };
        handler(mq);
        mq.addEventListener('change', handler);
        return () => mq.removeEventListener('change', handler);
    }, []);

    const toggle = () => {
        const next = !collapsed;
        setCollapsed(next);
        localStorage.setItem('synapse-sidebar-collapsed', String(next));
    };

    const navItems = [
        { path: '/', icon: 'rocket_launch', label: 'Central' },
        { path: '/factory', icon: 'network_node', label: 'Fábrica' },
        { path: '/clipper', icon: 'radar', label: 'Clipper' },
        { path: '/profiles', icon: 'groups', label: 'Perfis' },
        { path: '/scheduler', icon: 'calendar_month', label: 'Grade' },
        { path: '/metrics', icon: 'analytics', label: 'Telemetria' },
        { path: '/oracle', icon: 'public', label: 'Oráculo' },
    ];

    return (
        <aside
            className={`relative z-40 flex flex-col py-6 h-full border-r border-white/5 bg-black/40 backdrop-blur-md transition-all duration-300 ease-out ${collapsed ? 'w-[72px]' : 'w-[200px]'
                }`}
        >
            <div className="flex flex-col items-center gap-6 h-full px-3">
                {/* Logo */}
                <Link href="/" className="relative group cursor-pointer block shrink-0">
                    <div className="absolute inset-0 bg-cyan-500/20 rounded-full blur-xl group-hover:blur-2xl transition-all duration-500 animate-pulse"></div>
                    <div className="relative w-11 h-11 flex items-center justify-center border border-cyan-500/30 rounded-full bg-black/60 shadow-[0_0_15px_rgba(0,240,255,0.2)]">
                        <span className="material-symbols-outlined text-cyan-400" style={{ fontSize: '22px' }}>blur_on</span>
                    </div>
                </Link>

                {/* Toggle Button */}
                <button
                    onClick={toggle}
                    className="w-full flex items-center justify-center gap-2 py-1.5 rounded-lg text-slate-500 hover:text-cyan-400 hover:bg-white/5 transition-all text-xs shrink-0"
                    title={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
                >
                    <span className={`material-symbols-outlined text-[18px] transition-transform duration-300 ${collapsed ? '' : 'rotate-180'}`}>
                        chevron_right
                    </span>
                    {!collapsed && <span className="font-mono text-[10px] tracking-widest uppercase">Colapsar</span>}
                </button>

                {/* Divider */}
                <div className="w-8 h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent"></div>

                {/* Navigation */}
                <nav className="flex flex-col gap-2 w-full">
                    {navItems.map((item) => {
                        const isActive = pathname === item.path || (pathname.startsWith(item.path) && item.path !== '/');
                        return (
                            <Link
                                key={item.path}
                                href={item.path}
                                title={item.label}
                                className={`group relative flex items-center gap-3 rounded-xl transition-all duration-200 ${collapsed ? 'justify-center w-11 h-11 mx-auto' : 'px-3 h-11'
                                    } ${isActive
                                        ? 'bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_-3px_rgba(0,240,255,0.4)] border border-cyan-500/30'
                                        : 'text-slate-500 hover:text-white hover:bg-white/5 border border-transparent'
                                    }`}
                            >
                                <span className={`material-symbols-outlined shrink-0 ${!isActive ? 'group-hover:text-cyan-300 transition-colors' : ''}`} style={{ fontSize: '22px' }}>
                                    {item.icon}
                                </span>
                                {!collapsed && (
                                    <span className="text-xs font-bold tracking-wider uppercase whitespace-nowrap overflow-hidden">
                                        {item.label}
                                    </span>
                                )}
                                {isActive && (
                                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-cyan-400 rounded-l-full shadow-[0_0_10px_#00f0ff]"></div>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                {/* Bottom Section */}
                <div className="mt-auto flex flex-col gap-4 items-center">
                    <div className="w-px h-12 bg-gradient-to-b from-transparent via-cyan-500/30 to-transparent"></div>
                    <Link
                        href="/settings"
                        title="Configuração do Sistema"
                        className={`relative group block transition-colors ${pathname === '/settings'
                                ? 'text-magenta-500 drop-shadow-[0_0_5px_rgba(255,0,255,0.5)]'
                                : 'text-slate-500 hover:text-magenta-500'
                            }`}
                    >
                        <span className="material-symbols-outlined group-hover:rotate-90 transition-transform duration-500">settings</span>
                    </Link>
                </div>
            </div>
        </aside>
    );
}
