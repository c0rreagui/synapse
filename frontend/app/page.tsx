'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

// Interface defined but used for type safety if needed in future
interface Profile {
  id: string;
  label: string;
}

export default function Home() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    return pathname === href || pathname?.startsWith(href);
  };

  return (
    <>
      <div className="fixed inset-0 z-0 bg-[#050507]"></div>
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[150px] rounded-full opacity-40 pointer-events-none"></div>
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/10 blur-[150px] rounded-full opacity-30 pointer-events-none"></div>
      <div className="absolute inset-0 z-0 synapse-grid bg-grid-pattern opacity-20 pointer-events-none"></div>
      <div className="absolute top-0 left-0 w-full h-[600px] bg-synapse-gradient opacity-60 pointer-events-none z-0"></div>

      <div className="flex h-screen w-full relative z-10">
        {/* Sidebar - Added sidebar-desktop class */}
        <div className="hidden md:flex sidebar-desktop shrink-0 flex-col w-[288px] min-w-[288px] border-r border-white/5 bg-[#050507]/80 backdrop-blur-3xl p-6 justify-between h-full relative z-50">
          <div className="flex flex-col gap-8">
            <div className="flex items-center gap-3 px-2 py-2">
              <div className="size-10 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-[0_0_20px_rgba(139,85,247,0.4)] relative overflow-hidden group">
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                <span className="material-symbols-outlined text-white text-[24px]">neurology</span>
              </div>
              <div className="flex flex-col">
                <h1 className="text-white text-lg font-bold tracking-tight font-display">SYNAPSE</h1>
                <p className="text-primary/60 text-[10px] font-mono tracking-[0.2em]">ORCHESTRATOR_V4</p>
              </div>
            </div>

            <nav className="flex flex-col gap-1.5">
              <p className="px-4 text-[10px] font-bold text-[#475569] uppercase tracking-wider mb-2 font-mono">Operations</p>
              <Link href="/" className={`flex items-center gap-3 px-4 py-3 rounded-lg group relative overflow-hidden ${isActive('/') ? 'nav-item-active text-white' : 'text-[#94a3b8] hover:text-white transition-colors'}`}>
                {isActive('/') && <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>}
                {!isActive('/') && <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>}
                <span className={`material-symbols-outlined text-[20px] ${isActive('/') ? 'text-primary drop-shadow-[0_0_8px_rgba(139,85,247,0.8)]' : 'group-hover:text-primary transition-colors'}`}>dashboard</span>
                <span className="text-sm font-medium tracking-wide">Command Center</span>
              </Link>
              <Link href="/profiles" className={`flex items-center gap-3 px-4 py-3 rounded-lg group relative overflow-hidden ${isActive('/profiles') ? 'nav-item-active text-white' : 'text-[#94a3b8] hover:text-white transition-colors'}`}>
                {isActive('/profiles') && <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>}
                {!isActive('/profiles') && <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>}
                <span className={`material-symbols-outlined text-[20px] ${isActive('/profiles') ? 'text-primary drop-shadow-[0_0_8px_rgba(139,85,247,0.8)]' : 'group-hover:text-primary transition-colors'}`}>folder_open</span>
                <span className="text-sm font-medium tracking-wide">Dark Profiles</span>
              </Link>
              <Link href="/metrics" className="flex items-center gap-3 px-4 py-3 rounded-lg text-[#94a3b8] hover:text-white group relative overflow-hidden transition-colors">
                <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <span className="material-symbols-outlined text-[20px] group-hover:text-primary transition-colors">show_chart</span>
                <span className="text-sm font-medium tracking-wide">Growth Metrics</span>
              </Link>

              <p className="px-4 text-[10px] font-bold text-[#475569] uppercase tracking-wider mb-2 mt-6 font-mono">Neural Net</p>
              <Link href="/nodes" className="flex items-center gap-3 px-4 py-3 rounded-lg text-[#94a3b8] hover:text-white group relative overflow-hidden transition-colors">
                <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <span className="material-symbols-outlined text-[20px] group-hover:text-primary transition-colors">hub</span>
                <span className="text-sm font-medium tracking-wide">Node Matrix</span>
              </Link>
              <Link href="/integrations" className="flex items-center gap-3 px-4 py-3 rounded-lg text-[#94a3b8] hover:text-white group relative overflow-hidden transition-colors">
                <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <span className="material-symbols-outlined text-[20px] group-hover:text-primary transition-colors">settings_input_component</span>
                <span className="text-sm font-medium tracking-wide">Integrations</span>
              </Link>
            </nav>
          </div>
          <div className="glass-panel rounded-xl p-3 flex items-center gap-3 border border-white/5 hover:border-primary/30 transition-all cursor-pointer group">
            <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-lg size-9 ring-1 ring-white/10 group-hover:ring-primary/50 transition-all bg-[url('https://lh3.googleusercontent.com/aida-public/AB6AXuBmtFcygHM-XjbaE1KOGTW22gTuqgmMV8naX8HCJq3IrwMXLY7ds26yarLQV2hF_E53X7KY2HT4Eh7u3NFFnRATricFSIFz74RDb_06RxqpwVjck5BYOgImaDzzelNNsr0L3H3dZgBs0JqsQPc9irH3hxlfw17tpfr2WC0v5d6fNVESWFA3JyMTFYSM8O2hrvOfQOWUyoCwFtq4tLnvVr8Pu6I85lOTej-RpTBmoXk7tgG39tcbcXPayz_sjX-4bbGTZGETMjoLUQ')]"></div>
            <div className="flex flex-col min-w-0">
              <p className="text-sm font-medium text-white truncate group-hover:text-primary transition-colors">Administrator</p>
              <p className="text-[10px] font-mono text-[#64748b] truncate">SYS_ADMIN_01</p>
            </div>
            <span className="material-symbols-outlined text-[#64748b] ml-auto text-lg group-hover:text-white transition-colors">more_vert</span>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col h-full overflow-hidden relative">
          <header className="flex items-center justify-between border-b border-white/5 bg-[#050507]/80 backdrop-blur-md px-8 py-4 z-40 sticky top-0">
            <div className="flex items-center gap-4">
              <h2 className="text-white text-xl font-bold leading-tight tracking-tight flex items-center gap-3">
                <span className="material-symbols-outlined text-primary shadow-primary drop-shadow-[0_0_10px_rgba(139,85,247,0.5)]">space_dashboard</span>
                Command Center
              </h2>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3 bg-[#0a0a0e] border border-white/10 rounded-full pl-2 pr-4 py-1.5 shadow-[inset_0_2px_4px_rgba(0,0,0,0.5)]">
                <div className="relative flex items-center justify-center size-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                  <span className="relative inline-flex rounded-full size-2 bg-success shadow-[0_0_8px_#0bda6f]"></span>
                </div>
                <span className="text-[10px] font-mono text-success/80 tracking-wide uppercase neon-text">System Active</span>
              </div>
              <div className="h-5 w-px bg-white/10"></div>
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

          <main className="flex-1 overflow-y-auto custom-scrollbar p-6 lg:p-8">
            <div className="max-w-[1800px] mx-auto flex flex-col gap-6">
              <div className="flex justify-between items-end mb-2">
                <div className="flex flex-col gap-1">
                  <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                    Network Telemetry
                    <span className="w-16 h-[1px] bg-gradient-to-r from-primary/50 to-transparent"></span>
                  </h3>
                </div>
                <div className="flex gap-2">
                  <span className="text-[10px] font-mono text-primary/80 bg-primary/5 px-2 py-1 rounded border border-primary/20">v.3.4.1-stable</span>
                </div>
              </div>

              {/* Telemetry Grid - Added grid-telemetry class */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 grid-telemetry gap-6">
                <div className="glass-panel rounded-2xl p-6 group">
                  <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-all transform group-hover:scale-110 duration-500">
                    <span className="material-symbols-outlined text-8xl text-primary">layers</span>
                  </div>
                  <div className="relative z-10 flex flex-col h-full justify-between gap-4">
                    <div className="flex items-center gap-3 text-[#94a3b8]">
                      <div className="p-2 rounded-lg bg-white/5 border border-white/5 shadow-inner">
                        <span className="material-symbols-outlined text-primary text-xl">layers</span>
                      </div>
                      <span className="text-xs font-mono font-medium uppercase tracking-wider text-white/60">Pending Clips</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-white tracking-tighter tabular-nums drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">14</span>
                      <span className="text-xs font-mono text-[#94a3b8]">in queue</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono font-medium text-warning bg-warning/5 border border-warning/10 self-start px-2 py-1 rounded">
                      <span className="material-symbols-outlined text-sm">trending_up</span>
                      HIGH LOAD
                    </div>
                  </div>
                  <div className="data-flow-line opacity-50"></div>
                </div>
                <div className="glass-panel rounded-2xl p-6 group">
                  <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-all transform group-hover:scale-110 duration-500">
                    <span className="material-symbols-outlined text-8xl text-success">rocket_launch</span>
                  </div>
                  <div className="relative z-10 flex flex-col h-full justify-between gap-4">
                    <div className="flex items-center gap-3 text-[#94a3b8]">
                      <div className="p-2 rounded-lg bg-white/5 border border-white/5 shadow-inner">
                        <span className="material-symbols-outlined text-success text-xl">rocket_launch</span>
                      </div>
                      <span className="text-xs font-mono font-medium uppercase tracking-wider text-white/60">Deployed Today</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-white tracking-tighter tabular-nums drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">32</span>
                      <span className="text-xs font-mono text-[#94a3b8]">clips</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono font-medium text-success bg-success/5 border border-success/10 self-start px-2 py-1 rounded">
                      <span className="material-symbols-outlined text-sm">arrow_upward</span>
                      +12% EFFICIENCY
                    </div>
                  </div>
                  <div className="data-flow-line opacity-50 delay-1000"></div>
                </div>
                <div className="glass-panel rounded-2xl p-6 group">
                  <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-all transform group-hover:scale-110 duration-500">
                    <span className="material-symbols-outlined text-8xl text-secondary">memory</span>
                  </div>
                  <div className="relative z-10 flex flex-col h-full justify-between gap-4">
                    <div className="flex items-center gap-3 text-[#94a3b8]">
                      <div className="p-2 rounded-lg bg-white/5 border border-white/5 shadow-inner">
                        <span className="material-symbols-outlined text-secondary text-xl">memory</span>
                      </div>
                      <span className="text-xs font-mono font-medium uppercase tracking-wider text-white/60">Compute Nodes</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-white tracking-tighter tabular-nums drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">4m 20s</span>
                      <span className="text-xs font-mono text-[#94a3b8]">avg time</span>
                    </div>
                    <div className="h-6 flex items-end gap-1 mt-auto">
                      <div className="w-full bg-secondary/20 h-[30%] rounded-sm"></div>
                      <div className="w-full bg-secondary/30 h-[50%] rounded-sm"></div>
                      <div className="w-full bg-secondary/40 h-[40%] rounded-sm"></div>
                      <div className="w-full bg-secondary/60 h-[70%] rounded-sm"></div>
                      <div className="w-full bg-secondary/50 h-[60%] rounded-sm"></div>
                      <div className="w-full bg-secondary h-[85%] rounded-sm shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
                      <div className="w-full bg-secondary/40 h-[55%] rounded-sm"></div>
                    </div>
                  </div>
                  <div className="data-flow-line opacity-50 delay-500"></div>
                </div>
              </div>

              {/* Main Grid: Radar + Neural Health - Added grid-main class */}
              <div className="grid grid-cols-1 lg:grid-cols-3 grid-main gap-6 h-[600px]">
                {/* Watch Folder Matrix (Radar) - Added col-span-2-desktop */}
                <div className="lg:col-span-2 col-span-2-desktop glass-panel rounded-2xl p-0 relative flex flex-col border-t border-t-white/10 overflow-hidden">
                  <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-start z-30 pointer-events-none">
                    <div className="pointer-events-auto">
                      <h3 className="text-lg font-bold text-white flex items-center gap-3 font-display">
                        <span className="flex size-2 rounded-full bg-success shadow-[0_0_10px_#00ff9d] animate-pulse"></span>
                        Watch Folder Matrix
                      </h3>
                      <div className="flex items-center gap-2 mt-2">
                        <p className="text-[10px] text-[#94a3b8] font-mono tracking-wide bg-black/40 px-2 py-0.5 rounded border border-white/5">PATH: /mnt/data/ingest/*.mp4</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/5 border border-success/20 backdrop-blur-md text-success text-[10px] font-bold uppercase tracking-wider shadow-[0_0_15px_rgba(0,255,157,0.1)]">
                      <span className="material-symbols-outlined text-sm animate-spin">sync</span>
                      Live Scanning
                    </div>
                  </div>

                  {/* Radar Visualization Container */}
                  <div className="flex-1 relative flex items-center justify-center overflow-hidden bg-[#030304] min-h-[400px]">
                    {/* SVG Connection Lines */}
                    <svg className="absolute inset-0 w-full h-full z-10 pointer-events-none">
                      <defs>
                        <linearGradient id="lineGradient" x1="0%" x2="100%" y1="0%" y2="0%">
                          <stop offset="0%" stopColor="rgba(139, 85, 247, 0.0)"></stop>
                          <stop offset="50%" stopColor="rgba(139, 85, 247, 0.4)"></stop>
                          <stop offset="100%" stopColor="rgba(139, 85, 247, 0.0)"></stop>
                        </linearGradient>
                      </defs>
                      <line className="connection-line" stroke="url(#lineGradient)" strokeWidth="1" x1="50%" x2="25%" y1="50%" y2="25%"></line>
                      <line className="connection-line delay-[-15s]" stroke="url(#lineGradient)" strokeWidth="1" x1="50%" x2="80%" y1="50%" y2="70%"></line>
                      <circle cx="50%" cy="50%" fill="none" r="225" stroke="rgba(255,255,255,0.03)" strokeDasharray="4 4" strokeWidth="1"></circle>
                    </svg>
                    <div className="absolute inset-0 opacity-30 bg-[radial-gradient(rgba(139,85,247,0.05)_1px,transparent_1px)] [background-size:30px_30px]"></div>

                    {/* Radar Rings - Converted from inline styles to Tailwind classes */}
                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] border border-white/5 rounded-full"></div>
                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[450px] h-[450px] border border-dashed border-white/5 rounded-full animate-spin [animation-duration:60s]"></div>
                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] border border-primary/20 rounded-full shadow-[0_0_30px_rgba(139,85,247,0.1)]"></div>

                    {/* Center Hub */}
                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[160px] h-[160px] flex items-center justify-center z-20">
                      <div className="absolute inset-0 rounded-full border border-primary/30 border-t-primary/80 animate-spin-slow"></div>
                      <div className="absolute inset-2 rounded-full border border-secondary/30 border-b-secondary/80 animate-reverse-spin"></div>
                      <div className="w-[100px] h-[100px] rounded-full bg-[#050507] border border-primary/50 shadow-[0_0_50px_rgba(139,85,247,0.4)] flex items-center justify-center relative overflow-hidden group cursor-pointer hover:scale-105 transition-transform">
                        <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-secondary/20 animate-pulse"></div>
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white/10 via-transparent to-transparent opacity-50"></div>
                        <span className="material-symbols-outlined text-5xl text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.9)] relative z-10">neurology</span>
                        <div className="absolute w-full h-[1px] bg-primary/50 top-1/2 animate-ping opacity-20"></div>
                        <div className="absolute h-full w-[1px] bg-primary/50 left-1/2 animate-ping opacity-20 delay-500"></div>
                      </div>
                      <div className="absolute inset-[-10px] animate-spin-slow [animation-duration:8s]">
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_10px_white]"></div>
                      </div>
                    </div>

                    {/* Radar Scan Beam */}
                    <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full animate-scan-rotate radar-scan-beam opacity-40 pointer-events-none"></div>

                    {/* File Node 1 */}
                    <div className="absolute top-[25%] left-[25%] flex flex-col items-center gap-3 animate-float z-30 group cursor-pointer">
                      <div className="relative">
                        <div className="absolute -inset-2 rounded-xl bg-primary/20 blur-md opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div className="bg-[#0f0f13] border border-primary/40 text-white p-3 rounded-xl shadow-[0_0_20px_rgba(139,85,247,0.2)] group-hover:border-primary group-hover:shadow-[0_0_30px_rgba(139,85,247,0.5)] transition-all relative">
                          <span className="material-symbols-outlined text-2xl">movie</span>
                          <div className="absolute -top-1 -right-1 size-3 bg-success rounded-full shadow-[0_0_8px_#00ff9d] border-2 border-[#0f0f13]"></div>
                        </div>
                      </div>
                      <div className="flex flex-col items-center gap-1">
                        <div className="text-[10px] text-white bg-black/80 backdrop-blur px-2 py-0.5 rounded border border-white/10 font-mono tracking-wider">clip_22.mp4</div>
                        <div className="text-[8px] text-success font-mono uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">Ready to Deploy</div>
                      </div>
                    </div>

                    {/* File Node 2 */}
                    <div className="absolute bottom-[30%] right-[20%] flex flex-col items-center gap-3 animate-float-delayed z-30 group cursor-pointer">
                      <div className="relative">
                        <div className="absolute -inset-2 rounded-xl bg-primary/20 blur-md opacity-0 group-hover:opacity-100 transition-opacity"></div>
                        <div className="bg-[#0f0f13] border border-primary/40 text-white p-3 rounded-xl shadow-[0_0_20px_rgba(139,85,247,0.2)] group-hover:border-primary group-hover:shadow-[0_0_30px_rgba(139,85,247,0.5)] transition-all relative">
                          <span className="material-symbols-outlined text-2xl">movie</span>
                          <div className="absolute -top-1 -right-1 size-3 bg-success rounded-full shadow-[0_0_8px_#00ff9d] border-2 border-[#0f0f13]"></div>
                        </div>
                      </div>
                      <div className="flex flex-col items-center gap-1">
                        <div className="text-[10px] text-white bg-black/80 backdrop-blur px-2 py-0.5 rounded border border-white/10 font-mono tracking-wider">promo_v3.mp4</div>
                        <div className="text-[8px] text-success font-mono uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity">Processing</div>
                      </div>
                    </div>

                    {/* Scanning Indicator */}
                    <div className="absolute top-[20%] right-[30%] flex flex-col items-center gap-2 animate-pulse-slow z-20 opacity-60">
                      <div className="size-2 bg-warning rounded-full shadow-[0_0_10px_#fa6c38]"></div>
                      <span className="text-[9px] font-mono text-warning tracking-wider">SCANNING_NEW_FILES...</span>
                    </div>
                  </div>

                  {/* Ingestion Log Overlay */}
                  <div className="mt-auto z-30 bg-gradient-to-t from-[#050507] via-[#050507]/90 to-transparent p-6 pt-16 pointer-events-none">
                    <div className="glass-panel p-3 rounded-xl border border-white/5 pointer-events-auto w-full max-w-sm ml-auto mr-0 backdrop-blur-xl">
                      <div className="flex items-center gap-2 mb-3 px-1 border-b border-white/5 pb-2">
                        <span className="size-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_5px_#8b55f7]"></span>
                        <span className="text-[10px] font-bold text-white uppercase tracking-widest font-mono">Ingestion Log</span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs p-2 rounded hover:bg-white/5 transition-colors cursor-default group">
                          <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-sm text-primary">downloading</span>
                            <span className="text-gray-200 font-mono text-[11px] group-hover:text-white transition-colors">interview_raw_04.mp4</span>
                          </div>
                          <span className="text-[#64748b] font-mono text-[10px]">2s ago</span>
                        </div>
                        <div className="flex items-center justify-between text-xs p-2 rounded hover:bg-white/5 transition-colors cursor-default opacity-60 hover:opacity-100">
                          <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-sm text-success">check_circle</span>
                            <span className="text-gray-200 font-mono text-[11px]">social_cut_01.mp4</span>
                          </div>
                          <span className="text-[#64748b] font-mono text-[10px]">45s ago</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Neural Health Panel */}
                <div className="flex flex-col gap-6 h-full">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <span className="material-symbols-outlined text-success">monitor_heart</span>
                      Neural Health
                    </h3>
                    <button className="text-[10px] font-mono text-primary hover:text-white transition-colors uppercase tracking-wider">View All Nodes</button>
                  </div>

                  <div className="flex flex-col gap-4 flex-1">
                    {/* YouTube */}
                    <div className="glass-panel p-4 rounded-xl flex items-center justify-between group hover:border-primary/40 transition-all cursor-pointer">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="size-10 rounded-lg bg-red-500/10 flex items-center justify-center text-red-500 border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.1)] group-hover:shadow-[0_0_25px_rgba(239,68,68,0.3)] transition-shadow">
                            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"></path></svg>
                          </div>
                          <div className="absolute -bottom-1 -right-1 size-2.5 bg-[#050507] rounded-full flex items-center justify-center">
                            <div className="size-1.5 bg-success rounded-full shadow-[0_0_5px_#00ff9d]"></div>
                          </div>
                        </div>
                        <div>
                          <h4 className="text-white font-semibold text-sm">YouTube Shorts</h4>
                          <span className="text-[9px] font-mono text-[#94a3b8] uppercase tracking-wide">API Connected</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex flex-col items-end">
                          <span className="text-xs font-mono text-success">45ms</span>
                          <div className="flex gap-0.5 mt-1">
                            <div className="w-1 h-2 bg-success rounded-sm"></div>
                            <div className="w-1 h-2 bg-success rounded-sm"></div>
                            <div className="w-1 h-2 bg-success/30 rounded-sm"></div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* LinkedIn */}
                    <div className="glass-panel p-4 rounded-xl flex items-center justify-between group hover:border-secondary/40 transition-all cursor-pointer">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="size-10 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary border border-secondary/20 shadow-[0_0_15px_rgba(59,130,246,0.1)] group-hover:shadow-[0_0_25px_rgba(59,130,246,0.3)] transition-shadow">
                            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"></path></svg>
                          </div>
                          <div className="absolute -bottom-1 -right-1 size-2.5 bg-[#050507] rounded-full flex items-center justify-center">
                            <div className="size-1.5 bg-idle rounded-full"></div>
                          </div>
                        </div>
                        <div>
                          <h4 className="text-white font-semibold text-sm">LinkedIn Video</h4>
                          <span className="text-[9px] font-mono text-[#94a3b8] uppercase tracking-wide">Awaiting Token</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <button className="text-[9px] bg-idle/10 text-idle px-2 py-1 rounded border border-idle/20 hover:bg-idle/20 transition-colors uppercase font-mono tracking-wider">Refresh</button>
                      </div>
                    </div>

                    {/* TikTok */}
                    <div className="glass-panel p-4 rounded-xl flex items-center justify-between group hover:border-pink-500/40 transition-all cursor-pointer">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="size-10 rounded-lg bg-pink-500/10 flex items-center justify-center text-pink-500 border border-pink-500/20 shadow-[0_0_15px_rgba(236,72,153,0.1)] group-hover:shadow-[0_0_25px_rgba(236,72,153,0.3)] transition-shadow">
                            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93v6.16c0 2.52-1.12 4.84-2.9 6.24-1.72 1.36-4.04 1.86-6.23 1.3-3.17-.79-5.35-3.66-5.32-6.9-.02-3.4 2.59-6.31 5.96-6.66 1.43-.16 2.87.16 4.15.86v4.06c-1.21-.86-2.89-.9-4.13-.12-1.56.96-2.02 2.99-1.07 4.56.94 1.57 2.97 2.05 4.53 1.12.87-.52 1.41-1.45 1.41-2.47v-16.2z"></path></svg>
                          </div>
                          <div className="absolute -bottom-1 -right-1 size-2.5 bg-[#050507] rounded-full flex items-center justify-center">
                            <div className="size-1.5 bg-success rounded-full shadow-[0_0_5px_#00ff9d]"></div>
                          </div>
                        </div>
                        <div>
                          <h4 className="text-white font-semibold text-sm">TikTok</h4>
                          <span className="text-[9px] font-mono text-[#94a3b8] uppercase tracking-wide">Ready for Upload</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="block text-[9px] text-[#64748b] uppercase font-mono tracking-wider">Queue</span>
                        <span className="text-sm font-bold text-white">Empty</span>
                      </div>
                    </div>

                    {/* System Alerts */}
                    <div className="glass-panel p-4 rounded-xl flex-1 flex flex-col gap-3 mt-auto border border-red-500/20 bg-red-900/5">
                      <div className="flex justify-between items-center border-b border-white/5 pb-2">
                        <h4 className="text-red-200 font-bold text-xs uppercase tracking-wider font-mono">System Alerts</h4>
                        <span className="size-1.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]"></span>
                      </div>
                      <div className="flex flex-col gap-2">
                        <div className="flex items-start gap-3 text-xs p-2 rounded bg-red-500/5 border border-red-500/10">
                          <span className="material-symbols-outlined text-sm text-red-500 mt-0.5">warning</span>
                          <div className="flex flex-col">
                            <span className="text-red-200 font-medium">Upload Timeout</span>
                            <span className="text-red-400/60 text-[10px] font-mono">ERR_504_GATEWAY</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}
