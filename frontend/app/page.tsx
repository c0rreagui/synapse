'use client';

import { useState, useEffect } from 'react';

// --- ICONS (Heroicons as fallback for Material Symbols where distinct, but favor Google Fonts Material in Head) ---
// Actually, the Reference uses Material Symbols via Google Fonts. I should ensure Layout.tsx loads them.
// I checked layout.tsx, it DOES load Material Symbols. So I will use <span class="material-symbols-outlined">...</span> directly.

export default function Home() {
  // --- STATE ---
  interface Profile { id: string; label: string }
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [isDragging, setIsDragging] = useState(false);
  const [activeTab, setActiveTab] = useState('command_center');

  // --- API ---
  useEffect(() => {
    async function fetchProfiles() {
      try {
        const res = await fetch('http://localhost:8001/api/v1/profiles/list');
        if (res.ok) {
          const data = await res.json();
          setProfiles(data);
          if (data.length > 0) setSelectedProfile(data[0].id);
        }
      } catch (error) {
        console.error("Erro API", error);
        setProfiles([{ id: "offline", label: "Backend Offline" }]);
      }
    }
    fetchProfiles();
  }, []);

  const handleUpload = async (file: File) => {
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append("file", file);
    formData.append("profile_key", selectedProfile);

    try {
      const response = await fetch("http://localhost:8001/api/v1/ingest/upload", {
        method: "POST",
        body: formData,
      });
      if (response.ok) setUploadStatus('success');
      else setUploadStatus('error');
      setTimeout(() => setUploadStatus('idle'), 3000);
    } catch {
      setUploadStatus('error');
    }
  };

  // --- DRAG HANDLERS ---
  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]);
  };

  // --- RENDER ---
  return (
    // Body classes are handled in layout.tsx, but we ensure main container matches Reference
    <div className="flex h-screen w-full relative z-10 overflow-hidden font-display text-slate-200 selection:bg-primary/30 selection:text-white">

      {/* BACKGROUND LAYERS (Reference Lines 146-150) */}
      <div className="fixed inset-0 z-0 bg-[#050507]"></div>
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[150px] rounded-full opacity-40 pointer-events-none"></div>
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/10 blur-[150px] rounded-full opacity-30 pointer-events-none"></div>
      <div className="absolute inset-0 z-0 synapse-grid bg-grid-pattern opacity-20 pointer-events-none"></div>
      <div className="absolute top-0 left-0 w-full h-[600px] bg-synapse-gradient opacity-40 pointer-events-none z-0"></div>

      {/* SIDEBAR (Reference Lines 152-202) */}
      <div className="hidden md:flex flex-col w-72 border-r border-white/5 bg-[#050507]/60 backdrop-blur-2xl p-4 justify-between h-full relative z-50 shrink-0">
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

            <a href="#" onClick={() => setActiveTab('command_center')} className={`flex items-center gap-3 px-4 py-3 rounded-lg text-white group relative overflow-hidden ${activeTab === 'command_center' ? 'nav-item-active' : 'text-[#94a3b8] hover:text-white'}`}>
              <div className={`absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity ${activeTab === 'command_center' ? 'opacity-100' : ''}`}></div>
              <span className={`material-symbols-outlined text-[20px] transition-colors ${activeTab === 'command_center' ? 'text-primary drop-shadow-[0_0_8px_rgba(139,85,247,0.8)]' : 'group-hover:text-primary'}`}>dashboard</span>
              <span className="text-sm font-medium tracking-wide">Command Center</span>
            </a>

            <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-lg text-[#94a3b8] hover:text-white group relative overflow-hidden transition-colors">
              <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="material-symbols-outlined text-[20px] group-hover:text-primary transition-colors">folder_open</span>
              <span className="text-sm font-medium tracking-wide">Dark Profiles</span>
            </a>

            <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-lg text-[#94a3b8] hover:text-white group relative overflow-hidden transition-colors">
              <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="material-symbols-outlined text-[20px] group-hover:text-primary transition-colors">show_chart</span>
              <span className="text-sm font-medium tracking-wide">Growth Metrics</span>
            </a>

            <p className="px-4 text-[10px] font-bold text-[#475569] uppercase tracking-wider mb-2 mt-6 font-mono">Neural Net</p>
            <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-lg text-[#94a3b8] hover:text-white group relative overflow-hidden transition-colors">
              <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <span className="material-symbols-outlined text-[20px] group-hover:text-primary transition-colors">hub</span>
              <span className="text-sm font-medium tracking-wide">Node Matrix</span>
            </a>
          </nav>
        </div>

        {/* User Profile */}
        <div className="glass-panel rounded-xl p-3 flex items-center gap-3 border border-white/5 hover:border-primary/30 transition-all cursor-pointer group">
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-lg size-9 ring-1 ring-white/10 group-hover:ring-primary/50 transition-all" style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBmtFcygHM-XjbaE1KOGTW22gTuqgmMV8naX8HCJq3IrwMXLY7ds26yarLQV2hF_E53X7KY2HT4Eh7u3NFFnRATricFSIFz74RDb_06RxqpwVjck5BYOgImaDzzelNNsr0L3H3dZgBs0JqsQPc9irH3hxlfw17tpfr2WC0v5d6fNVESWFA3JyMTFYSM8O2hrvOfQOWUyoCwFtq4tLnvVr8Pu6I85lOTej-RpTBmoXk7tgG39tcbcXPayz_sjX-4bbGTZGETMjoLUQ")' }}></div>
          <div className="flex flex-col min-w-0">
            <p className="text-sm font-medium text-white truncate group-hover:text-primary transition-colors">Administrator</p>
            <p className="text-[10px] font-mono text-[#64748b] truncate">SYS_ADMIN_01</p>
          </div>
          <span className="material-symbols-outlined text-[#64748b] ml-auto text-lg group-hover:text-white transition-colors">more_vert</span>
        </div>
      </div>

      {/* MAIN CONTENT (Reference Lines 203-610) */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">

        {/* HEADER */}
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
              </button>
            </div>
          </div>
        </header>

        {/* CONTENT SCROLLABLE */}
        <main className="flex-1 overflow-y-auto custom-scrollbar p-6 lg:p-8">
          <div className="max-w-[1800px] mx-auto flex flex-col gap-6">

            {/* TELEMETRY SECTION */}
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

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* CARD 1: Pending Clips */}
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

              {/* CARD 2: Deployed Today */}
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
                <div className="data-flow-line opacity-50" style={{ animationDelay: '1s' }}></div>
              </div>

              {/* CARD 3: Compute Nodes */}
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
                <div className="data-flow-line opacity-50" style={{ animationDelay: '0.5s' }}></div>
              </div>
            </div>

            {/* MAIN DASHBOARD GRID */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">

              {/* LEFT: WATCH FOLDER MATRIX (Interactive Dropzone) */}
              <div
                onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
                className={`lg:col-span-2 glass-panel rounded-2xl p-0 relative flex flex-col border-t border-t-white/10 overflow-hidden transition-all duration-500 ${isDragging ? 'border-primary shadow-[0_0_30px_rgba(139,85,247,0.3)]' : ''}`}
              >
                {/* Header Overlay */}
                <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-start z-30 pointer-events-none">
                  <div className="pointer-events-auto">
                    <h3 className="text-lg font-bold text-white flex items-center gap-3 font-display">
                      <span className={`flex size-2 rounded-full bg-success shadow-[0_0_10px_#00ff9d] ${uploadStatus === 'uploading' ? 'animate-ping' : 'animate-pulse'}`}></span>
                      Watch Folder Matrix
                    </h3>
                    <div className="flex items-center gap-2 mt-2">
                      <p className="text-[10px] text-[#94a3b8] font-mono tracking-wide bg-black/40 px-2 py-0.5 rounded border border-white/5">PATH: /mnt/data/ingest/*.mp4</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/5 border border-success/20 backdrop-blur-md text-success text-[10px] font-bold uppercase tracking-wider shadow-[0_0_15px_rgba(0,255,157,0.1)]">
                    <span className={`material-symbols-outlined text-sm ${uploadStatus === 'uploading' ? 'animate-spin' : ''}`}>sync</span>
                    {uploadStatus === 'uploading' ? 'INGESTING...' : uploadStatus === 'success' ? 'UPLOAD COMPLETE' : 'LIVE SCANNING'}
                  </div>
                </div>

                {/* Radar Visualization Layer */}
                <div className="absolute inset-0 flex items-center justify-center overflow-hidden bg-[#030304]">
                  {/* Grid & SVGs */}
                  <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(rgba(139, 85, 247, 0.05) 1px, transparent 1px)', backgroundSize: '30px 30px', opacity: 0.3 }}></div>

                  {/* Rotating Rings */}
                  <div className="absolute size-[600px] border border-white/5 rounded-full"></div>
                  <div className="absolute size-[450px] border border-white/5 rounded-full border-dashed animate-spin" style={{ animationDuration: '60s' }}></div>
                  <div className="absolute size-[300px] border border-primary/20 rounded-full shadow-[0_0_30px_rgba(139,85,247,0.1)]"></div>

                  {/* Center Hub */}
                  <div className="absolute size-[160px] flex items-center justify-center z-20">
                    <div className="absolute inset-0 rounded-full border border-primary/30 border-t-primary/80 animate-spin-slow"></div>
                    <div className="absolute inset-2 rounded-full border border-secondary/30 border-b-secondary/80 animate-reverse-spin"></div>
                    <div className={`absolute size-[100px] rounded-full bg-[#050507] border border-primary/50 shadow-[0_0_50px_rgba(139,85,247,0.4)] flex items-center justify-center group cursor-pointer hover:scale-105 transition-transform overflow-hidden ${isDragging ? 'scale-110 border-primary' : ''}`}>
                      <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-secondary/20 animate-pulse"></div>
                      <span className="material-symbols-outlined text-5xl text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.9)] relative z-10 w-full h-full flex items-center justify-center">
                        {uploadStatus === 'uploading' ? 'cloud_upload' : 'neurology'}
                      </span>
                    </div>
                  </div>

                  {/* Scanning Beam */}
                  <div className="absolute size-[600px] rounded-full animate-scan-rotate radar-scan-beam opacity-40 z-10 pointer-events-none"></div>

                  {/* Floating Nodes (Mock Files) */}
                  <div className="absolute top-[25%] left-[25%] flex flex-col items-center gap-3 animate-float z-30 group cursor-pointer">
                    <div className="relative">
                      <div className="bg-[#0f0f13] border border-primary/40 text-white p-3 rounded-xl shadow-[0_0_20px_rgba(139,85,247,0.2)] group-hover:border-primary transition-all relative">
                        <span className="material-symbols-outlined text-2xl">movie</span>
                      </div>
                    </div>
                    <div className="text-[10px] text-white bg-black/80 backdrop-blur px-2 py-0.5 rounded border border-white/10 font-mono tracking-wider">clip_22.mp4</div>
                  </div>

                  {/* Upload Trigger Text */}
                  <div className={`absolute top-[20%] right-[30%] flex flex-col items-center gap-2 z-20 transition-all duration-300 ${isDragging ? 'opacity-100 scale-125' : 'opacity-60 animate-pulse-slow'}`}>
                    <div className={`size-2 rounded-full shadow-[0_0_10px_#fa6c38] ${isDragging ? 'bg-primary shadow-primary' : 'bg-warning'}`}></div>
                    <span className={`text-[9px] font-mono tracking-wider ${isDragging ? 'text-primary' : 'text-warning'}`}>
                      {isDragging ? 'RELEASE_TO_INJECT' : 'SCANNING_NEW_FILES...'}
                    </span>
                  </div>
                </div>

                {/* Bottom Log */}
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
                          <span className="text-gray-200 font-mono text-[11px]">interview_raw_04.mp4</span>
                        </div>
                        <span className="text-[#64748b] font-mono text-[10px]">2s ago</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* RIGHT: NEURAL HEALTH (Profile Selector) */}
              <div className="flex flex-col gap-6 h-full">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span className="material-symbols-outlined text-success">monitor_heart</span>
                    Neural Health
                  </h3>
                  <button className="text-[10px] font-mono text-primary hover:text-white transition-colors uppercase tracking-wider">View All Nodes</button>
                </div>

                <div className="flex flex-col gap-4 flex-1">
                  {/* Map Profiles to Cards */}
                  {profiles.length > 0 ? profiles.map((p, i) => (
                    <div
                      key={p.id}
                      onClick={() => setSelectedProfile(p.id)}
                      className={`glass-panel p-4 rounded-xl flex items-center justify-between group transition-all cursor-pointer ${selectedProfile === p.id ? 'border-primary/60 bg-primary/5' : 'hover:border-primary/40'}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className={`size-10 rounded-lg flex items-center justify-center border shadow-[0_0_15px_rgba(239,68,68,0.1)] transition-shadow ${selectedProfile === p.id ? 'bg-primary/20 text-white border-primary/50' : 'bg-white/5 text-slate-400 border-white/10'}`}>
                            <span className="material-symbols-outlined">{i === 0 ? 'smart_display' : i === 1 ? 'music_note' : 'work'}</span>
                          </div>
                          {selectedProfile === p.id && (
                            <div className="absolute -bottom-1 -right-1 size-2.5 bg-[#050507] rounded-full flex items-center justify-center">
                              <div className="size-1.5 bg-success rounded-full shadow-[0_0_5px_#00ff9d]"></div>
                            </div>
                          )}
                        </div>
                        <div>
                          <h4 className="text-white font-semibold text-sm">{p.label}</h4>
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
                  )) : (
                    <div className="text-center p-4 text-slate-500 font-mono text-xs">Loading Nodes...</div>
                  )}

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

            {/* EVENT STREAM TABLE */}
            <div className="glass-panel rounded-2xl overflow-hidden mb-6">
              <div className="px-6 py-5 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary/70">history</span>
                  Event Stream
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-[#94a3b8]">
                  <thead className="bg-white/5 text-xs uppercase font-semibold text-[#64748b] tracking-wider font-mono">
                    <tr>
                      <th className="px-6 py-4">Asset ID</th>
                      <th className="px-6 py-4">Destination</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4">Duration</th>
                      <th className="px-6 py-4 text-right">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    <tr className="hover:bg-white/[0.02] transition-colors group">
                      <td className="px-6 py-4 font-medium text-white flex items-center gap-4">
                        <div className="size-8 rounded-lg bg-[#0f0f13] flex items-center justify-center text-primary border border-white/5 group-hover:border-primary/50 transition-colors shadow-lg">
                          <span className="material-symbols-outlined text-base">play_circle</span>
                        </div>
                        <span className="font-mono text-xs text-primary/80">marketing_vid_final_v2.mp4</span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-base">smart_display</span>
                          YouTube Shorts
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-success/10 text-success border border-success/20 shadow-[0_0_10px_rgba(11,218,111,0.1)]">
                          <span className="size-1.5 rounded-full bg-success shadow-[0_0_5px_#0bda6f]"></span>
                          Published
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs">00:58:12</td>
                      <td className="px-6 py-4 text-right font-mono text-xs text-white/50">14:02:45</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </main>
      </div>

      {/* SVG FILTERS (Optional) */}
      <svg className="absolute w-0 h-0">
        <defs>
          <filter id="glow-filter">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      </svg>
    </div>
  );
}
