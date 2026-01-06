'use client';

import { useState, useEffect } from 'react';
import GlassCard from './components/GlassCard';
import StatCard from './components/StatCard';
import { CloudArrowUpIcon, FilmIcon, SignalIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface Profile {
  id: string;
  label: string;
  color?: string;
}

export default function Home() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [isLoadingProfiles, setIsLoadingProfiles] = useState(true);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');

  // Fetch profiles on mount
  useEffect(() => {
    async function fetchProfiles() {
      try {
        const res = await fetch('http://localhost:8000/api/v1/profiles/list');
        if (res.ok) {
          const data = await res.json();
          // Map backend data to UI format if needed
          // Adicionando cores rotativas para manter o visual neon
          const mappedProfile = data.map((p: Profile, index: number) => ({
            ...p,
            color: index % 2 === 0 ? "border-cyan-500" : "border-purple-500"
          }));
          setProfiles(mappedProfile);
          if (mappedProfile.length > 0) setSelectedProfile(mappedProfile[0].id);
        }
      } catch (e) {
        console.error("Failed to load profiles", e);
        // Fallback visual
        setProfiles([
          { id: "tiktok_profile_01", label: "⚠️ Modo Offline (@p1)", color: "border-gray-500" }
        ]);
      } finally {
        setIsLoadingProfiles(false);
      }
    }
    fetchProfiles();
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await handleUpload(file);
    }
  };

  const handleUpload = async (file: File) => {
    if (!selectedProfile) {
      alert("Selecione um perfil primeiro!");
      return;
    }
    setUploadStatus('uploading');
    const formData = new FormData();
    formData.append("file", file);
    formData.append("profile_key", selectedProfile);

    try {
      const response = await fetch("http://localhost:8000/api/v1/ingest/upload", {
        method: "POST",
        body: formData,
      });
      if (response.ok) {
        setUploadStatus('success');
        setTimeout(() => setUploadStatus('idle'), 3000);
      } else {
        setUploadStatus('error');
      }
    } catch (error) {
      console.error(error);
      setUploadStatus('error');
    }
  };

  return (
    <main className="min-h-screen bg-[#030712] relative overflow-hidden selection:bg-cyan-500/30">

      {/* Radial Gradient Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-[radial-gradient(ellipse_at_top,rgba(6,182,212,0.15),transparent_70%)] pointer-events-none" />

      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10 space-y-6 p-4">

        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-500 mb-1">
              Synapse Command Center
            </h1>
            <p className="text-slate-400">Sistema Operacional de Mídia Autônoma</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="text-sm font-mono text-emerald-400">SYSTEM ONLINE</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Videos na Fila" value="03" icon={<FilmIcon className="w-5 h-5" />} trend="+2 desde ontem" color="primary" />
          <StatCard label="Uploads Hoje" value="12" icon={<CloudArrowUpIcon className="w-5 h-5" />} color="success" />
          <StatCard label="Taxa de Sucesso" value="98.5%" icon={<CheckCircleIcon className="w-5 h-5" />} color="secondary" />
          <StatCard label="Proxies Ativos" value="01" icon={<SignalIcon className="w-5 h-5" />} color="danger" />
        </div>

        {/* Main Action Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left Column: Upload */}
          <div className="lg:col-span-2 space-y-6">
            <GlassCard title="Nova Transmissão" icon={<CloudArrowUpIcon className="w-5 h-5" />} className="border-t border-cyan-500/20">

              {/* Profile Selector */}
              <div className="mb-8 relative">
                {/* Visual Connector Line */}
                <div className="absolute left-4 top-8 bottom-[-40px] w-px bg-gradient-to-b from-cyan-500/50 to-transparent z-0 hidden md:block"></div>

                <label className="block text-xs font-bold text-cyan-500 mb-4 font-mono uppercase tracking-widest flex items-center gap-2 relative z-10">
                  <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_8px_#22d3ee]"></span>
                  1. Selecione o Canal de Destino
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10 pl-6 md:pl-0">
                  {isLoadingProfiles ? (
                    <div className="col-span-2 flex items-center justify-center p-8 border border-dashed border-cyan-900/50 rounded-xl bg-cyan-950/10">
                      <div className="flex flex-col items-center gap-3">
                        <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-cyan-400/70 text-sm font-mono tracking-wider animate-pulse">SINCRONIZANDO CANAIS...</span>
                      </div>
                    </div>
                  ) : profiles.length === 0 ? (
                    <div className="col-span-2 p-6 text-center text-amber-500 bg-amber-500/5 rounded-xl border border-amber-500/10 font-mono text-sm">
                      <p className="font-bold">⚠ NENHUM PERFIL ENCONTRADO</p>
                      <p className="text-xs text-amber-500/70 mt-1">Verifique a conexão com o módulo Brain</p>
                    </div>
                  ) : (
                    profiles.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => setSelectedProfile(p.id)}
                        className={`relative p-4 rounded-xl border transition-all duration-300 group overflow-hidden text-left
                        ${selectedProfile === p.id
                            ? `bg-cyan-950/40 ${p.color || 'border-cyan-500'} shadow-[0_0_20px_rgba(6,182,212,0.15)] ring-1 ring-cyan-500/50`
                            : 'bg-slate-900/40 border-slate-800 hover:border-slate-600 hover:bg-slate-800/60'
                          }`}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />

                        <div className="flex items-center justify-between relative z-10">
                          <span className={`font-medium transition-colors ${selectedProfile === p.id ? 'text-cyan-50' : 'text-slate-400 group-hover:text-slate-200'}`}>
                            {p.label}
                          </span>
                          {selectedProfile === p.id && (
                            <div className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee] animate-pulse"></div>
                          )}
                        </div>
                      </button>
                    )))}
                </div>
              </div>

              {/* Dropzone */}
              <div className="relative">
                <label className="block text-xs font-bold text-cyan-500 mb-4 font-mono uppercase tracking-widest flex items-center gap-2 relative z-10">
                  <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_8px_#22d3ee]"></span>
                  2. Arquivo de Vídeo (.MP4)
                </label>
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleLeave}
                  onDrop={handleDrop}
                  className={`
                    relative border border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer overflow-hidden group
                    ${isDragging
                      ? 'border-cyan-400 bg-cyan-500/10 scale-[1.01] shadow-[0_0_30px_rgba(6,182,212,0.1)]'
                      : 'border-slate-800 hover:border-cyan-500/30 hover:bg-slate-900/60'
                    }
                    ${uploadStatus === 'success' ? 'border-emerald-500 bg-emerald-500/10' : ''}
                  `}
                >
                  <input
                    type="file"
                    title="Upload Video"
                    aria-label="Upload Video"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                    onChange={(e) => e.target.files && handleUpload(e.target.files[0])}
                    accept=".mp4,.mov"
                  />

                  <div className="flex flex-col items-center justify-center space-y-3 relative z-10">
                    <div className={`p-5 rounded-2xl bg-slate-900/80 border border-white/5 transition-transform duration-300 group-hover:scale-110 shadow-lg ${isDragging ? 'text-cyan-400' : 'text-slate-500 group-hover:text-cyan-400'}`}>
                      {uploadStatus === 'uploading' ? (
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
                      ) : uploadStatus === 'success' ? (
                        <CheckCircleIcon className="w-8 h-8 text-emerald-500" />
                      ) : (
                        <CloudArrowUpIcon className="w-8 h-8" />
                      )}
                    </div>
                    <div>
                      <p className={`text-lg font-bold transition-colors ${isDragging ? 'text-cyan-400' : 'text-white'}`}>
                        {uploadStatus === 'success' ? 'Upload Recebido com Sucesso!' : 'Arraste o vídeo aqui'}
                      </p>
                      <p className="text-sm text-slate-500 mt-2 font-medium">ou clique para buscar seus arquivos</p>
                    </div>
                    <div className="pt-2">
                      <span className="text-xs font-mono text-slate-600 bg-slate-900/50 px-2 py-1 rounded border border-white/5">MP4 / MOV • MAX 500MB</span>
                    </div>
                  </div>
                </div>
              </div>

            </GlassCard>
          </div>

          {/* Right Column: Recent Activity */}
          <div className="lg:col-span-1">
            <GlassCard title="Log de Operações" icon={<SignalIcon className="w-5 h-5" />} className="h-full">
              <div className="space-y-4">
                {/* Mock Items - Futuramente virão do Backend */}
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/30 border border-white/5 hover:border-white/10 transition-colors">
                    <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">Video_Corte_0{i}.mp4</p>
                      <p className="text-xs text-slate-500">@p1 • Agendado 18:00</p>
                    </div>
                    <span className="text-xs font-mono text-emerald-400">OK</span>
                  </div>
                ))}
                <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/30 border border-white/5 opacity-60">
                  <div className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse"></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">Processando...</p>
                    <p className="text-xs text-slate-500">Aguardando Fila</p>
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
