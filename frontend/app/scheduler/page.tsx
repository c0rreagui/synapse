'use client';

import React from 'react';

export default function SchedulerPage() {
    return (
        <div className="flex-1 flex flex-col relative overflow-hidden bg-background-dark text-slate-100 min-h-screen selection:bg-primary/30 w-full">
            <div className="parallax-bg"></div>

            <main className="flex-1 flex flex-col relative overflow-hidden w-full h-full max-w-[1600px] mx-auto">
                <div className="px-8 py-6 flex flex-wrap gap-4 items-end justify-between z-30 relative pointer-events-none mt-4">
                    <div className="pointer-events-auto">
                        <div className="flex items-center gap-2 text-xs font-mono text-cyan-400/60 mb-2 tech-stencil">
                            <span className="material-symbols-outlined text-[14px]">history</span>
                            <span>Operações Temporais</span>
                            <span className="text-slate-600">/</span>
                            <span className="text-white font-bold">Visão em Grade</span>
                        </div>
                        <h1 className="text-5xl font-bold text-white tracking-tight flex items-center gap-4 font-display">
                            OUTUBRO <span className="text-slate-600 font-light">2023</span>
                            <div className="flex items-center gap-2 px-2 py-1 bg-cyan-400/10 border border-cyan-400/30 rounded-none backdrop-blur-sm">
                                <span className="size-1.5 bg-cyan-400 rounded-full animate-pulse-slow"></span>
                                <span className="text-[10px] font-mono font-bold text-cyan-400 tracking-widest">AO VIVO</span>
                            </div>
                        </h1>
                    </div>

                    <div className="flex items-center gap-2 bg-black/60 p-1 border border-white/10 backdrop-blur-md shadow-2xl pointer-events-auto">
                        <button className="size-8 flex items-center justify-center hover:bg-white/5 border border-transparent hover:border-white/10 text-slate-300 transition-all">
                            <span className="material-symbols-outlined text-[18px]">chevron_left</span>
                        </button>
                        <button className="px-4 h-8 flex items-center justify-center bg-cyan-400/20 border border-cyan-400/50 text-cyan-400 font-bold text-[10px] tech-stencil hover:bg-cyan-400/30 transition-all shadow-[0_0_15px_rgba(7,182,213,0.15)]">
                            Presente
                        </button>
                        <button className="size-8 flex items-center justify-center hover:bg-white/5 border border-transparent hover:border-white/10 text-slate-300 transition-all">
                            <span className="material-symbols-outlined text-[18px]">chevron_right</span>
                        </button>
                        <div className="w-px h-4 bg-white/10 mx-2"></div>
                        <div className="flex">
                            <button className="px-3 h-8 text-[10px] font-bold tech-stencil text-white bg-white/10 border border-white/10">Mês</button>
                            <button className="px-3 h-8 text-[10px] font-bold tech-stencil text-slate-500 hover:text-white border-y border-r border-white/10 hover:bg-white/5 transition-colors">Semana</button>
                        </div>
                    </div>
                </div>

                <div className="flex-1 px-8 pb-8 overflow-hidden flex gap-8 perspective-container relative z-10">
                    {/* Grid Section */}
                    <div className="flex-1 relative">
                        <div className="tilted-grid w-full h-full flex flex-col pt-8">
                            <div className="grid grid-cols-7 mb-2 transform-style-3d">
                                {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map((day, i) => (
                                    <div key={day} className={`text-center text-[10px] font-bold ${i < 5 ? 'text-cyan-400/60 border-cyan-400/20' : 'text-slate-600 border-slate-800'} tech-stencil pb-2 border-b`}>
                                        {day}
                                    </div>
                                ))}
                            </div>

                            <div className="flex-1 grid grid-cols-7 grid-rows-5 gap-3 pb-12">
                                {/* Dummy Grid Filler */}
                                {Array.from({ length: 5 }).map((_, i) => (
                                    <div key={`prev-${i}`} className="grid-cell bg-[#0c1618]/40 border border-white/5 relative p-2">
                                        <span className="text-slate-700 font-mono text-xs">{25 + i}</span>
                                    </div>
                                ))}
                                <div className="grid-cell bg-[#060b0c]/20 border border-white/5 relative p-2">
                                    <span className="text-slate-700 font-mono text-xs">30</span>
                                </div>
                                <div className="grid-cell bg-[#060b0c]/20 border border-white/5 relative p-2">
                                    <span className="text-slate-600 font-mono text-xs">01</span>
                                </div>

                                <div className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                    <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">02</span>
                                </div>
                                <div className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                    <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">03</span>
                                    <div className="time-crystal mt-4 p-2 rounded-sm" style={{ '--crystal-color': '#a855f7' } as React.CSSProperties}>
                                        <div className="chronos-connector diagonal" style={{ '--color': '#a855f7' } as React.CSSProperties}></div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[9px] font-bold text-purple-200 uppercase tracking-wider">IG Reels</span>
                                            <span className="ml-auto size-1 bg-purple-400 rounded-full shadow-[0_0_5px_#a855f7]"></span>
                                        </div>
                                        <div className="text-[10px] text-slate-300 font-mono">10:00 UTC</div>
                                    </div>
                                </div>
                                <div className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                    <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">04</span>
                                </div>

                                {/* Today Highlights */}
                                <div className="grid-cell bg-[#060b0c]/80 border border-cyan-400/50 relative p-2 shadow-neon z-20 overflow-visible transform translate-z-10">
                                    <div className="beam-of-light"></div>
                                    <div className="beam-core"></div>
                                    <div className="flex justify-between items-start relative z-20">
                                        <span className="text-cyan-400 font-mono text-sm font-bold drop-shadow-[0_0_5px_#0bf]">05</span>
                                        <span className="text-[8px] bg-cyan-400 text-black font-bold px-1 py-0.5 uppercase tracking-wider">Hoje</span>
                                    </div>
                                    <div className="time-crystal mt-4 p-2 rounded-sm bg-cyan-400/10 border-cyan-400/30" style={{ '--crystal-color': '#0bf' } as React.CSSProperties}>
                                        <div className="chronos-connector" style={{ '--color': '#0bf' } as React.CSSProperties}></div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[9px] font-bold text-cyan-100 uppercase tracking-wider">TikTok Gaming</span>
                                            <span className="ml-auto material-symbols-outlined text-[10px] text-cyan-300 animate-spin">sync</span>
                                        </div>
                                        <div className="text-[10px] text-cyan-200 font-mono">14:00 UTC</div>
                                        <div className="h-0.5 w-full bg-cyan-400/20 mt-1 rounded-full overflow-hidden">
                                            <div className="h-full bg-cyan-400 w-2/3 shadow-[0_0_5px_#0bf]"></div>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                    <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">06</span>
                                    <div className="mt-8 p-2 border border-dashed border-slate-600 bg-black/40 backdrop-blur-sm opacity-60 transform translate-z-2 hover:translate-z-4 hover:opacity-100 transition-all">
                                        <span className="text-[9px] text-slate-400 uppercase tracking-wider block">Rascunho: Prod V2</span>
                                    </div>
                                </div>
                                <div className="grid-cell bg-[#060b0c]/20 border border-white/5 relative p-2">
                                    <span className="text-slate-600 font-mono text-xs">07</span>
                                </div>
                                <div className="grid-cell bg-[#060b0c]/20 border border-white/5 relative p-2">
                                    <span className="text-slate-600 font-mono text-xs">08</span>
                                </div>

                                {/* Next Week Filler */}
                                {Array.from({ length: 4 }).map((_, i) => (
                                    <div key={`next-${i}`} className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                        <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">{9 + i}</span>
                                    </div>
                                ))}

                                <div className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                    <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">13</span>
                                    <div className="time-crystal mt-4 p-2 rounded-sm" style={{ '--crystal-color': '#f59e0b' } as React.CSSProperties}>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[9px] font-bold text-amber-200 uppercase tracking-wider">YT Short</span>
                                            <span className="ml-auto size-1 bg-amber-400 rounded-full shadow-[0_0_5px_#f59e0b]"></span>
                                        </div>
                                        <div className="text-[10px] text-slate-300 font-mono">16:30 UTC</div>
                                    </div>
                                </div>

                                {Array.from({ length: 5 }).map((_, i) => (
                                    <div key={`mid-${i}`} className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                        <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">{14 + i}</span>
                                    </div>
                                ))}
                                <div className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                    <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">19</span>
                                    <div className="time-crystal mt-4 p-2 rounded-sm" style={{ '--crystal-color': '#ef4444' } as React.CSSProperties}>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-[9px] font-bold text-red-200 uppercase tracking-wider">Lançamento</span>
                                            <span className="ml-auto material-symbols-outlined text-[10px] text-red-400">rocket_launch</span>
                                        </div>
                                        <div className="text-[10px] text-slate-300 font-mono">11:00 UTC</div>
                                    </div>
                                </div>

                                {Array.from({ length: 11 }).map((_, i) => (
                                    <div key={`end-${i}`} className="grid-cell bg-[#0c1618]/60 border border-white/10 relative p-2 group hover:border-cyan-400/30">
                                        <span className="text-slate-400 font-mono text-xs group-hover:text-cyan-400 transition-colors">{20 + i}</span>
                                    </div>
                                ))}

                            </div>
                        </div>
                    </div>

                    {/* Staging Dock Panel */}
                    <div className="w-80 flex-shrink-0 flex flex-col gap-4 z-50">
                        <div className="glass-panel p-0 rounded-none flex-1 flex flex-col h-full border border-white/10 shadow-[0_0_20px_rgba(0,0,0,0.5)] relative overflow-hidden backdrop-blur-3xl">
                            <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-cyan-400/40"></div>
                            <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-cyan-400/40"></div>

                            <div className="p-5 border-b border-white/10 bg-[#060b0c]/80 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-cyan-400 text-[20px] animate-pulse-slow">precision_manufacturing</span>
                                    <h3 className="text-white font-bold text-xs tech-stencil">Doca de Preparação</h3>
                                </div>
                                <div className="flex gap-2">
                                    <button className="text-slate-500 hover:text-cyan-400 transition-colors">
                                        <span className="material-symbols-outlined text-[18px]">tune</span>
                                    </button>
                                </div>
                            </div>

                            <div className="p-4 bg-[#0c1618]/50">
                                <div className="relative">
                                    <input className="w-full bg-black/40 border border-white/10 px-3 py-2 pl-9 text-xs text-white placeholder-slate-600 font-mono focus:outline-none focus:border-cyan-400/50" placeholder="FILTRAR CARGAS..." type="text" />
                                    <span className="material-symbols-outlined absolute left-2 top-2 text-cyan-400/50 text-[16px]">filter_alt</span>
                                </div>
                            </div>

                            <div className="flex flex-col gap-0 overflow-y-auto flex-1 dock-slot scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">

                                <div className="p-4 border-b border-white/5 hover:bg-white/5 cursor-grab active:cursor-grabbing group transition-all relative payload-ready">
                                    <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-cyan-400/0 group-hover:bg-cyan-400 transition-all"></div>
                                    <div className="flex gap-4">
                                        <div className="size-12 bg-black border border-white/10 relative overflow-hidden group-hover:border-cyan-400/50 transition-colors shrink-0">
                                            <div className="absolute inset-0 bg-cover bg-center opacity-70 group-hover:opacity-100 transition-opacity bg-[url('https://lh3.googleusercontent.com/aida-public/AB6AXuC5p7MjHgkG8S5UjLu1ZcSSWPHABvgZLQ7hfPq7FksYtr7ngiq2BMYmZNTPR694JoPz5iOM-FHLo3tPQ6tYbu5sOKVKM_li9o7v1GXwbphgGL4O5CEgehvOsK5G_MRkr1WpnCjsl4ycFmu1nU0zY3lyJz9gIBjAuCOqzPxj2WYj_cM-ofi3VevJPEboKqBoNfrvMxQ17Ry6dFI1Lq5LktZ_dKfcBjR5PcQ8eVtjetP9piEYUgHxJSwQmaWZpi85Fu3mzsd6W6ztmjw')]"></div>
                                            <div className="absolute bottom-0 right-0 bg-black/80 px-1 py-0.5 text-[8px] font-mono text-cyan-400 border-t border-l border-white/10">MP4</div>
                                        </div>
                                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                                            <h4 className="text-slate-200 text-xs font-bold truncate font-mono">Cyberpunk_Intro_v4</h4>
                                            <div className="flex items-center gap-3 mt-1.5">
                                                <div className="flex items-center gap-1 text-[10px] text-slate-500">
                                                    <span className="material-symbols-outlined text-[12px]">timer</span> 00:15
                                                </div>
                                                <div className="flex items-center gap-1 text-[10px] text-cyan-400/70">
                                                    <span className="material-symbols-outlined text-[12px]">check_circle</span> PRONTO
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center justify-center text-slate-600 group-hover:text-cyan-400 transition-colors">
                                            <span className="material-symbols-outlined text-[20px] mech-arm">precision_manufacturing</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-4 border-b border-white/5 hover:bg-white/5 cursor-grab active:cursor-grabbing group transition-all relative">
                                    <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-cyan-400/0 group-hover:bg-purple-500 transition-all"></div>
                                    <div className="flex gap-4">
                                        <div className="size-12 bg-black border border-white/10 relative overflow-hidden group-hover:border-purple-500/50 transition-colors shrink-0">
                                            <div className="absolute inset-0 bg-cover bg-center opacity-70 group-hover:opacity-100 transition-opacity bg-[url('https://lh3.googleusercontent.com/aida-public/AB6AXuCp3ZSJi4VX2PPXcgxESiy8yAAXcCDK50mlZ1_v0kW1Tv-WMVitvttd1D7HqdNfz548HUWhFD6TBfcXf0_tTvWiuTIjOsBHq1FMu3UNXWUXwOeelEUV5oqGkV_lcVBuy9gj2a3342H3Hk8fKRV67YlQc2pBipjPRsEGPODTR77GK9MkihpY0_UkxWgk69nU9iwlhBRvOBo13lGvukAizQt5pQs0QDm6CU52Nr63aKpCo-Vol5uKzWfA8lJZKxMyWn7wGeLcF_izkzg')]"></div>
                                            <div className="absolute bottom-0 right-0 bg-black/80 px-1 py-0.5 text-[8px] font-mono text-purple-400 border-t border-l border-white/10">MOV</div>
                                        </div>
                                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                                            <h4 className="text-slate-200 text-xs font-bold truncate font-mono">Neon_City_Loop</h4>
                                            <div className="flex items-center gap-3 mt-1.5">
                                                <div className="flex items-center gap-1 text-[10px] text-slate-500">
                                                    <span className="material-symbols-outlined text-[12px]">timer</span> 00:30
                                                </div>
                                                <div className="flex items-center gap-1 text-[10px] text-slate-500">
                                                    <span className="material-symbols-outlined text-[12px]">cloud_upload</span> 95%
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center justify-center text-slate-600 group-hover:text-white transition-colors">
                                            <span className="material-symbols-outlined text-[20px]">drag_indicator</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="m-4 border border-dashed border-cyan-400/30 bg-cyan-400/5 p-6 flex flex-col items-center justify-center text-center group hover:bg-cyan-400/10 transition-colors cursor-pointer">
                                    <div className="p-2 rounded-full bg-cyan-400/10 mb-2 group-hover:scale-110 transition-transform">
                                        <span className="material-symbols-outlined text-cyan-400 text-[24px]">input</span>
                                    </div>
                                    <span className="text-[10px] text-cyan-400/70 font-mono uppercase tracking-wider">Inicializar Upload</span>
                                </div>

                            </div>
                        </div>

                        <div className="glass-panel p-4 rounded-none border border-white/10 relative overflow-hidden backdrop-blur-3xl">
                            <div className="absolute top-0 left-0 w-full h-[1px] bg-cyan-400/50 shadow-[0_0_10px_#0bf] animate-[scan_2s_ease-in-out_infinite]"></div>
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-[10px] font-bold text-slate-400 tech-stencil">Taxa de Transferência do Uplink</span>
                                <span className="text-cyan-400 text-xs font-mono font-bold">12.4 TB/s</span>
                            </div>
                            <div className="relative h-12 w-full flex items-end gap-[2px] opacity-80">
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/40 h-[30%]"></div>
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/50 h-[50%]"></div>
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/30 h-[20%]"></div>
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/60 h-[70%]"></div>
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/20 to-cyan-400 h-[90%] shadow-[0_0_8px_rgba(7,182,213,0.4)]"></div>
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/50 h-[45%]"></div>
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/20 h-[25%]"></div>
                                <div className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/30 h-[35%]"></div>
                            </div>
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}
