'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Squares2X2Icon, UserGroupIcon, CubeTransparentIcon,
    DocumentTextIcon, ChartBarIcon, CalendarIcon
} from '@heroicons/react/24/outline';
import clsx from 'clsx';

const navItems = [
    { href: '/', icon: Squares2X2Icon, label: 'Central de Comando' },
    { href: '/profiles', icon: UserGroupIcon, label: 'Perfis TikTok' },
    { href: '/oracle', icon: CubeTransparentIcon, label: 'Oracle Intelligence' },
    { href: '/factory', icon: CubeTransparentIcon, label: 'Factory Watcher' },
    { href: '/scheduler', icon: CalendarIcon, label: 'Agendamento' },
    { href: '/analytics', icon: ChartBarIcon, label: 'Deep Analytics' },
    { href: '/logs', icon: DocumentTextIcon, label: 'Logs' },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="w-64 h-screen bg-[#0f0a15] border-r border-[#1f1a25] flex flex-col shrink-0 sticky top-0">
            {/* Logo */}
            <div className="p-6 border-b border-[#1f1a25]">
                <Link href="/" className="no-underline group">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-synapse-primary/10 flex items-center justify-center group-hover:bg-synapse-primary/20 transition-colors border border-synapse-primary/30 group-hover:border-synapse-primary hover:shadow-[0_0_15px_rgba(139,92,246,0.5)] shadow-[0_0_10px_rgba(139,92,246,0.1)]">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-synapse-primary drop-shadow-[0_0_5px_rgba(139,92,246,0.5)]">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-white m-0 tracking-wider font-mono">SYNAPSE</h1>
                            <p className="text-[10px] text-synapse-primary font-mono m-0 opacity-80 group-hover:opacity-100">// CONTENT_AUTO</p>
                        </div>
                    </div>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 overflow-y-auto">
                <p className="text-[10px] text-gray-500 font-mono mb-3 pl-2 tracking-widest uppercase">:: System_Menu</p>
                <div className="space-y-1">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link key={item.href} href={item.href} className="block no-underline">
                                <div className={clsx(
                                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group relative overflow-hidden",
                                    isActive
                                        ? "bg-synapse-primary/20 text-synapse-primary border-l-2 border-synapse-primary shadow-[0_0_15px_rgba(139,92,246,0.15)]"
                                        : "text-gray-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent hover:shadow-[0_0_10px_rgba(255,255,255,0.05)]"
                                )}>
                                    {isActive && (
                                        <div className="absolute inset-0 bg-synapse-primary/5 animate-pulse pointer-events-none" />
                                    )}
                                    <item.icon className={clsx("w-5 h-5 transition-colors", isActive ? "text-synapse-primary drop-shadow-[0_0_8px_rgba(139,92,246,0.6)]" : "text-synapse-primary/50 group-hover:text-white")} />
                                    <span className="relative z-10 font-medium">{item.label}</span>
                                </div>
                            </Link>
                        );
                    })}
                </div>
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-[#1f1a25]">
                <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-synapse-primary to-synapse-secondary flex items-center justify-center text-white font-bold shadow-lg shadow-purple-500/20">
                        S
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white m-0">Synapse Admin</p>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-synapse-emerald animate-pulse"></div>
                            <p className="text-[10px] text-gray-400 font-mono m-0">v1.2.0-STITCH</p>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    );
}
