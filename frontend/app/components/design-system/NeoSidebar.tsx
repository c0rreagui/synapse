'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function NeoSidebar() {
    const pathname = usePathname() || '/';

    const getLinkClasses = (path: string) => {
        const isActive = pathname === path || (pathname.startsWith(path) && path !== '/');

        if (isActive) {
            return "group relative flex items-center justify-center w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_-3px_rgba(0,240,255,0.4)] border border-cyan-500/30";
        }

        return "group relative flex items-center justify-center w-12 h-12 rounded-xl text-slate-500 hover:text-white hover:bg-white/5 transition-all";
    };

    const navItems = [
        { path: '/', icon: 'rocket_launch', label: 'Central de Comando' },
        { path: '/factory', icon: 'network_node', label: 'Fábrica de Vídeos' },
        { path: '/clipper', icon: 'radar', label: 'Clipper Twitch' },
        { path: '/scheduler', icon: 'calendar_month', label: 'Grade Temporal' },
        { path: '/metrics', icon: 'analytics', label: 'Monitor de Telemetria' },
        { path: '/oracle', icon: 'public', label: 'Motor Oráculo' },
    ];

    return (
        <aside className="relative z-40 flex w-[80px] md:w-[100px] flex-col py-6 pl-4 h-full border-r border-white/5 bg-black/40 backdrop-blur-md">
            <div className="flex flex-col items-center gap-8 h-full">
                {/* Logo Pulse Effect */}
                <Link href="/" className="relative group cursor-pointer block">
                    <div className="absolute inset-0 bg-cyan-500/20 rounded-full blur-xl group-hover:blur-2xl transition-all duration-500 animate-pulse"></div>
                    <div className="relative w-12 h-12 flex items-center justify-center border border-cyan-500/30 rounded-full bg-black/60 shadow-[0_0_15px_rgba(0,240,255,0.2)]">
                        <span className="material-symbols-outlined text-cyan-400" style={{ fontSize: '24px' }}>blur_on</span>
                    </div>
                </Link>

                <nav className="flex flex-col gap-6 mt-8 w-full items-center">
                    {navItems.map((item) => {
                        const isActive = pathname === item.path || (pathname.startsWith(item.path) && item.path !== '/');
                        return (
                            <Link key={item.path} href={item.path} title={item.label} className={getLinkClasses(item.path)}>
                                <span className={`material-symbols-outlined ${!isActive ? 'group-hover:text-cyan-300 transition-colors' : ''}`}>
                                    {item.icon}
                                </span>
                                {isActive && (
                                    <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-cyan-400 rounded-l-full shadow-[0_0_10px_#00f0ff]"></div>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                <div className="mt-auto flex flex-col gap-4 items-center">
                    <div className="w-px h-12 bg-gradient-to-b from-transparent via-cyan-500/30 to-transparent"></div>
                    <Link href="/settings" title="Configuração do Sistema" className={`text-slate-500 hover:text-magenta-500 transition-colors relative group block ${pathname === '/settings' ? 'text-magenta-500 drop-shadow-[0_0_5px_rgba(255,0,255,0.5)]' : ''}`}>
                        <span className="material-symbols-outlined group-hover:rotate-90 transition-transform duration-500">settings</span>
                    </Link>
                </div>
            </div>
        </aside>
    );
}
