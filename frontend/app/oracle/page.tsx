'use client';

import React from 'react';

export default function OraclePage() {
    return (
        <div className="relative z-10 flex flex-col h-full grow w-full mx-auto min-h-[calc(100vh-88px)] bg-transparent text-slate-100 font-display selection:bg-cyan-400/30 selection:text-white">
            {/* Background elements */}
            <div className="fixed inset-0 z-0 pointer-events-none bg-[radial-gradient(circle_at_50%_40%,#1e1b4b_0%,#0f172a_40%,#020204_100%)]">
                <div className="absolute top-[-20%] left-[-10%] w-[80%] h-[80%] nebula-cloud opacity-40 mix-blend-screen animate-pulse duration-[10000ms]"></div>
                <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] nebula-cloud opacity-30 mix-blend-screen animate-pulse duration-[12000ms]" style={{ background: 'radial-gradient(circle at 50% 50%, rgba(7, 182, 213, 0.06), transparent 70%)' }}></div>
                <div className="absolute inset-0 star-field opacity-60"></div>
                <div className="absolute inset-0 star-field opacity-30 scale-150 transform rotate-12"></div>
                <div className="absolute inset-0 opacity-[0.07] mix-blend-overlay"></div>
                <div className="absolute inset-0 scan-line pointer-events-none"></div>
            </div>

            <main className="flex flex-col flex-1 relative items-center justify-center overflow-hidden z-10 w-full">

                <div className="relative w-full max-w-5xl h-[700px] flex items-center justify-center perspective-1000">
                    <div className="absolute w-[650px] h-[650px] transform-style-3d orbit-container pointer-events-none opacity-80">
                        <div className="absolute inset-0 border border-cyan-400/10 rounded-full transform rotate-x-[75deg] shadow-[0_0_15px_rgba(7,182,213,0.05)]"></div>
                        <div className="absolute inset-[15%] border border-indigo-500/15 rounded-full transform rotate-x-[75deg] rotate-y-[45deg]"></div>
                        <div className="absolute inset-[30%] border border-white/5 rounded-full transform rotate-x-[75deg] rotate-y-[-45deg] border-dashed"></div>

                        <div className="absolute top-[10%] left-[50%] transform -translate-x-1/2 translate-z-[240px] orbit-item">
                            <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group">
                                <span className="size-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(7,182,213,0.8)]"></span>
                                <span className="text-[10px] font-mono text-cyan-400/90 tracking-wider group-hover:text-white transition-colors uppercase drop-shadow-[0_0_5px_rgba(7,182,213,0.4)]">Aprendizado_Profundo</span>
                            </div>
                        </div>

                        <div className="absolute top-[50%] right-[0%] transform translate-x-1/2 translate-z-[120px] orbit-item">
                            <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group">
                                <span className="size-1.5 bg-indigo-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
                                <span className="text-[10px] font-mono text-indigo-400/90 tracking-wider group-hover:text-white transition-colors uppercase drop-shadow-[0_0_5px_rgba(99,102,241,0.4)]">Rede_Neural</span>
                            </div>
                        </div>

                        <div className="absolute bottom-[20%] left-[20%] transform translate-z-[-180px] orbit-item">
                            <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group border-white/10">
                                <span className="size-1.5 bg-slate-400 rounded-full"></span>
                                <span className="text-[10px] font-mono text-slate-300 tracking-wider uppercase">Auto_Escala</span>
                            </div>
                        </div>

                        <div className="absolute top-[20%] right-[20%] transform translate-z-[60px] orbit-item">
                            <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group border-white/10">
                                <span className="size-1.5 bg-slate-400 rounded-full"></span>
                                <span className="text-[10px] font-mono text-slate-300 tracking-wider uppercase">Hash_Quântico</span>
                            </div>
                        </div>

                        <div className="absolute bottom-[10%] right-[40%] transform translate-z-[200px] orbit-item">
                            <div className="glass-tag px-4 py-1.5 rounded-sm flex items-center gap-2 group">
                                <span className="size-1.5 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(7,182,213,0.8)]"></span>
                                <span className="text-[10px] font-mono text-cyan-400/90 tracking-wider uppercase drop-shadow-[0_0_5px_rgba(7,182,213,0.4)]">Singularidade</span>
                            </div>
                        </div>
                    </div>

                    <div className="relative z-20 group w-full max-w-[500px] flex flex-col items-center gap-12">
                        <div className="relative size-56 md:size-72 flex items-center justify-center">
                            <div className="absolute inset-4 rounded-full z-10 singularity-core volumetric-glow border border-cyan-400/20 overflow-hidden">
                                <div className="absolute inset-0 internal-energy opacity-50 mix-blend-screen"></div>
                                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-400/5 to-transparent animate-pulse"></div>
                            </div>

                            <div className="absolute inset-0 rounded-full border border-cyan-400/10 border-t-cyan-400/40 animate-spin" style={{ animationDuration: '8s' }}></div>
                            <div className="absolute inset-[-15px] rounded-full border border-indigo-500/10 border-b-indigo-500/30 animate-[spin_12s_linear_infinite_reverse]"></div>
                            <div className="absolute inset-[-30px] rounded-full border border-dashed border-white/5 animate-[spin_20s_linear_infinite]"></div>
                            <div className="absolute inset-[-50px] bg-cyan-400/5 rounded-full blur-[60px] animate-pulse"></div>

                            <div className="relative z-20 w-full h-full flex items-center justify-center">
                                <input autoFocus className="bg-transparent border-none text-center text-white text-xl font-medium placeholder:text-cyan-400/30 focus:ring-0 w-[80%] drop-shadow-[0_0_10px_rgba(255,255,255,0.2)] tracking-wide outline-none" placeholder="INICIAR SEQUÊNCIA..." type="text" />
                            </div>
                        </div>

                        <div className="text-center space-y-3 opacity-0 group-focus-within:opacity-100 transition-opacity duration-700">
                            <p className="text-cyan-400 tracking-[0.3em] text-[10px] font-mono soft-pulse uppercase border-b border-cyan-400/20 pb-1 inline-block">Aguardando Sequência de Entrada</p>
                            <p className="text-slate-500 text-xs font-mono tracking-wide">Pressione <span className="text-white">ENTER</span> para acionar o motor de dobra</p>
                        </div>
                    </div>
                </div>

                <div className="absolute inset-0 pointer-events-none z-0 flex justify-between px-10 md:px-32 overflow-hidden opacity-10">
                    <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '2.5s', animationDelay: '0.2s' }}></div>
                    <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '3.1s', animationDelay: '1.5s' }}></div>
                    <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '2.8s', animationDelay: '0.8s' }}></div>
                    <div className="w-[1px] h-full matrix-rain hidden md:block" style={{ animationDuration: '3.5s', animationDelay: '2.1s' }}></div>
                    <div className="w-[1px] h-full matrix-rain" style={{ animationDuration: '2.2s', animationDelay: '0.5s' }}></div>
                    <div className="w-[1px] h-full matrix-rain hidden md:block" style={{ animationDuration: '4s', animationDelay: '1.2s' }}></div>
                </div>
            </main>
        </div>
    );
}
