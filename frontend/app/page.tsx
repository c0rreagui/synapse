'use client';

import { useState } from 'react';
import GlassCard from './components/GlassCard';
import StatCard from './components/StatCard';
import { CloudArrowUpIcon, FilmIcon, SignalIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const PROFILES = [
  { id: "tiktok_profile_01", label: "✂️ Cortes Aleatórios (@p1)", color: "border-cyan-500" },
  { id: "tiktok_profile_02", label: "🔥 Criando Ibope (@p2)", color: "border-purple-500" },
];

export default function Home() {
  const [selectedProfile, setSelectedProfile] = useState("tiktok_profile_01");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');

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
    <main className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#030712] to-black p-8 text-white relative overflow-hidden">

      {/* Background Grid Effect */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10 space-y-8">

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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard label="Videos na Fila" value="03" icon={<FilmIcon className="w-6 h-6" />} trend="+2 desde ontem" color="primary" />
          <StatCard label="Uploads Hoje" value="12" icon={<CloudArrowUpIcon className="w-6 h-6" />} color="success" />
          <StatCard label="Taxa de Sucesso" value="98.5%" icon={<CheckCircleIcon className="w-6 h-6" />} color="secondary" />
          <StatCard label="Proxies Ativos" value="01" icon={<SignalIcon className="w-6 h-6" />} color="danger" />
        </div>

        {/* Main Action Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left Column: Upload */}
          <div className="lg:col-span-2 space-y-6">
            <GlassCard title="Nova Transmissão" icon={<CloudArrowUpIcon className="w-5 h-5" />} className="border-t border-cyan-500/20">

              {/* Profile Selector */}
              <div className="mb-8">
                <label className="block text-sm font-bold text-cyan-400 mb-3 font-mono uppercase tracking-wider">
                  1. Selecione o Canal de Destino
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {PROFILES.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setSelectedProfile(p.id)}
                      className={`relative p-4 rounded-lg border flex items-center justify-between transition-all duration-200 group
                        ${selectedProfile === p.id
                          ? `bg-cyan-500/10 ${p.color} shadow-[0_0_15px_rgba(6,182,212,0.15)]`
                          : 'bg-slate-800/50 border-slate-700 hover:border-slate-500 hover:bg-slate-800'
                        }`}
                    >
                      <span className="font-medium text-white group-hover:text-cyan-300 transition-colors">{p.label}</span>
                      {selectedProfile === p.id && (
                        <div className="h-3 w-3 rounded-full bg-cyan-400 shadow-[0_0_10px_#22d3ee]"></div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dropzone */}
              <div>
                <label className="block text-sm font-bold text-cyan-400 mb-3 font-mono uppercase tracking-wider">
                  2. Arquivo de Vídeo (.MP4)
                </label>
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleLeave}
                  onDrop={handleDrop}
                  className={`
                    relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer overflow-hidden
                    ${isDragging
                      ? 'border-cyan-400 bg-cyan-400/5 scale-[1.01]'
                      : 'border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800/50'
                    }
                    ${uploadStatus === 'success' ? 'border-emerald-500 bg-emerald-500/10' : ''}
                  `}
                >
                  <input
                    type="file"
                    title="Upload Video"
                    aria-label="Upload Video"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    onChange={(e) => e.target.files && handleUpload(e.target.files[0])}
                    accept=".mp4,.mov"
                  />

                  <div className="flex flex-col items-center justify-center space-y-4">
                    <div className={`p-4 rounded-full bg-slate-800/80 ${isDragging ? 'text-cyan-400' : 'text-slate-400'}`}>
                      {uploadStatus === 'uploading' ? (
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
                      ) : uploadStatus === 'success' ? (
                        <CheckCircleIcon className="w-8 h-8 text-emerald-500" />
                      ) : (
                        <CloudArrowUpIcon className="w-8 h-8" />
                      )}
                    </div>
                    <div>
                      <p className="text-lg font-medium text-white">
                        {uploadStatus === 'success' ? 'Upload Recebido com Sucesso!' : 'Arraste o vídeo aqui ou clique para buscar'}
                      </p>
                      <p className="text-sm text-slate-500 mt-1">Suporta MP4 e MOV (Max 500MB)</p>
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
