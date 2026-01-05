"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
    icon: string;
    label: string;
    href: string;
}

const mainNavItems: NavItem[] = [
    { icon: "dashboard", label: "Command Center", href: "/" },
    { icon: "folder_open", label: "Dark Profiles", href: "/profiles" },
    { icon: "show_chart", label: "Growth Metrics", href: "/metrics" },
];

const neuralNavItems: NavItem[] = [
    { icon: "hub", label: "Node Matrix", href: "/distribution" },
    { icon: "settings_input_component", label: "Integrations", href: "/settings" },
];

export default function Sidebar() {
    const pathname = usePathname();

    const isActive = (href: string) => {
        if (href === "/") return pathname === "/";
        return pathname.startsWith(href);
    };

    return (
        <aside className="hidden md:flex flex-col w-20 lg:w-72 border-r border-white/5 bg-[#050507]/60 backdrop-blur-2xl p-4 justify-between h-full relative z-50 transition-all">
            <div className="flex flex-col gap-8">
                {/* Logo */}
                <div className="flex items-center gap-3 px-2 py-2">
                    <div className="size-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-[0_0_20px_rgba(139,85,247,0.4)] relative overflow-hidden group">
                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                        <span className="material-symbols-outlined text-white text-[24px]">neurology</span>
                    </div>
                    <div className="hidden lg:block">
                        <h1 className="text-white text-lg font-bold tracking-tight font-display">SYNAPSE</h1>
                        <p className="text-primary/60 text-[10px] font-mono tracking-[0.2em]">ORCHESTRATOR_V4</p>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex flex-col gap-1.5">
                    <p className="px-4 text-[10px] font-bold text-[#475569] uppercase tracking-wider mb-2 font-mono hidden lg:block">Operations</p>

                    {mainNavItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg group relative overflow-hidden transition-colors ${isActive(item.href)
                                ? "nav-item-active text-white"
                                : "text-[#94a3b8] hover:text-white hover:bg-white/5"
                                }`}
                        >
                            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            <span
                                className={`material-symbols-outlined text-[20px] ${isActive(item.href)
                                    ? "text-primary drop-shadow-[0_0_8px_rgba(139,85,247,0.8)]"
                                    : "group-hover:text-primary transition-colors"
                                    }`}
                            >
                                {item.icon}
                            </span>
                            <span className="text-sm font-medium tracking-wide hidden lg:block">{item.label}</span>
                        </Link>
                    ))}

                    <p className="px-4 text-[10px] font-bold text-[#475569] uppercase tracking-wider mb-2 mt-6 font-mono hidden lg:block">Neural Net</p>

                    {neuralNavItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg group relative overflow-hidden transition-colors ${isActive(item.href)
                                ? "nav-item-active text-white"
                                : "text-[#94a3b8] hover:text-white hover:bg-white/5"
                                }`}
                        >
                            <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            <span
                                className={`material-symbols-outlined text-[20px] ${isActive(item.href)
                                    ? "text-primary drop-shadow-[0_0_8px_rgba(139,85,247,0.8)]"
                                    : "group-hover:text-primary transition-colors"
                                    }`}
                            >
                                {item.icon}
                            </span>
                            <span className="text-sm font-medium tracking-wide hidden lg:block">{item.label}</span>
                        </Link>
                    ))}
                </nav>
            </div>

            {/* User Profile Card */}
            <div className="glass-panel rounded-xl p-3 flex items-center gap-3 border border-white/5 hover:border-primary/30 transition-all cursor-pointer group">
                <div
                    className="bg-center bg-no-repeat aspect-square bg-cover rounded-lg size-9 ring-1 ring-white/10 group-hover:ring-primary/50 transition-all avatar-admin"
                ></div>
                <div className="flex flex-col min-w-0 hidden lg:block">
                    <p className="text-sm font-medium text-white truncate group-hover:text-primary transition-colors">Administrator</p>
                    <p className="text-[10px] font-mono text-[#64748b] truncate">SYS_ADMIN_01</p>
                </div>
                <span className="material-symbols-outlined text-[#64748b] ml-auto text-lg group-hover:text-white transition-colors hidden lg:block">more_vert</span>
            </div>
        </aside>
    );
}
