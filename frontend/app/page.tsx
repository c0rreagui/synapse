'use client';

import { useState, useEffect } from 'react';
import GlassCard from './components/GlassCard';
import StatCard from './components/StatCard';
import {
  CloudArrowUpIcon,
  VideoCameraIcon,
  SignalIcon,
  CpuChipIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

export default function Home() {
  // --- LÓGICA DE ESTADO (MANTIDA) ---
  const [profiles, setProfiles] = useState<any[]>([]);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [isLoadingProfiles, setIsLoadingProfiles] = useState(true);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [isDragging, setIsDragging] = useState(false);

  // Fetch Perfis
  useEffect(() => {
    async function fetchProfiles() {
      try {
        const res = await fetch('http://localhost:8000/api/v1/profiles/list');
        if (res.ok) {
          const data = await res.json();
          setProfiles(data);
          if (data.length > 0) setSelectedProfile(data[0].id);
        }
      } catch (error) {
        console.error("Erro API", error);
        setProfiles([{ id: "offline", label: "⚠️ Backend Offline" }]);
      } finally {
        setIsLoadingProfiles(false);
      }
    }
    fetchProfiles();
  }, []);

  // Upload Handlers
  const handleUpload = async (file: File) => {
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append("file", file);
    formData.append("profile_key", selectedProfile);

    try {
      const response = await fetch("http://localhost:8000/api/v1/ingest/upload", {
        method: "POST",
        body: formData,
      });
      if (response.ok) setUploadStatus('success');
      else setUploadStatus('error');
      setTimeout(() => setUploadStatus('idle'), 3000);
    } catch (e) {
      setUploadStatus('error');
    }
  };

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]);
  };

  // --- RENDERIZAÇÃO VISUAL (NOVA) ---
  return (
    <main className="min-h-screen bg-synapse-bg text-synapse-text relative font-sans selection:bg-synapse-primary/30">

      {/* Background FX */}
      <div className="absolute inset-0 bg-cyber-grid opacity-[0.05] pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-glow-radial opacity-40 pointer-events-none" />

      <div className="max-w-7xl mx-auto p-6 relative z-10 space-y-8">

        {/* Header */}
        <header className="flex justify-between items-end border-b border-white/5 pb-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">
              SYNAPSE
            </h1>
            <p className="text-synapse-muted mt-1 font-mono text-xs tracking-widest uppercase">
              Automated Content Operations // v2.0
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-bold text-emerald-400">SYSTEM ONLINE</span>
          </div>
        </header>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard label="Fila de Processamento" value="0" icon={CpuChipIcon} color="purple" />
          <StatCard label="Uploads (24h)" value="12" icon={CloudArrowUpIcon} color="cyan" trend="+20% vs ontem" />
          <StatCard label="Contas Ativas" value={profiles.length || "-"} icon={SignalIcon} color="emerald" />
          <StatCard label="Taxa de Sucesso" value="99.9%" icon={CheckCircleIcon} color="emerald" />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Coluna Esquerda: Centro de Upload */}
          <div className="lg:col-span-2">
            <GlassCard title="Nova Transmissão" className="h-full">

              {/* 1. Profile Selector */}
              <div className="mb-8">
                <label className="block text-xs font-bold text-cyan-400 mb-4 font-mono uppercase tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 bg-cyan-400 rounded-sm"></span>
                  Selecione o Canal de Destino
                </label>

                {isLoadingProfiles ? (
                  <div className="h-16 w-full animate-pulse bg-white/5 rounded-lg"></div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {profiles.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => setSelectedProfile(p.id)}
                        className={`
                          group relative p-4 rounded-lg border text-left transition-all duration-200
                          ${selectedProfile === p.id
                            ? 'bg-synapse-primary/10 border-synapse-primary shadow-[0_0_20px_rgba(6,182,212,0.1)]'
                            : 'bg-synapse-surface border-synapse-border hover:border-synapse-primary/50'
                          }
                        `}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`font-medium ${selectedProfile === p.id ? 'text-white' : 'text-slate-400 group-hover:text-white'}`}>
                            {p.label}
                          </span>
                          {selectedProfile === p.id && <div className="w-2 h-2 bg-cyan-400 rounded-full shadow-[0_0_8px_cyan]"></div>}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* 2. Dropzone */}
              <div>
                <label className="block text-xs font-bold text-purple-400 mb-4 font-mono uppercase tracking-wider flex items-center gap-2">
                  <span className="w-2 h-2 bg-purple-400 rounded-sm"></span>
                  Upload de Mídia
                </label>

                <div
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  className={`
                    relative h-64 rounded-xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center cursor-pointer group
                    ${isDragging
                      ? 'border-cyan-400 bg-cyan-400/5 scale-[1.01] shadow-[0_0_30px_rgba(6,182,212,0.15)]'
                      : 'border-synapse-border bg-synapse-surface/50 hover:border-synapse-primary/40 hover:bg-synapse-surface'
                    }
                    ${uploadStatus === 'success' ? 'border-emerald-500 bg-emerald-500/10' : ''}
                  `}
                >
                  <input
                    type="file"
                    className="absolute inset-0 opacity-0 cursor-pointer"
                    onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
                    accept=".mp4,.mov"
                  />

                  {uploadStatus === 'uploading' ? (
                    <div className="flex flex-col items-center animate-pulse">
                      <ArrowPathIcon className="w-12 h-12 text-cyan-400 animate-spin mb-4" />
                      <p className="text-cyan-400 font-mono text-sm">ENVIANDO DADOS...</p>
                    </div>
                  ) : uploadStatus === 'success' ? (
                    <div className="flex flex-col items-center">
                      <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-4">
                        <CheckCircleIcon className="w-10 h-10 text-emerald-400" />
                      </div>
                      <p className="text-emerald-400 font-bold">UPLOAD CONCLUÍDO</p>
                      <p className="text-slate-500 text-sm mt-1">O robô iniciará o processamento em breve.</p>
                    </div>
                  ) : (
                    <>
                      <div className="w-16 h-16 rounded-full bg-synapse-surface border border-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                        <VideoCameraIcon className="w-8 h-8 text-slate-400 group-hover:text-cyan-400 transition-colors" />
                      </div>
                      <p className="text-lg font-medium text-white group-hover:text-cyan-200 transition-colors">
                        Arraste o arquivo de vídeo aqui
                      </p>
                      <p className="text-sm text-slate-500 mt-2">ou clique para navegar nos arquivos</p>
                    </>
                  )}
                </div>
              </div>

            </GlassCard>
          </div>

          {/* Coluna Direita: Live Log (Mockup por enquanto) */}
          <div className="lg:col-span-1">
            <GlassCard title="Terminal de Eventos" className="h-full bg-black/20">
              <div className="space-y-3 font-mono text-xs">
                <div className="flex gap-3 text-slate-500 border-b border-white/5 pb-2">
                  <span>TIME</span>
                  <span>EVENT</span>
                </div>
                {/* Mock Logs */}
                <div className="flex gap-3">
                  <span className="text-slate-600">18:04:12</span>
                  <span className="text-emerald-400">Upload success: @p2_vid.mp4</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-slate-600">18:03:45</span>
                  <span className="text-cyan-400">Queue active: 2 jobs pending</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-slate-600">18:01:20</span>
                  <span className="text-purple-400">Brain: Generating captions...</span>
                </div>
                <div className="flex gap-3 opacity-50">
                  <span className="text-slate-600">18:00:00</span>
                  <span className="text-slate-400">System initialized.</span>
                </div>
                <div className="mt-4 pt-4 border-t border-white/5">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-cyan-500 animate-pulse rounded-full"></span>
                    <span className="text-cyan-500">Aguardando novos inputs...</span>
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>

        </div>
      </div>
    </main>
  );
}
