"use client";

interface HeaderProps {
    title: string;
    subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
    return (
        <header className="flex items-center justify-between border-b border-white/5 bg-[#050507]/80 backdrop-blur-md px-8 py-4 z-40 sticky top-0">
            <div className="flex items-center gap-4">
                <h2 className="text-white text-xl font-bold leading-tight tracking-tight flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary shadow-primary drop-shadow-[0_0_10px_rgba(139,85,247,0.5)]">
                        space_dashboard
                    </span>
                    {title}
                </h2>
                {subtitle && (
                    <span className="text-xs font-mono text-primary/80 bg-primary/5 px-2 py-1 rounded border border-primary/20">
                        {subtitle}
                    </span>
                )}
            </div>

            <div className="flex items-center gap-6">
                {/* System Status */}
                <div className="flex items-center gap-3 bg-[#0a0a0e] border border-white/10 rounded-full pl-2 pr-4 py-1.5 shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)]">
                    <div className="relative flex items-center justify-center size-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                        <span className="relative inline-flex rounded-full size-2 bg-success shadow-[0_0_8px_#0bda6f]"></span>
                    </div>
                    <span className="text-[10px] font-mono text-success/80 tracking-wide uppercase neon-text">System Active</span>
                </div>

                <div className="h-5 w-px bg-white/10"></div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                    <button className="flex items-center justify-center size-9 rounded-full hover:bg-white/5 text-[#94a3b8] hover:text-white transition-colors relative group">
                        <span className="material-symbols-outlined text-[20px]">notifications</span>
                        <span className="absolute top-2 right-2.5 size-1.5 bg-primary rounded-full ring-2 ring-[#050507]"></span>
                        <div className="absolute inset-0 rounded-full border border-primary/30 scale-110 opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
                    </button>
                    <button className="flex items-center justify-center size-9 rounded-full hover:bg-white/5 text-[#94a3b8] hover:text-white transition-colors">
                        <span className="material-symbols-outlined text-[20px]">settings</span>
                    </button>
                </div>
            </div>
        </header>
    );
}
