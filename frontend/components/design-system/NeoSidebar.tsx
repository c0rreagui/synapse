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
    collapsed?: boolean;
    onToggle?: () => void;
}

export const NeoSidebar = React.forwardRef<HTMLDivElement, NeoSidebarProps>(
    ({ className, logo, collapsed = false, onToggle, ...props }, ref) => {
        const pathname = usePathname();

        return (
            <GlassPanel
                ref={ref}
                intensity="high"
                border={false}
                className={cnLocal(
                    "h-[95vh] flex flex-col p-4 fixed left-4 top-1/2 -translate-y-1/2 z-50 transition-all duration-300 ease-in-out",
                    collapsed ? "w-[80px]" : "w-[280px]",
                    className
                )}
                {...props}
            >
                {/* Header / Logo */}
                <div className={cnLocal(
                    "mb-8 py-4 border-b border-neo-border/50 flex items-center transition-all",
                    collapsed ? "justify-center px-0 gap-0" : "px-2 gap-3"
                )}>
                    <div className="w-8 h-8 rounded-lg bg-neo-primary shadow-[0_0_15px_rgba(139,92,246,0.5)] flex items-center justify-center text-white font-bold shrink-0">
                        S
                    </div>
                    <div className={cnLocal("flex flex-col overflow-hidden transition-all duration-300", collapsed ? "w-0 opacity-0 ml-0" : "w-auto opacity-100 ml-0")}>
                        <span className="text-white font-bold tracking-wider whitespace-nowrap">SYNAPSE</span>
                        <span className="text-[10px] text-neo-secondary uppercase tracking-[0.2em] whitespace-nowrap">Systems</span>
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
                                    "group flex items-center rounded-xl transition-all duration-300 relative",
                                    collapsed ? "justify-center px-0 py-3" : "gap-3 px-4 py-3",
                                    "hover:bg-white/5",
                                    isActive
                                        ? "bg-neo-primary/10 text-neo-primary shadow-[inset_0_0_20px_rgba(139,92,246,0.1)] border border-neo-primary/20"
                                        : "text-gray-400 hover:text-white border border-transparent"
                                )}
                                title={collapsed ? item.label : undefined}
                            >
                                <item.icon className={cnLocal(
                                    "w-5 h-5 transition-transform duration-300 group-hover:scale-110 shrink-0",
                                    isActive ? "drop-shadow-[0_0_8px_rgba(139,92,246,0.6)]" : ""
                                )} />

                                <span className={cnLocal(
                                    "font-medium tracking-wide whitespace-nowrap overflow-hidden transition-all duration-300",
                                    collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
                                )}>
                                    {item.label}
                                </span>


                            </Link>
                        )
                    })}
                </nav>

                {/* Status Footer */}
                <StatusFooter collapsed={collapsed} />

                {/* Toggle Button */}
                <button
                    onClick={onToggle}
                    className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-neo-border border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-neo-primary/20 transition-all z-50 shadow-lg"
                >
                    {collapsed ? (
                        <svg onClick={onToggle} xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6" /></svg>
                    ) : (
                        <svg onClick={onToggle} xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6" /></svg>
                    )}
                </button>
            </GlassPanel>
        );
    }
);

NeoSidebar.displayName = "NeoSidebar";

function StatusFooter({ collapsed }: { collapsed?: boolean }) {
    const { isConnected } = useWebSocketContext();

    return (
        <div className={cnLocal(
            "mt-auto bg-black/20 rounded-xl border border-white/5 transition-all duration-300",
            collapsed ? "px-0 py-3 bg-transparent border-0 flex justify-center" : "px-4 py-4"
        )}>
            <div className={cnLocal("flex items-center", collapsed ? "justify-center gap-0" : "gap-3")}>
                <div className="relative shrink-0">
                    <div className={clsx(
                        "w-2 h-2 rounded-full transition-colors duration-500",
                        isConnected ? "bg-emerald-500" : "bg-red-500"
                    )} />
                    <div className={clsx(
                        "absolute inset-0 w-2 h-2 rounded-full blur-sm transition-colors duration-500",
                        isConnected ? "bg-emerald-500 animate-pulse" : "bg-red-500 animate-none opacity-50"
                    )} />
                </div>
                <div className={cnLocal("flex flex-col whitespace-nowrap overflow-hidden transition-all duration-300", collapsed ? "w-0 opacity-0 ml-0" : "w-auto opacity-100")}>
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
