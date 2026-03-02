'use client';

import React from 'react';

export default function MetricsPage() {
    return (
        <div className="relative flex h-full w-full flex-col bg-black overflow-hidden group/design-root schematic-bg animate-drift" style={{ backgroundSize: '100px 100px' }}>
            <div className="absolute inset-0 pointer-events-none z-50 bg-scanline bg-[length:100%_4px] opacity-15 animate-scan mix-blend-overlay"></div>
            <div className="absolute inset-0 pointer-events-none z-40 crt-overlay opacity-40"></div>
            <div className="absolute inset-0 pointer-events-none z-0 opacity-10 flex items-center justify-center">
                <svg className="w-full h-full stroke-cyan-400 fill-none stroke-[0.5]" style={{ WebkitMaskImage: 'radial-gradient(circle, black 40%, transparent 70%)' }} viewBox="0 0 800 600">
                    <circle cx="400" cy="300" r="250" strokeDasharray="4 4"></circle>
                    <circle cx="400" cy="300" r="150" strokeDasharray="10 5"></circle>
                    <line x1="150" x2="650" y1="300" y2="300"></line>
                    <line x1="400" x2="400" y1="50" y2="550"></line>
                    <rect height="200" strokeWidth="1" width="400" x="200" y="200"></rect>
                </svg>
            </div>

            <main className="flex flex-1 overflow-hidden relative z-20 w-full max-w-[1600px] mx-auto">
                <aside className="hidden lg:flex w-80 flex-col border-r border-white/10 bg-[#020202] p-6 gap-8 shrink-0 relative shadow-[15px_0_30px_-5px_rgba(0,0,0,0.9)] z-30">
                    <div className="absolute top-2 left-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>
                    <div className="absolute top-2 right-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>
                    <div className="absolute bottom-2 left-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>
                    <div className="absolute bottom-2 right-2 size-1.5 bg-slate-800 shadow-[0_0_5px_rgba(255,255,255,0.2)]"></div>

                    <div className="flex flex-col gap-5 mt-6">
                        <p className="text-slate-500 font-display text-sm uppercase tracking-[0.2em] border-b border-white/5 pb-2 text-right">Matriz de Filtro</p>
                        <div className="flex items-center justify-between group py-1">
                            <span className="text-xs text-slate-400 font-mono tracking-widest group-hover:text-cyan-400 transition-colors">TODOS OS SISTEMAS</span>
                            <div className="relative inline-block w-10 align-middle select-none transition duration-200 ease-in">
                                <input className="toggle-checkbox absolute block w-4 h-4 bg-black border border-slate-600 appearance-none cursor-pointer rounded-none transition-all duration-200 ease-in-out checked:bg-cyan-400 checked:translate-x-full" id="toggle1" name="toggle" type="checkbox" defaultChecked />
                                <label className="toggle-label block overflow-hidden h-4 bg-slate-900 cursor-pointer border border-slate-800" htmlFor="toggle1"><span className="sr-only">Todos os Sistemas</span></label>
                            </div>
                        </div>
                        <div className="flex items-center justify-between group py-1">
                            <span className="text-xs text-slate-400 font-mono tracking-widest group-hover:text-magenta-500 transition-colors shadow-magenta-500/50">APENAS ERROS</span>
                            <div className="relative inline-block w-10 align-middle select-none transition duration-200 ease-in">
                                <input className="toggle-checkbox absolute block w-4 h-4 bg-black border border-slate-600 appearance-none cursor-pointer rounded-none transition-all duration-200 ease-in-out checked:translate-x-full checked:bg-magenta-500" id="toggle2" name="toggle" type="checkbox" />
                                <label className="toggle-label block overflow-hidden h-4 bg-slate-900 cursor-pointer border border-slate-800" htmlFor="toggle2"><span className="sr-only">Apenas Erros</span></label>
                            </div>
                        </div>
                        <div className="flex items-center justify-between group py-1">
                            <span className="text-xs text-slate-400 font-mono tracking-widest group-hover:text-yellow-400 transition-colors">AVISOS</span>
                            <div className="relative inline-block w-10 align-middle select-none transition duration-200 ease-in">
                                <input className="toggle-checkbox absolute block w-4 h-4 bg-black border border-slate-600 appearance-none cursor-pointer rounded-none transition-all duration-200 ease-in-out checked:translate-x-full checked:bg-yellow-400" id="toggle3" name="toggle" type="checkbox" defaultChecked />
                                <label className="toggle-label block overflow-hidden h-4 bg-slate-900 cursor-pointer border border-slate-800" htmlFor="toggle3"><span className="sr-only">Avisos</span></label>
                            </div>
                        </div>
                    </div>

                    <div className="w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-2"></div>

                    <div className="flex flex-col gap-3">
                        <p className="text-slate-500 font-display text-xs uppercase tracking-[0.2em] mb-2 text-right">Modos de Operação</p>
                        <button className="w-full border border-cyan-400/40 text-cyan-400 bg-cyan-400/5 hover:bg-cyan-400/10 py-2.5 px-4 text-[10px] font-mono uppercase tracking-[0.15em] transition-all flex items-center justify-between shadow-[0_0_10px_rgba(0,240,255,0.05)] group">
                            <span className="group-hover:translate-x-1 transition-transform">Log ao Vivo</span>
                            <span className="material-symbols-outlined text-[14px] animate-spin group-hover:text-white transition-colors">sync</span>
                        </button>
                        <button className="w-full border border-slate-800 text-slate-500 hover:text-white hover:border-white/20 bg-transparent py-2.5 px-4 text-[10px] font-mono uppercase tracking-[0.15em] transition-all flex items-center justify-between group">
                            <span className="group-hover:translate-x-1 transition-transform">Modo de Depuração</span>
                            <span className="material-symbols-outlined text-[14px] group-hover:text-white transition-colors">bug_report</span>
                        </button>
                    </div>

                    <div className="mt-auto bg-[#030303] border border-white/10 p-4 relative overflow-hidden group">
                        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(0,240,255,0.03)_50%,transparent_75%,transparent_100%)] bg-[length:250%_250%,100%_100%] bg-[position:-100%_0,0_0] bg-no-repeat transition-[background-position_0s_ease] hover:bg-[position:200%_0,0_0] duration-1000"></div>
                        <div className="flex items-center justify-between mb-3 relative z-10">
                            <span className="text-[10px] text-cyan-400 font-display tracking-widest">CAPACIDADE_DO_BUFFER</span>
                            <span className="text-[10px] text-cyan-400 font-mono">24%</span>
                        </div>
                        <div className="flex gap-0.5 h-1.5 w-full">
                            <div className="flex-1 bg-cyan-400 shadow-[0_0_5px_#00f0ff]"></div>
                            <div className="flex-1 bg-cyan-400 shadow-[0_0_5px_#00f0ff]"></div>
                            <div className="flex-1 bg-cyan-400 shadow-[0_0_5px_#00f0ff]"></div>
                            <div className="flex-1 bg-cyan-400/20"></div>
                            <div className="flex-1 bg-cyan-400/20"></div>
                            <div className="flex-1 bg-cyan-400/20"></div>
                            <div className="flex-1 bg-cyan-400/20"></div>
                            <div className="flex-1 bg-cyan-400/20"></div>
                        </div>
                        <div className="mt-2 text-[8px] text-slate-600 font-mono text-right">SYS_ID: 8X-99</div>
                    </div>
                </aside>

                <div className="flex-1 flex flex-col bg-transparent relative overflow-hidden hud-perspective">
                    <div className="flex items-center justify-between px-6 py-2 pb-4 pt-6 border-b border-white/10 bg-black/80 backdrop-blur z-10 shrink-0">
                        <div className="flex items-center gap-4">
                            <h1 className="text-4xl font-display tracking-[0.2em] text-white uppercase drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">Fluxo de Telemetria</h1>
                            <span className="px-2 py-0.5 bg-magenta-500/10 border border-magenta-500/30 text-[9px] text-magenta-500 font-mono tracking-wider animate-pulse">CANAL SEGURO // CRIPTOGRAFADO</span>
                        </div>
                        <div className="flex gap-2">
                            <button className="p-1.5 text-cyan-400 hover:bg-cyan-400/10 border border-transparent hover:border-cyan-400/30 transition-colors" title="Download Logs">
                                <span className="material-symbols-outlined text-[18px]">download</span>
                            </button>
                            <button className="p-1.5 text-magenta-500 hover:bg-magenta-500/10 border border-transparent hover:border-magenta-500/30 transition-colors" title="Clear Console">
                                <span className="material-symbols-outlined text-[18px]">delete_sweep</span>
                            </button>
                            <button className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 border border-transparent hover:border-white/30 transition-colors" title="Pause Stream">
                                <span className="material-symbols-outlined text-[18px]">pause</span>
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto overflow-x-hidden p-8 font-mono text-sm leading-relaxed scroll-smooth relative" id="terminal-content">
                        <div className="w-full max-w-7xl mx-auto hud-tilted min-h-[800px] h-full backdrop-blur-sm relative p-10 pb-20">
                            <div className="absolute top-0 left-0 w-16 h-16 border-t border-l border-cyan-400/60"></div>
                            <div className="absolute top-0 right-0 w-16 h-16 border-t border-r border-cyan-400/60"></div>
                            <div className="absolute bottom-0 left-0 w-16 h-16 border-b border-l border-cyan-400/60"></div>
                            <div className="absolute bottom-0 right-0 w-16 h-16 border-b border-r border-cyan-400/60"></div>

                            <div className="absolute top-2 left-2 text-[9px] text-cyan-400/40 font-mono">COORD: 45.21, 12.90</div>
                            <div className="absolute bottom-2 right-2 text-[9px] text-cyan-400/40 font-mono">HUD_VER: 4.2</div>

                            <div className="flex flex-col gap-0.5 w-full relative z-10">
                                <div className="log-line flex gap-4 hover:bg-white/5 p-1 px-4 transition-colors group items-center border-l-2 border-transparent hover:border-cyan-400/50">
                                    <span className="text-slate-600 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider opacity-70">2023-10-27 14:02:01.452</span>
                                    <span className="text-cyan-400 font-bold w-12 shrink-0 tracking-wider text-xs">[INFO]</span>
                                    <span className="text-slate-500 w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest">Worker-01</span>
                                    <span className="text-slate-300 group-hover:text-cyan-400 transition-colors font-light text-xs">Processo iniciado. Sequência da ponte neural: <span className="text-green-400 font-bold">OK</span></span>
                                </div>

                                <div className="log-line flex gap-4 hover:bg-white/5 p-1 px-4 transition-colors group items-center border-l-2 border-transparent hover:border-cyan-400/50">
                                    <span className="text-slate-600 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider opacity-70">2023-10-27 14:02:05.112</span>
                                    <span className="text-cyan-400 font-bold w-12 shrink-0 tracking-wider text-xs">[INFO]</span>
                                    <span className="text-slate-500 w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest">Worker-01</span>
                                    <span className="text-slate-300 group-hover:text-cyan-400 transition-colors font-light text-xs">Carregando pacote interno: <span className="text-white bg-white/10 px-1 border border-white/20">cosmic_dust.mp4</span> (Size: 450MB)</span>
                                </div>

                                <div className="log-line flex gap-4 bg-magenta-500/5 hover:bg-magenta-500/10 p-3 px-4 my-2 transition-all group items-center border border-magenta-500/40 shadow-[0_0_20px_-5px_rgba(255,0,255,0.4)] relative overflow-hidden error-shake">
                                    <div className="absolute inset-0 bg-magenta-500/5 animate-pulse"></div>
                                    <div className="absolute top-0 bottom-0 left-0 w-1 bg-magenta-500 animate-pulse"></div>
                                    <span className="text-magenta-500/60 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider relative z-10">2023-10-27 14:03:00.005</span>
                                    <span className="text-magenta-500 font-bold w-12 shrink-0 tracking-wider relative z-10 text-xs">[ERR]</span>
                                    <span className="text-magenta-500/80 w-28 shrink-0 font-mono uppercase relative z-10 text-[10px] tracking-widest">API_Gate</span>
                                    <span className="text-white relative z-10 glitch-text text-xs font-bold tracking-wide" data-text="HTTP 401: Tentativa de acesso não autorizado detectada do IP 192.168.1.45.">HTTP 401: Tentativa de acesso não autorizado detectada do IP 192.168.1.45.</span>
                                </div>

                                <div className="log-line flex gap-4 hover:bg-white/5 p-1 px-4 transition-colors group items-center border-l-2 border-transparent hover:border-cyan-400/50">
                                    <span className="text-slate-600 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider opacity-70">2023-10-27 14:03:08.110</span>
                                    <span className="text-cyan-400 font-bold w-12 shrink-0 tracking-wider text-xs">[INFO]</span>
                                    <span className="text-slate-500 w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest">Worker-02</span>
                                    <span className="text-slate-300 group-hover:text-cyan-400 transition-colors font-light text-xs">Modo de espera ativado. Aguardando designação do balanceador.</span>
                                </div>

                                <div className="log-line flex gap-4 hover:bg-green-500/5 p-1 px-4 transition-colors group items-center border-l-2 border-transparent hover:border-green-500/50">
                                    <span className="text-slate-600 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider opacity-70">2023-10-27 14:03:10.552</span>
                                    <span className="text-green-500 font-bold w-12 shrink-0 tracking-wider text-xs">[OK]</span>
                                    <span className="text-slate-500 w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest">Auth_Svc</span>
                                    <span className="text-green-100/80 group-hover:text-green-400 transition-colors font-light text-xs">Token atualizado com sucesso. Sessão válida por 3600s.</span>
                                </div>

                                <div className="log-line flex gap-4 hover:bg-yellow-500/5 p-1 px-4 transition-colors group items-center border-l-2 border-transparent hover:border-yellow-500/50">
                                    <span className="text-slate-600 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider opacity-70">2023-10-27 14:03:15.678</span>
                                    <span className="text-yellow-500 font-bold w-12 shrink-0 tracking-wider text-xs">[WARN]</span>
                                    <span className="text-slate-500 w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest">Render_C</span>
                                    <span className="text-yellow-100/80 group-hover:text-yellow-400 transition-colors font-light text-xs">Queda de quadros detectada no setor 7. Estrangulamento da GPU ativo.</span>
                                </div>

                                <div className="log-line flex gap-4 bg-magenta-500/5 hover:bg-magenta-500/10 p-3 px-4 my-2 transition-all group items-center border border-magenta-500/40 shadow-[0_0_20px_-5px_rgba(255,0,255,0.4)] relative overflow-hidden error-shake">
                                    <div className="absolute inset-0 bg-magenta-500/5 animate-pulse"></div>
                                    <div className="absolute top-0 bottom-0 left-0 w-1 bg-magenta-500 animate-pulse"></div>
                                    <span className="text-magenta-500/60 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider relative z-10">2023-10-27 14:03:28.445</span>
                                    <span className="text-magenta-500 font-bold w-12 shrink-0 tracking-wider relative z-10 text-xs">[ERR]</span>
                                    <span className="text-magenta-500/80 w-28 shrink-0 font-mono uppercase relative z-10 text-[10px] tracking-widest">DB_Conn</span>
                                    <span className="text-white relative z-10 glitch-text text-xs font-bold tracking-wide" data-text="Tempo limite de conexão no shard-04. Tentando novamente... (Tentativa 2/5)">Tempo limite de conexão no shard-04. Tentando novamente... (Tentativa 2/5)</span>
                                </div>

                                <div className="log-line flex gap-4 p-2 px-4 mt-6 transition-colors group items-center border border-cyan-400/40 bg-cyan-400/5 shadow-[0_0_20px_-5px_rgba(0,240,255,0.4)]">
                                    <span className="text-cyan-400/70 font-mono w-36 shrink-0 text-[10px] mt-0.5 tracking-wider">2023-10-27 14:03:30.000</span>
                                    <span className="text-cyan-400 font-bold w-12 shrink-0 tracking-wider text-xs">[INFO]</span>
                                    <span className="text-cyan-400/70 w-28 shrink-0 font-mono uppercase text-[10px] tracking-widest">System</span>
                                    <span className="text-white font-bold text-scan-effect uppercase tracking-widest text-xs">Fluxo de log ao vivo ativo... <span className="animate-ping text-cyan-400">_</span></span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="shrink-0 bg-black/90 backdrop-blur border-t border-white/10 px-6 py-3 flex items-center justify-between text-xs font-mono z-30">
                        <div className="flex items-center gap-8">
                            <span className="flex items-center gap-2 text-cyan-400 drop-shadow-[0_0_5px_rgba(0,240,255,0.5)]">
                                <span className="size-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(0,240,255,0.8)]"></span>
                                <span className="tracking-widest text-[10px] uppercase">Stream: wss://api.synapse.ai/v1/stream</span>
                            </span>
                            <span className="text-slate-500 text-[10px] uppercase tracking-wider">LATENCY: <span className="text-white font-bold">45ms</span></span>
                        </div>
                        <div className="flex items-center gap-8 text-slate-500 text-[10px] uppercase tracking-wider">
                            <span>MEM: <span className="text-white">12.4GB</span> <span className="text-slate-700 mx-1">/</span> 32GB</span>
                            <span>CPU: <span className="text-white">34%</span></span>
                            <span className="text-magenta-500 drop-shadow-[0_0_5px_rgba(255,0,255,0.5)]">UPTIME: 14d 02h 12m</span>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
