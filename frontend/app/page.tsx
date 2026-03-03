import React from 'react';

export default function Home() {
  return (
    <div className="flex-1 w-full grid grid-cols-12 gap-6 h-full min-h-[600px]">

      {/* Left Column: Stats & Probes */}
      <div className="col-span-12 xl:col-span-3 flex flex-col gap-4 h-full relative z-20">
        <div className="connection-line top-1/2 right-[-24px] w-[24px]" style={{ top: '20%' }}>
          <div className="pulse-packet" style={{ animationDelay: '0.5s' }}></div>
        </div>

        <div className="atmospheric-glass p-5 rounded-sm relative group overflow-hidden transition-all duration-300 hover:bg-white/5">
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex justify-between items-start mb-4 relative z-10">
            <span className="text-xs font-mono text-cyan-500/60 uppercase tracking-widest">Taxa de Ingestão</span>
            <span className="material-symbols-outlined text-white/20 group-hover:text-cyan-400 transition-colors animate-pulse">speed</span>
          </div>
          <div className="text-3xl font-display font-bold text-white mb-1 drop-shadow-[0_0_8px_rgba(0,240,255,0.3)]">
            27 <span className="text-lg text-slate-500 font-normal">vídeos/dia</span>
          </div>
          <div className="text-xs font-mono text-emerald-400 flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">arrow_upward</span> Fluxo Contínuo
          </div>
          <div className="absolute top-0 left-0 w-2 h-2 border-l border-t border-cyan-500/50"></div>
          <div className="absolute bottom-0 right-0 w-2 h-2 border-r border-b border-cyan-500/50"></div>
        </div>

        <div className="atmospheric-glass p-5 rounded-sm relative group overflow-hidden hover:bg-white/5 transition-all">
          <div className="absolute inset-0 bg-gradient-to-br from-magenta-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex justify-between items-start mb-4 relative z-10">
            <span className="text-xs font-mono text-magenta-500/60 uppercase tracking-widest">Espaço em Disco</span>
            <span className="material-symbols-outlined text-white/20 group-hover:text-magenta-400 transition-colors">dns</span>
          </div>
          <div className="text-3xl font-display font-bold text-white mb-1 drop-shadow-[0_0_8px_rgba(255,0,85,0.3)]">
            42.8 <span className="text-lg text-slate-500 font-normal">GB Livre</span>
          </div>
          <div className="w-full bg-slate-800/50 h-1 mt-2 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-magenta-600 to-purple-500 h-full w-[65%] shadow-[0_0_20px_rgba(255,0,85,0.3)] relative">
              <div className="absolute top-0 right-0 h-full w-2 bg-white/80 blur-[2px] animate-pulse"></div>
            </div>
          </div>
        </div>

        <div className="atmospheric-glass flex-1 p-5 rounded-sm relative flex flex-col overflow-hidden hover:bg-white/5 transition-all min-h-[200px]">
          <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
            <span className="text-xs font-display font-bold text-white uppercase tracking-wider text-cyan-200">Nós de Publicação</span>
            <span className="text-[10px] font-mono text-slate-500 animate-pulse">AUTO-SYNC</span>
          </div>
          <div className="space-y-3 font-mono text-xs overflow-y-auto pr-2 custom-scrollbar relative z-10">
            <div className="flex items-center justify-between p-2 bg-white/5 border-l-2 border-cyan-500 hover:bg-cyan-500/10 transition-colors cursor-pointer group/item">
              <div>
                <div className="text-cyan-300 font-bold group-hover/item:text-white group-hover/item:shadow-[0_0_10px_rgba(255,255,255,0.4)] transition-all">@opiniao_viral</div>
                <div className="text-slate-500 text-[10px]">TikTok // Fazendo Upload</div>
              </div>
              <div className="h-1.5 w-1.5 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e] animate-pulse"></div>
            </div>
            <div className="flex items-center justify-between p-2 bg-white/5 border-l-2 border-slate-700 hover:bg-indigo-500/10 transition-colors cursor-pointer group/item">
              <div>
                <div className="text-slate-300 font-bold group-hover/item:text-white">@vibe.cortes</div>
                <div className="text-slate-500 text-[10px]">Insta Reels // Ocioso</div>
              </div>
              <div className="h-1.5 w-1.5 rounded-full bg-yellow-500 shadow-[0_0_5px_#eab308]"></div>
            </div>
            <div className="flex items-center justify-between p-2 bg-white/5 border-l-2 border-magenta-500 hover:bg-magenta-500/10 transition-colors cursor-pointer group/item">
              <div>
                <div className="text-magenta-300 font-bold group-hover/item:text-white">@corte.celestial</div>
                <div className="text-slate-500 text-[10px]">Shorts // Falha de Sessão</div>
              </div>
              <div className="h-1.5 w-1.5 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444] animate-ping"></div>
            </div>
          </div>
          <div className="absolute bottom-0 right-0 w-20 h-20 bg-gradient-to-tl from-cyan-500/10 to-transparent pointer-events-none"></div>
        </div>
      </div>

      {/* Center Column: Core Engine Graphic */}
      <div className="col-span-12 xl:col-span-6 flex flex-col items-center justify-center min-h-[500px] relative">
        {/* SVG Guidelines */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <svg className="w-full h-full max-w-[800px] opacity-40 mx-auto" viewBox="0 0 800 800">
            <circle cx="400" cy="400" fill="none" r="150" stroke="#00f0ff" strokeOpacity="0.1" strokeWidth="1"></circle>
            <circle cx="400" cy="400" fill="none" r="280" stroke="#00f0ff" strokeDasharray="2 10" strokeOpacity="0.3" strokeWidth="0.5"></circle>
            <circle cx="400" cy="400" fill="none" r="350" stroke="#6366f1" strokeOpacity="0.15" strokeWidth="1"></circle>
            <line stroke="url(#gradient-line-left)" strokeWidth="1" x1="400" x2="100" y1="400" y2="400"></line>
            <line stroke="url(#gradient-line-right)" strokeWidth="1" x1="400" x2="700" y1="400" y2="400"></line>
            <line stroke="url(#gradient-line-top)" strokeWidth="1" x1="400" x2="400" y1="400" y2="100"></line>
            <defs>
              <linearGradient id="gradient-line-left" x1="1" x2="0" y1="0" y2="0">
                <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.5"></stop>
                <stop offset="100%" stopColor="transparent"></stop>
              </linearGradient>
              <linearGradient id="gradient-line-right" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.5"></stop>
                <stop offset="100%" stopColor="transparent"></stop>
              </linearGradient>
              <linearGradient id="gradient-line-top" x1="0" x2="0" y1="1" y2="0">
                <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.5"></stop>
                <stop offset="100%" stopColor="transparent"></stop>
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="relative w-[500px] h-[500px] flex items-center justify-center transform-gpu mx-auto scale-75 md:scale-100">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-[300px] h-[300px] border border-cyan-500/20 rounded-full animate-ping opacity-20" style={{ animationDuration: '3s' }}></div>
            <div className="w-[200px] h-[200px] border border-indigo-500/20 rounded-full animate-ping opacity-30" style={{ animationDelay: '1.5s', animationDuration: '3s' }}></div>
          </div>

          <div className="relative z-20 w-40 h-40 rounded-full bg-black flex items-center justify-center shadow-[0_0_80px_rgba(0,240,255,0.3)] animate-float-slow group cursor-pointer">
            <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_30%_30%,_rgba(0,240,255,0.4),_transparent_60%)]"></div>
            <div className="absolute inset-0 rounded-full border border-cyan-500/40 bg-black/60 backdrop-blur-sm z-10"></div>
            <div className="absolute w-20 h-20 bg-cyan-400 rounded-full blur-xl opacity-40 animate-heartbeat z-0"></div>

            <div className="text-center z-30 relative mt-6">
              <div className="text-[10px] font-mono text-cyan-300 tracking-[0.2em] mb-1 opacity-70">NÚCLEO NEURAL (CPU)</div>
              <div className="text-4xl font-display font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.8)] chromatic-text" data-text="84%">84%</div>
              <div className="text-[9px] font-mono text-indigo-300 mt-1">EM PROCESSAMENTO</div>
            </div>

            <div className="absolute inset-[-10px] border-l-2 border-r-2 border-cyan-500/60 rounded-full animate-[spin_4s_linear_infinite] z-20"></div>
            <div className="absolute inset-[-20px] border-t border-b border-indigo-500/40 rounded-full animate-spin-reverse-slow z-10"></div>
          </div>

          <div className="absolute w-[280px] h-[280px] border border-cyan-500/10 rounded-full animate-[spin_15s_linear_infinite]">
            <div className="absolute w-2 h-2 bg-cyan-400 rounded-full shadow-[0_0_15px_#00f0ff] -mt-1" style={{ left: '100%', top: '50%', transform: 'translate(-50%, -50%)' }}></div>
          </div>

          <div className="absolute w-[400px] h-[400px] border border-indigo-500/10 rounded-full animate-[spin_30s_linear_infinite_reverse]">
            <div className="absolute w-4 h-4 rounded-full bg-black border border-indigo-500 flex items-center justify-center -mt-2 shadow-[0_0_20px_rgba(99,102,241,0.4)]" style={{ left: '50%', top: '0%', transform: 'translate(-50%, -50%)' }}>
              <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-pulse"></div>
            </div>
          </div>

          <div className="absolute top-20 right-10 animate-pulse text-xs font-mono text-cyan-500/50 text-right">
            Main Node: 46.225.62.76<br />
            Latência: 12ms
          </div>
          <div className="absolute bottom-32 left-10 text-left text-xs font-mono text-indigo-400/60">
            <span className="animate-pulse">/// POOL DE PROXIES ATIVO</span><br />
            Rota Confiável: US-East
          </div>
        </div>

        <div className="absolute bottom-0 w-full px-8 pb-4">
          <div className="flex justify-between items-end border-b border-white/10 pb-2 mb-2">
            <span className="text-xs font-display text-slate-400 tracking-widest text-shadow">VITAIS DO SISTEMA</span>
            <span className="text-xs font-mono text-cyan-400 animate-pulse">IDEAL</span>
          </div>
          <div className="relative h-16 w-full system-vitals-graph border border-white/5 bg-black/20 rounded overflow-hidden">
            <svg className="absolute bottom-0 left-0 w-full h-full" preserveAspectRatio="none">
              <path d="M0,50 Q20,50 40,30 T80,50 T120,50 T160,20 T200,50 L200,64 L0,64 Z" fill="rgba(0, 240, 255, 0.1)" stroke="none"></path>
              <path className="drop-shadow-[0_0_5px_#00f0ff]" d="M0,50 Q20,50 40,30 T80,50 T120,50 T160,20 T200,50 T240,50 T280,10 T320,50 T360,50 T400,60 T440,50 T480,50 T520,30 T560,50 L800,50" fill="none" stroke="#00f0ff" strokeWidth="1.5" vectorEffect="non-scaling-stroke">
                <animate attributeName="d" dur="3s" repeatCount="indefinite" values="M0,50 Q20,50 40,30 T80,50 T120,50 T160,20 T200,50 T240,50 T280,10 T320,50 T360,50 T400,60 T440,50 T480,50 T520,30 T560,50 L800,50;
                                                           M0,50 Q20,55 40,40 T80,50 T120,50 T160,35 T200,50 T240,55 T280,25 T320,50 T360,55 T400,50 T440,50 T480,55 T520,40 T560,50 L800,50;
                                                           M0,50 Q20,50 40,30 T80,50 T120,50 T160,20 T200,50 T240,50 T280,10 T320,50 T360,50 T400,60 T440,50 T480,50 T520,30 T560,50 L800,50"></animate>
              </path>
            </svg>
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/10 to-transparent animate-pulse-transmission" style={{ animationDuration: '4s' }}></div>
          </div>
        </div>
      </div>

      {/* Right Column: Logs & Allocation */}
      <div className="col-span-12 xl:col-span-3 flex flex-col gap-6 h-full relative z-20">
        <div className="connection-line top-[20%] left-[-24px] w-[24px]">
          <div className="pulse-packet" style={{ animationDelay: '1.5s', animationDirection: 'reverse' }}></div>
        </div>

        <div className="flex-1 relative overflow-hidden flex flex-col justify-center items-center min-h-[300px]">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-900/10 to-transparent pointer-events-none z-0"></div>
          <div className="text-center mb-4 relative z-10">
            <h3 className="text-cyan-400 font-display font-bold tracking-[0.2em] text-sm uppercase glow-text">Log do Sistema</h3>
            <div className="text-[9px] text-indigo-400 font-mono">PROJEÇÃO HOLOGRÁFICA</div>
          </div>

          <div className="holographic-log-container w-full h-[400px] relative flex items-center justify-center">
            <div className="absolute bottom-10 w-40 h-10 bg-cyan-500/20 rounded-[100%] blur-xl animate-pulse"></div>

            <div className="holographic-log-cylinder absolute w-[240px] h-[300px]">
              <div className="absolute inset-0 overflow-hidden rounded-lg">
                <div className="particle" style={{ left: '20%', width: '2px', height: '2px', animationDuration: '3s', animationDelay: '0s' }}></div>
                <div className="particle" style={{ left: '50%', width: '3px', height: '3px', animationDuration: '5s', animationDelay: '1s' }}></div>
                <div className="particle" style={{ left: '80%', width: '2px', height: '2px', animationDuration: '4s', animationDelay: '2s' }}></div>
                <div className="particle" style={{ left: '30%', width: '2px', height: '2px', animationDuration: '6s', animationDelay: '0.5s' }}></div>
              </div>
              <div className="absolute inset-0 flex flex-col items-center justify-center space-y-6">
                <div className="w-[200px] bg-cyan-900/20 border border-cyan-500/30 p-3 backdrop-blur-sm transform hover:scale-105 transition-all shadow-glow-cyan">
                  <div className="flex justify-between text-[9px] font-mono text-cyan-300 mb-1 border-b border-cyan-500/20 pb-1">
                    <span>[SYS_AUT]</span>
                    <span>10:42:01</span>
                  </div>
                  <div className="text-[11px] text-white drop-shadow-[0_0_3px_rgba(0,240,255,0.8)]">Sessão validada para @opiniao_viral.</div>
                </div>
                <div className="w-[190px] bg-black/40 border border-indigo-500/30 p-3 backdrop-blur-sm opacity-90 hover:opacity-100 transition-opacity">
                  <div className="flex justify-between text-[9px] font-mono text-indigo-300 mb-1 pb-1">
                    <span>[NET_WARN]</span>
                    <span>10:42:15</span>
                  </div>
                  <div className="text-[11px] text-slate-300">Proxy US-East-1 apresentando lentidão.</div>
                </div>
                <div className="w-[180px] bg-magenta-900/10 border border-magenta-500/30 p-3 backdrop-blur-sm opacity-70 hover:opacity-100 transition-opacity">
                  <div className="flex justify-between text-[9px] font-mono text-magenta-300 mb-1 pb-1">
                    <span>[JOB_OK]</span>
                    <span>10:42:44</span>
                  </div>
                  <div className="text-[11px] text-magenta-100">Vídeo VCL_2393 publicado em @vibe.cortes!</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="h-1/3 atmospheric-glass p-4 rounded-sm flex flex-col justify-between relative overflow-hidden transition-all hover:bg-white/5 min-h-[180px]">
          <div className="absolute top-0 left-0 w-8 h-8 border-t border-l border-cyan-500/50"></div>
          <div>
            <h4 className="text-xs font-mono text-slate-400 uppercase mb-3 tracking-wider">Alocação de Recursos</h4>
            <div className="flex items-center gap-2 mb-2 group">
              <div className="text-sm font-bold text-white w-12 group-hover:text-cyan-400 transition-colors">CPU</div>
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-cyan-500 w-[45%] shadow-[0_0_10px_#00f0ff]"></div>
              </div>
              <span className="text-xs font-mono text-cyan-400">45%</span>
            </div>
            <div className="flex items-center gap-2 mb-2 group">
              <div className="text-sm font-bold text-white w-12 group-hover:text-indigo-400 transition-colors">MEM</div>
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 w-[72%] shadow-[0_0_10px_#6366f1]"></div>
              </div>
              <span className="text-xs font-mono text-indigo-400">72%</span>
            </div>
            <div className="flex items-center gap-2 group">
              <div className="text-sm font-bold text-white w-12 group-hover:text-emerald-400 transition-colors">NET</div>
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 w-[12%] shadow-[0_0_10px_#10b981]"></div>
              </div>
              <span className="text-xs font-mono text-emerald-400">12%</span>
            </div>
          </div>

          <div className="mt-4 p-2 bg-black/40 border border-white/5 rounded text-[10px] font-mono text-slate-400 relative overflow-hidden">
            <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-cyan-500"></div>
            <div className="pl-2">
              <div className="opacity-70">&gt; Otimizando threads de trabalho...</div>
              <div className="opacity-70">&gt; Limpando buffers de cache...</div>
              <div className="text-cyan-400 animate-pulse font-bold mt-1">&gt; SISTEMA IDEAL</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
