import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { GlassPanel } from './GlassPanel';
// import { cn } from '@/services/utils'; // Removed unused import
import { LayoutDashboard, Radio, Search, Users, Settings, Activity, Calendar, FileText } from 'lucide-react';
// Import clsx/twMerge local if needed, but assuming global utils for now to match project pattern
// Wait, I used local utils in Atoms. I should stick to consistency.
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cnLocal(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

import { useWebSocketContext } from '../../app/context/WebSocketContext';

interface NavItem {
    icon: React.ElementType;
    label: string;
    href: string;
    active?: boolean;
}

const navItems = [
    { icon: LayoutDashboard, label: 'Comando', href: '/' },
    { icon: Users, label: 'Perfis', href: '/profiles' },
    { icon: Search, label: 'Oracle', href: '/oracle' },
    { icon: Activity, label: 'Factory', href: '/factory' },
    { icon: Calendar, label: 'Agenda', href: '/scheduler' },
    { icon: FileText, label: 'Logs', href: '/logs' },
    { icon: Settings, label: 'Config', href: '/settings' },
];

interface NeoSidebarProps extends React.HTMLAttributes<HTMLDivElement> {
    logo?: React.ReactNode;
}

export const NeoSidebar = React.forwardRef<HTMLDivElement, NeoSidebarProps>(
    ({ className, logo, ...props }, ref) => {
        const pathname = usePathname();

        return (
            <GlassPanel
                ref={ref}
                intensity="high"
                border={false} // Removed strong border as per user feedback ("as if focused")
                className={cnLocal("w-[280px] h-[95vh] flex flex-col p-4 fixed left-4 top-1/2 -translate-y-1/2 z-50", className)}
                {...props}
            >
                {/* Header / Logo Error */}
                <div className="mb-8 px-2 py-4 border-b border-neo-border/50 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-neo-primary shadow-[0_0_15px_rgba(139,92,246,0.5)] flex items-center justify-center text-white font-bold">
                        S
                    </div>
                    <div className="flex flex-col">
                        <span className="text-white font-bold tracking-wider">SYNAPSE</span>
                        <span className="text-[10px] text-neo-secondary uppercase tracking-[0.2em]">Systems</span>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-2">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={cnLocal(
                                    "group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300",
                                    "hover:bg-white/5",
                                    isActive
                                        ? "bg-neo-primary/10 text-neo-primary shadow-[inset_0_0_20px_rgba(139,92,246,0.1)] border border-neo-primary/20"
                                        : "text-gray-400 hover:text-white border border-transparent"
                                )}
                            >
                                <item.icon className={cnLocal(
                                    "w-5 h-5 transition-transform duration-300 group-hover:scale-110",
                                    isActive ? "drop-shadow-[0_0_8px_rgba(139,92,246,0.6)]" : ""
                                )} />
                                <span className="font-medium tracking-wide">{item.label}</span>

                                {isActive && (
                                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-neo-primary shadow-[0_0_10px_#8b5cf6]" />
                                )}
                            </Link>
                        )
                    })}
                </nav>

                {/* Footer / Status */}
                <StatusFooter />
            </GlassPanel>
        );
    }
);

NeoSidebar.displayName = "NeoSidebar";

// ⚡ Dynamic Component to avoid hydration mismatch if possible, or just standard hook usage

function StatusFooter() {
    const { isConnected } = useWebSocketContext();

    return (
        <div className="mt-auto px-4 py-4 bg-black/20 rounded-xl border border-white/5">
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className={clsx(
                        "w-2 h-2 rounded-full transition-colors duration-500",
                        isConnected ? "bg-emerald-500" : "bg-red-500"
                    )} />
                    <div className={clsx(
                        "absolute inset-0 w-2 h-2 rounded-full blur-sm transition-colors duration-500",
                        isConnected ? "bg-emerald-500 animate-pulse" : "bg-red-500 animate-none opacity-50"
                    )} />
                </div>
                <div className="flex flex-col">
                    <span className={clsx(
                        "text-xs font-medium transition-colors duration-500",
                        isConnected ? "text-white/80" : "text-red-400"
                    )}>
                        {isConnected ? "System Online" : "System Offline"}
                    </span>
                    <span className="text-[10px] text-gray-500">v2.1.0-NEO</span>
                </div>
            </div>
        </div>
    );
}
