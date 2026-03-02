import React from 'react';

export function NeoHeader({ title = "Comando Celestial Pro" }: { title?: string }) {
    return (
        <header className="h-20 flex items-center justify-between px-8 border-b border-white/5 bg-black/10 backdrop-blur-sm z-30 relative shrink-0">
            {/* Top Scanning Line */}
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent">
                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-cyan-400 to-transparent w-[100px] animate-pulse-transmission"></div>
            </div>

            <div className="flex items-center gap-4">
                <h1 className="text-2xl font-display font-bold md:tracking-widest text-white uppercase flex items-center gap-3">
                    <span className="text-cyan-400 animate-pulse">///</span>
                    <span className="chromatic-text" data-text={title}>{title}</span>
                </h1>
                <div className="h-4 w-px bg-white/10 mx-2 hidden md:block"></div>
                <div className="hidden md:flex items-center gap-2 text-xs font-mono text-cyan-500/70">
                    <span className="animate-pulse text-red-500">●</span> AO VIVO
                    <span className="text-slate-600">::</span>
                    <span className="text-cyan-300">SETOR 7G</span>
                </div>
            </div>

            <div className="flex items-center gap-8">
                {/* Status Stats */}
                <div className="hidden lg:flex items-center gap-6 font-mono text-xs">
                    <div className="flex flex-col items-end group cursor-help">
                        <span className="text-slate-500 uppercase tracking-wider text-[9px] mb-1">Latência da Rede</span>
                        <span className="text-cyan-300 drop-shadow-[0_0_5px_rgba(0,240,255,0.5)]">12ms <span className="text-slate-600">estável</span></span>
                    </div>
                    <div className="flex flex-col items-end group cursor-help">
                        <span className="text-slate-500 uppercase tracking-wider text-[9px] mb-1">Temp. do Núcleo</span>
                        <span className="text-magenta-500 drop-shadow-[0_0_5px_rgba(255,0,85,0.5)]">342<span className="text-slate-600">K</span></span>
                    </div>
                </div>

                {/* Profile Avatar Glow */}
                <div className="relative w-10 h-10 rounded-full border border-white/10 flex items-center justify-center bg-white/5 overflow-hidden group cursor-pointer">
                    <div
                        className="absolute inset-0 bg-cover bg-center opacity-80 group-hover:opacity-100 transition-opacity"
                        style={{
                            backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuC3dZzME1UkKgHlqGy8F7oKyiroaA1oXyJ1TSzXREb0j3l7iVnF-CBYoUi8OEmJM73xzjzhEjt4MfZVUICKp1k-flKFONFIMsUo-4wpFt6lic8oTmk9hFjFS0WMdymikpISFhqSBUqPIekdeiyqAqr59cwl_fFYSd6Lm1IQMICQ8hXg55uCHAqtvpTkuBFMabPWanRR2_JNnVX9UHsbCVAujoTZfsybxWV_lfjshzHrBf9Cw8PFONcjpXtC13kI4uMuLUMKNNMkIO0')",
                            filter: "saturate(0) contrast(1.2)",
                            mixBlendMode: "luminosity"
                        }}
                    ></div>
                    <div className="absolute inset-0 border border-cyan-500/0 group-hover:border-cyan-500/50 rounded-full transition-all duration-300 shadow-[0_0_10px_rgba(0,240,255,0.2)]"></div>
                </div>
            </div>
        </header>
    );
}
