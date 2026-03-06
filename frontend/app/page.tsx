'use client';
import React, { useState, useRef, useEffect } from 'react';

interface TerminalLog {
  id: number;
  type: 'system' | 'warn' | 'error' | 'user' | 'success';
  text: string;
  time: string;
}

export default function Home() {
  const [logs, setLogs] = useState<TerminalLog[]>([
    { id: 1, type: 'system', text: 'Sequência Alfa iniciada.', time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) },
    { id: 2, type: 'warn', text: 'Pico de latência no Nó_7.', time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }
  ]);
  const [inputVal, setInputVal] = useState('');

  const addLog = (type: TerminalLog['type'], text: string) => {
    setLogs(prev => {
      const newLogs = [...prev, {
        id: Date.now(),
        type,
        text,
        time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      }];
      // Keep only last 3 to fit the 3D cylinder
      if (newLogs.length > 3) return newLogs.slice(newLogs.length - 3);
      return newLogs;
    });
  };

  const handleCommandSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    const cmd = inputVal.trim();
    addLog('user', `> ${cmd}`);
    setInputVal('');

    if (cmd.toLowerCase() === '/clear') {
      setLogs([]);
      return;
    }

    try {
      const API = typeof window !== 'undefined' ? localStorage.getItem('backend_url') || 'http://localhost:8000' : 'http://localhost:8000';
      const res = await fetch(`${API}/api/v1/debug/cli`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
      });

      if (!res.ok) throw new Error(`Falha na API: ${res.status}`);

      const data = await res.json();

      // Delay printing each line for a "terminal-like" feel
      data.lines.forEach((line: any, index: number) => {
        setTimeout(() => addLog(line.type, line.text), 150 * (index + 1));
      });

    } catch (err: any) {
      setTimeout(() => addLog('error', `Falha de Conecxão Node_1: ${err.message}`), 300);
    }
  };

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
            <span className="text-xs font-mono text-cyan-500/60 uppercase tracking-widest">Taxa de Produção</span>
            <span className="material-symbols-outlined text-white/20 group-hover:text-cyan-400 transition-colors animate-pulse">speed</span>
          </div>
          <div className="text-3xl font-display font-bold text-white mb-1 drop-shadow-[0_0_8px_rgba(0,240,255,0.3)]">
            27.400 <span className="text-lg text-slate-500 font-normal">v/h</span>
          </div>
          <div className="text-xs font-mono text-emerald-400 flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">arrow_upward</span> Delta-V Ideal
          </div>
          <div className="absolute top-0 left-0 w-2 h-2 border-l border-t border-cyan-500/50"></div>
          <div className="absolute bottom-0 right-0 w-2 h-2 border-r border-b border-cyan-500/50"></div>
        </div>

        <div className="atmospheric-glass p-5 rounded-sm relative group overflow-hidden hover:bg-white/5 transition-all">
          <div className="absolute inset-0 bg-gradient-to-br from-magenta-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex justify-between items-start mb-4 relative z-10">
            <span className="text-xs font-mono text-magenta-500/60 uppercase tracking-widest">Integridade dos Perfis</span>
            <span className="material-symbols-outlined text-white/20 group-hover:text-magenta-400 transition-colors">shield</span>
          </div>
          <div className="text-3xl font-display font-bold text-white mb-1 drop-shadow-[0_0_8px_rgba(255,0,85,0.3)]">
            99.8 <span className="text-lg text-slate-500 font-normal">%</span>
          </div>
          <div className="w-full bg-slate-800/50 h-1 mt-2 rounded-full overflow-hidden">
            <div className="bg-gradient-to-r from-magenta-600 to-purple-500 h-full w-[99.8%] shadow-[0_0_20px_rgba(255,0,85,0.3)] relative">
              <div className="absolute top-0 right-0 h-full w-2 bg-white/80 blur-[2px] animate-pulse"></div>
            </div>
          </div>
        </div>

        <div className="atmospheric-glass flex-1 p-5 rounded-sm relative flex flex-col overflow-hidden hover:bg-white/5 transition-all min-h-[200px]">
          <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
            <span className="text-xs font-display font-bold text-white uppercase tracking-wider text-cyan-200">Crawlers Ativos</span>
            <span className="text-[10px] font-mono text-slate-500 animate-pulse">AUTO-CICLO</span>
          </div>
          <div className="space-y-3 font-mono text-xs overflow-y-auto pr-2 custom-scrollbar relative z-10">
            <div className="flex items-center justify-between p-2 bg-white/5 border-l-2 border-cyan-500 hover:bg-cyan-500/10 transition-colors cursor-pointer group/item">
              <div>
                <div className="text-cyan-300 font-bold group-hover/item:text-white group-hover/item:shadow-[0_0_10px_rgba(255,255,255,0.4)] transition-all">EXTR-alfa</div>
                <div className="text-slate-500 text-[10px]">TikTok // Scraper</div>
              </div>
              <div className="h-1.5 w-1.5 rounded-full bg-green-500 shadow-[0_0_8px_#22c55e] animate-pulse"></div>
            </div>
            <div className="flex items-center justify-between p-2 bg-white/5 border-l-2 border-slate-700 hover:bg-indigo-500/10 transition-colors cursor-pointer group/item">
              <div>
                <div className="text-slate-300 font-bold group-hover/item:text-white">EXTR-beta</div>
                <div className="text-slate-500 text-[10px]">YouTube // Ocioso</div>
              </div>
              <div className="h-1.5 w-1.5 rounded-full bg-yellow-500 shadow-[0_0_5px_#eab308]"></div>
            </div>
            <div className="flex items-center justify-between p-2 bg-white/5 border-l-2 border-magenta-500 hover:bg-magenta-500/10 transition-colors cursor-pointer group/item">
              <div>
                <div className="text-magenta-300 font-bold group-hover/item:text-white">EXTR-gama</div>
                <div className="text-slate-500 text-[10px]">Instagram // Bloqueado</div>
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

            <div className="text-center z-30 relative">
              <div className="text-[10px] font-mono text-cyan-300 tracking-[0.2em] mb-1 opacity-70">MOTOR LLM</div>
              <div className="text-4xl font-display font-bold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.8)] chromatic-text" data-text="84%">84%</div>
              <div className="text-[9px] font-mono text-indigo-300 mt-1">PROCESSAMENTO</div>
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
            CDN: CLOUDFLARE_EDGE<br />
            Lat: 12ms
          </div>
          <div className="absolute bottom-32 left-10 text-left text-xs font-mono text-indigo-400/60">
            <span className="animate-pulse">/// TRANSMISSÃO ATIVA</span><br />
            Perda Pacotes: 0.002%
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
              <div className="absolute inset-0 flex flex-col items-center justify-end pb-8 space-y-4">
                {logs.map((log) => {
                  let bgClass = "bg-cyan-900/20 border-cyan-500/30";
                  let textClass = "text-white drop-shadow-[0_0_3px_rgba(0,240,255,0.8)]";
                  let headerClass = "text-cyan-300 border-cyan-500/20";
                  let tag = "[SYS_INIT]";
                  let width = "w-[200px]";

                  if (log.type === 'warn') {
                    bgClass = "bg-black/40 border-indigo-500/30";
                    textClass = "text-slate-300";
                    headerClass = "text-indigo-300 border-indigo-500/20";
                    tag = "[NET_WARN]";
                    width = "w-[190px]";
                  } else if (log.type === 'error') {
                    bgClass = "bg-magenta-900/10 border-magenta-500/30";
                    textClass = "text-magenta-100";
                    headerClass = "text-magenta-300 border-magenta-500/20";
                    tag = "[ERR_CRIT]";
                    width = "w-[180px]";
                  } else if (log.type === 'success') {
                    bgClass = "bg-emerald-900/20 border-emerald-500/30";
                    textClass = "text-emerald-100";
                    headerClass = "text-emerald-400 border-emerald-500/20";
                    tag = "[SYS_OK]";
                    width = "w-[200px]";
                  } else if (log.type === 'user') {
                    bgClass = "bg-white/5 border-white/20";
                    textClass = "text-white";
                    headerClass = "text-slate-400 border-white/10";
                    tag = "[USER_CMD]";
                    width = "w-[210px]";
                  }

                  return (
                    <div key={log.id} className={`${width} ${bgClass} border p-3 backdrop-blur-sm transform transition-all animate-in fade-in slide-in-from-bottom-5`}>
                      <div className={`flex justify-between text-[9px] font-mono ${headerClass} mb-1 border-b pb-1`}>
                        <span>{tag}</span>
                        <span>{log.time}</span>
                      </div>
                      <div className={`text-[11px] ${textClass}`}>{log.text}</div>
                    </div>
                  );
                })}
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

          <form onSubmit={handleCommandSubmit} className="mt-4 flex items-center bg-black/40 border border-white/5 rounded relative overflow-hidden group focus-within:border-cyan-500/50 transition-colors">
            <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-cyan-500 group-focus-within:shadow-[0_0_10px_#00f0ff] transition-shadow"></div>
            <div className="pl-3 pr-2 py-2 flex items-center w-full">
              <span className="text-cyan-400 font-bold mr-2 textxs font-mono">&gt;</span>
              <input
                type="text"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                className="bg-transparent border-none outline-none text-cyan-50 text-xs font-mono w-full placeholder:text-cyan-900 focus:ring-0"
                placeholder="Digite /help para comandos..."
              />
            </div>
          </form>
        </div>

      </div>
    </div>
  );
}
