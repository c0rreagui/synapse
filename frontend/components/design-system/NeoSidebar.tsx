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
import { toast } from 'sonner';

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
        const [inactiveCount, setInactiveCount] = React.useState(0);
        const [firstInactiveId, setFirstInactiveId] = React.useState<string | null>(null);
        const [isRepairing, setIsRepairing] = React.useState(false);

        React.useEffect(() => {
            const checkProfileHealth = async () => {
                try {
                    const res = await fetch('http://localhost:8000/api/v1/profiles');
                    const data = await res.json();
                    // Detect profiles with errors: health_status error OR has error screenshot
                    const inactive = data.filter((p: any) =>
                        p.health_status === 'error' ||
                        p.health_status === 'expired' ||
                        p.last_error_screenshot
                    );
                    setInactiveCount(inactive.length);
                    if (inactive.length > 0) {
                        setFirstInactiveId(inactive[0].id);
                    } else {
                        setFirstInactiveId(null);
                    }
                } catch (e) {
                    console.error("Error checking profile health:", e);
                }
            };

            checkProfileHealth();
            const interval = setInterval(checkProfileHealth, 30000); // Check every 30s
            return () => clearInterval(interval);
        }, []);

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


                                {item.label === 'Perfis' && inactiveCount > 0 && (
                                    <span className={cnLocal(
                                        "absolute w-2 h-2 bg-red-500 rounded-full animate-pulse shadow-[0_0_5px_rgba(239,68,68,0.8)]",
                                        collapsed ? "top-2 right-2" : "top-3 left-8"
                                    )} title={`${inactiveCount} perfis precisam de login`} />
                                )}
                            </Link>
                        )
                    })}
                </nav>

                {/* Repair Button (Visible if issues exist) */}
                {inactiveCount > 0 && firstInactiveId && (
                    <div className={cnLocal(
                        "my-2 transition-all duration-300",
                        collapsed ? "px-0 flex justify-center" : "px-4"
                    )}>
                        <button
                            onClick={async () => {
                                if (!firstInactiveId || isRepairing) return;
                                setIsRepairing(true);

                                const toastId = toast.loading('Abrindo browser para reparo...');

                                try {
                                    const res = await fetch(`http://localhost:8000/api/v1/profiles/repair/${firstInactiveId}`, { method: 'POST' });
                                    if (res.ok) {
                                        toast.success('Browser aberto no servidor!', {
                                            id: toastId,
                                            description: 'Complete o login e feche o navegador.',
                                            duration: 8000
                                        });
                                    } else {
                                        const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
                                        toast.error('Erro ao abrir reparo', {
                                            id: toastId,
                                            description: err.detail || 'Perfil pode estar ocupado'
                                        });
                                    }
                                } catch (e) {
                                    toast.error('Erro de conexao', { id: toastId });
                                } finally {
                                    setIsRepairing(false);
                                }
                            }}
                            className={cnLocal(
                                "flex items-center gap-3 w-full rounded-xl border transition-all duration-300 group relative overflow-hidden",
                                isRepairing
                                    ? "bg-yellow-500/20 border-yellow-500/50 text-yellow-500"
                                    : "bg-red-500/10 border-red-500/30 hover:bg-red-500/20 text-red-400 hover:text-red-300",
                                collapsed ? "justify-center p-3" : "px-4 py-3"
                            )}
                            title={collapsed ? "Reparar Sessão" : undefined}
                        >
                            {isRepairing ? (
                                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin shrink-0" />
                            ) : (
                                <Activity className="w-5 h-5 shrink-0" /> // Using Activity as Wrench is not imported yet
                            )}

                            <span className={cnLocal(
                                "font-bold text-sm whitespace-nowrap overflow-hidden transition-all duration-300",
                                collapsed ? "w-0 opacity-0" : "w-auto opacity-100"
                            )}>
                                {isRepairing ? "Abrindo..." : "Reparar Sessão"}
                            </span>

                            {!collapsed && !isRepairing && (
                                <span className="absolute right-2 w-2 h-2 rounded-full bg-red-500 animate-ping" />
                            )}
                        </button>
                    </div>
                )}

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
    const [sonarStatus, setSonarStatus] = React.useState<'running' | 'offline' | 'stalled'>('offline');
    const [lastPulse, setLastPulse] = React.useState<string>('N/A');

    React.useEffect(() => {
        const checkStatus = async () => {
            // Check Sonar
            try {
                const res = await fetch('http://localhost:8000/api/health/sonar');
                const data = await res.json();
                setSonarStatus(data.status || 'offline');
                if (data.last_beat) {
                    const date = new Date(data.last_beat);
                    setLastPulse(date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
                }
            } catch (e) {
                setSonarStatus('offline');
            }
        };

        checkStatus();
        const interval = setInterval(checkStatus, 15000); // Check every 15s
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = () => {
        if (sonarStatus === 'running') return 'bg-emerald-500';
        if (sonarStatus === 'stalled') return 'bg-yellow-500';
        return 'bg-red-500';
    };

    const getStatusText = () => {
        if (sonarStatus === 'running') return 'System Online';
        if (sonarStatus === 'stalled') return 'System Stalled';
        return 'System Offline';
    };

    return (
        <div className={cnLocal(
            "mt-auto bg-black/20 rounded-xl border border-white/5 transition-all duration-300 group cursor-help",
            collapsed ? "px-0 py-3 bg-transparent border-0 flex justify-center" : "px-4 py-4"
        )}>
            {/* Tooltip for Detailed Status */}
            <div className="absolute bottom-full left-4 mb-2 w-48 bg-black/90 backdrop-blur-xl border border-white/10 rounded-lg p-3 shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none">
                <div className="text-xs font-bold text-white mb-1">
                    {sonarStatus === 'running' ? '🟢 SISTEMA ONLINE' : '🔴 SISTEMA OFFLINE'}
                </div>
                <div className="text-[10px] text-white/50 space-y-1">
                    <p>Scheduler: {sonarStatus.toUpperCase()}</p>
                    <p>Último Pulso: {lastPulse}</p>
                    <p>WS Connected: {isConnected ? 'YES' : 'NO'}</p>
                </div>
            </div>

            <div className={cnLocal("flex items-center", collapsed ? "justify-center gap-0" : "gap-3")}>
                {/* Radar Visual */}
                <div className="relative w-8 h-8 shrink-0 flex items-center justify-center">
                    <div className={cnLocal(
                        "radar-container w-full h-full scale-[0.8] transition-opacity duration-1000",
                        sonarStatus === 'running' ? "opacity-100" : "opacity-40 grayscale-[0.5]"
                    )}>
                        <div className="radar-rings">
                            <div className={cnLocal(
                                "radar-ring w-full h-full border-emerald-500/50",
                                sonarStatus === 'running' ? "opacity-30" : "opacity-10"
                            )} />
                            <div className={cnLocal(
                                "radar-ring w-[60%] h-[60%] border-emerald-500/30",
                                sonarStatus === 'running' ? "opacity-20" : "opacity-5"
                            )} />
                        </div>

                        {/* Conic Sweep Effect - Dimmed if offline */}
                        <div className={cnLocal(
                            "radar-sweep",
                            sonarStatus === 'running' ? "" : "opacity-30"
                        )} />

                        {/* Concentric Ping Waves - Only active if running or subtle if offline */}
                        <div className={cnLocal(
                            "ping-wave w-[20%] h-[20%]",
                            sonarStatus === 'running' ? "opacity-100" : "opacity-20"
                        )} />

                        <div className="radar-beam" />

                        {/* Status Dot at Center */}
                        <div className={cnLocal(
                            "absolute inset-0 m-auto w-1.5 h-1.5 rounded-full shadow-[0_0_8px_currentColor] transition-colors duration-500",
                            sonarStatus === 'running' ? "bg-emerald-400 text-emerald-400" :
                                sonarStatus === 'stalled' ? "bg-yellow-400 text-yellow-400" : "bg-red-400 text-red-400"
                        )} />
                    </div>
                </div>

                <div className={cnLocal("flex flex-col whitespace-nowrap overflow-hidden transition-all duration-300", collapsed ? "w-0 opacity-0 ml-0" : "w-auto opacity-100")}>
                    <span className={clsx(
                        "text-xs font-bold tracking-wider transition-colors duration-500",
                        sonarStatus === 'running' ? "text-emerald-400 text-glow-green" : "text-red-400"
                    )}>
                        {sonarStatus === 'running' ? 'SONAR ACTIVE' : getStatusText().toUpperCase()}
                    </span>
                    <span className="text-[9px] text-gray-500 font-mono">T-MINUS {lastPulse.split(':').pop()}s</span>
                </div>
            </div>
        </div>

    );
}
