'use client';
import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import CommandCenter from './components/CommandCenter';
import Toast from './components/Toast';
import ConnectionStatus from './components/ConnectionStatus';
import CommandPalette from './components/CommandPalette';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { TikTokProfile } from './types';
import {
  PlayCircleIcon, CpuChipIcon, CheckCircleIcon,
  ClockIcon, XCircleIcon, XMarkIcon,
  MagnifyingGlassIcon, ArrowPathIcon
} from '@heroicons/react/24/outline';
const API_BASE = 'http://localhost:8000/api/v1';
interface IngestionStatus { queued: number; processing: number; completed: number; failed: number; }
interface PendingVideo {
  id: string;
  filename: string;
  profile: string;
  uploaded_at: string;
  status: string;
  metadata: {
    caption?: string;
    original_filename?: string;
    profile_id?: string;
  };
}
export default function Home() {
  const [ingestionStatus, setIngestionStatus] = useState<IngestionStatus>({ queued: 0, processing: 0, completed: 0, failed: 0 });
  const [pendingVideos, setPendingVideos] = useState<PendingVideo[]>([]);
  const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
  // UI State
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [toast, setToast] = useState<{ message: string; type: string; duration?: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // Modal State
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<PendingVideo | null>(null);
  const [postType, setPostType] = useState<'immediate' | 'scheduled'>('immediate');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('12:00');
  // System State
  const [backendOnline, setBackendOnline] = useState(false);
  const [lastUpdate, setLastUpdate] = useState('');
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  // Note: WebSocket is managed by CommandCenter component
  const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info', duration = 3000) => {
    setToast({ message, type, duration });
    if (duration > 0) setTimeout(() => setToast(null), duration + 300);
  };
  const fetchAllData = useCallback(async () => {
    try {
      setLastUpdate(new Date().toLocaleTimeString());
      const healthRes = await fetch('http://localhost:8000/');
      setBackendOnline(healthRes.ok);
      // Se backend offline, não tenta o resto para evitar spam de erros
      if (!healthRes.ok) return;
      const [statusRes, queueRes, profilesRes] = await Promise.all([
        fetch(`${API_BASE}/ingest/status`),
        fetch(`${API_BASE}/queue/pending`),
        fetch(`${API_BASE}/profiles/list`)
      ]);
      if (statusRes.ok) setIngestionStatus(await statusRes.json());
      if (queueRes.ok) setPendingVideos(await queueRes.json());
      if (profilesRes.ok) {
        const profs = await profilesRes.json();
        setProfiles(profs);
        if (!selectedProfile && profs.length > 0) setSelectedProfile(profs[0].id);
      }
    } catch {
      setBackendOnline(false);
    } finally {
      setIsLoading(false);
    }
  }, [selectedProfile]);
  // Polling como fallback e para dados não-socket
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000);
    return () => clearInterval(interval);
  }, [fetchAllData]);
  const commands = [
    { id: 'upload', title: 'Upload Video', key: 'u', description: 'Abrir seletor de arquivo', action: () => document.getElementById('file-input')?.click() },
    { id: 'refresh', title: 'Atualizar Dados', key: 'r', description: 'Recarregar dashboard', action: fetchAllData },
  ];
  useKeyboardShortcuts(commands);
  const handleUpload = async (file: File) => {
    setUploadStatus('uploading');
    showToast(`Enviando ${file.name}...`, 'info');
    const formData = new FormData();
    formData.append("file", file);
    formData.append("profile_id", selectedProfile || "p1");
    try {
      const response = await fetch(`${API_BASE}/ingest/upload`, { method: "POST", body: formData });
      if (response.ok) {
        setUploadStatus('success');
        showToast(`✓ ${file.name} enviado com sucesso!`, 'success');
        fetchAllData();
      } else {
        setUploadStatus('error');
        showToast(`✕ Erro ao enviar ${file.name}`, 'error');
      }
      setTimeout(() => setUploadStatus('idle'), 3000);
    } catch {
      setUploadStatus('error');
      showToast('✕ Falha na conexão com o servidor', 'error');
    }
  };
  const handleApprove = (video: PendingVideo) => {
    setSelectedVideo(video);
    setShowApprovalModal(true);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setSelectedDate(tomorrow.toISOString().split('T')[0]);
  };
  const handleReject = async (videoId: string) => {
    if (!confirm('Rejeitar este vídeo?')) return;
    try {
      await fetch(`${API_BASE}/queue/${videoId}`, { method: 'DELETE' });
      fetchAllData();
      showToast('Vídeo rejeitado', 'info');
    } catch { showToast('Erro', 'error'); }
  };
  const handleConfirmApproval = async () => {
    if (!selectedVideo) return;
    try {
      const scheduleTime = postType === 'scheduled' ? `${selectedDate}T${selectedTime}:00` : null;
      const response = await fetch(`${API_BASE}/queue/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: selectedVideo.id, action: postType, schedule_time: scheduleTime })
      });

      if (response.ok) {
        setShowApprovalModal(false);
        setSelectedVideo(null);
        fetchAllData();
        showToast('Processado com sucesso!', 'success');
      } else {
        throw new Error('Falha na resposta');
      }
    } catch {
      showToast('Erro na aprovação', 'error');
    }
  };
  return (
    <div className="flex min-h-screen bg-cmd-bg text-gray-300 font-sans selection:bg-cmd-purple selection:text-white">
      <Sidebar />
      {toast && <Toast message={toast.message} type={toast.type as any} duration={toast.duration} onClose={() => setToast(null)} />}
      <CommandPalette isOpen={showCommandPalette} onClose={() => setShowCommandPalette(false)} commands={commands} />
      <main className="flex-1 p-8 overflow-y-auto max-h-screen custom-scrollbar">

        {/* HEADER */}
        <header className="flex items-center justify-between mb-8 fade-in">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center border transition-all duration-500 ${backendOnline ? 'bg-cmd-green-bg border-cmd-green/30 shadow-[0_0_15px_rgba(52,211,153,0.3)]' : 'bg-cmd-red-bg border-cmd-red/30'}`}>
              <CpuChipIcon className={`w-7 h-7 ${backendOnline ? 'text-cmd-green animate-pulse-slow' : 'text-cmd-red'}`} />
            </div>
            <div>
              <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400 tracking-tight">Synapse Dashboard</h2>
              <p className="text-xs text-cmd-text-muted flex items-center gap-2 font-mono mt-1">
                <ClockIcon className="w-3 h-3" /> SYSTEM_TIME: {lastUpdate || 'SYNCING...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button onClick={() => fetchAllData()} className="p-2 rounded-lg border border-cmd-border hover:bg-cmd-card active:scale-95 transition-all text-cmd-text-muted" title="Atualizar">
              <ArrowPathIcon className="w-5 h-5" />
            </button>
            <button onClick={() => setShowCommandPalette(true)} className="hidden md:flex items-center gap-2 px-4 py-2 rounded-lg border border-cmd-border hover:bg-white/5 transition-all text-sm text-cmd-text-muted cursor-pointer hover:border-cmd-purple/30 group">
              <MagnifyingGlassIcon className="w-4 h-4 group-hover:text-white transition-colors" />
              <span>Comando</span>
              <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-white ml-2">Ctrl+K</span>
            </button>
            <ConnectionStatus isOnline={backendOnline} lastUpdate={lastUpdate} />
          </div>
        </header>
        {/* COMMAND CENTER VISUALS */}
        <div className="mb-8">
          <CommandCenter scheduledVideos={[]} />
        </div>
        {/* METRICS GRID */}
        <section className="mb-8 fade-in stagger-1">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest pl-1">Metrics & Telemetry</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: ClockIcon, label: 'Na Fila', value: ingestionStatus.queued, accent: 'var(--cmd-yellow)' },
              { icon: CpuChipIcon, label: 'Processando', value: ingestionStatus.processing, accent: 'var(--cmd-blue)' },
              { icon: CheckCircleIcon, label: 'Concluídos', value: ingestionStatus.completed, accent: 'var(--cmd-green)' },
              { icon: XCircleIcon, label: 'Falhas', value: ingestionStatus.failed, accent: 'var(--cmd-red)' },
            ].map((card, i) => (
              <div key={i} className="stat-card p-6 flex flex-col justify-between h-32 relative overflow-hidden group" style={{ '--stat-accent': card.accent } as any}>
                <div className="flex justify-between items-start relative z-10">
                  <div className="p-2 rounded-lg bg-white/5 border border-white/10 group-hover:bg-white/10 transition-colors">
                    <card.icon className="w-5 h-5" style={{ color: card.accent }} />
                  </div>
                  <span className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">{card.label}</span>
                </div>
                <p className="text-4xl font-extrabold text-white mt-2 count-animation relative z-10">{card.value}</p>
                {/* Background Glow */}
                <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full blur-2xl opacity-0 group-hover:opacity-20 transition-opacity duration-500" style={{ background: card.accent }}></div>
              </div>
            ))}
          </div>
        </section>
        {/* MAIN SPLIT */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* LEFT COLUMN: UPLOAD & PENDING */}
          <div className="xl:col-span-2 flex flex-col gap-6 fade-in stagger-2">

            {/* UPLOAD CARD */}
            <div className="glass-card p-8 relative overflow-hidden group">
              <div className="flex justify-between items-center mb-6 relative z-10">
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <span className="w-1.5 h-6 bg-gradient-brand rounded-full block shadow-[0_0_10px_rgba(232,121,249,0.5)]"></span>
                  Central de Ingestão
                </h3>
                <div className="relative group/select">
                  <select
                    value={selectedProfile}
                    onChange={e => setSelectedProfile(e.target.value)}
                    className="appearance-none bg-[#0d1117]/80 backdrop-blur border border-cmd-border text-white text-sm rounded-lg pl-4 pr-10 py-2.5 focus:ring-2 focus:ring-cmd-purple/50 focus:border-cmd-purple outline-none cursor-pointer transition-all hover:border-cmd-purple/50 shadow-lg min-w-[200px]"
                  >
                    {profiles.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400 group-hover/select:text-cmd-purple transition-colors">▼</div>
                </div>
              </div>
              <div
                className={`upload-zone h-64 flex flex-col items-center justify-center transition-all duration-300 border-2 border-dashed ${isDragging ? 'border-cmd-green bg-cmd-green/5 scale-[0.99] shadow-[inset_0_0_30px_rgba(52,211,153,0.1)]' : 'border-gray-700 hover:border-gray-500 hover:bg-white/5'}`}
                onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={e => { e.preventDefault(); setIsDragging(false); if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]) }}
              >
                <input id="file-input" type="file" className="hidden" onChange={e => e.target.files?.[0] && handleUpload(e.target.files[0])} accept=".mp4,.mov,.avi" />

                <div className={`w-20 h-20 rounded-full bg-[#1c2128] flex items-center justify-center mb-4 transition-all duration-500 shadow-xl ${isDragging ? 'scale-110 text-cmd-green' : 'text-gray-500 group-hover:text-white'}`}>
                  <PlayCircleIcon className="w-10 h-10" />
                </div>
                <p className="text-lg font-medium text-gray-300">
                  {uploadStatus === 'uploading' ? <span className="animate-pulse text-cmd-purple">Enviando ao servidor...</span> : 'Arraste seu vídeo aqui'}
                </p>
                <p className="text-sm text-gray-500 mt-2">ou clique para selecionar do computador</p>
              </div>
            </div>
            {/* PENDING LIST */}
            <div className="bg-[#161b22]/50 border border-cmd-border rounded-xl p-6 relative backdrop-blur-sm">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <ClockIcon className="w-5 h-5 text-cmd-purple" /> Fila de Aprovação
                </h3>
                {pendingVideos.length > 0 && (
                  <span className="animate-pulse text-xs px-2 py-0.5 rounded-full bg-cmd-purple/20 text-cmd-purple border border-cmd-purple/30 font-bold">
                    ATIVO
                  </span>
                )}
              </div>
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {pendingVideos.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-lg">
                    <CheckCircleIcon className="w-10 h-10 mb-2 opacity-20" />
                    <p>Nenhum vídeo aguardando aprovação.</p>
                  </div>
                ) : (
                  pendingVideos.map(v => (
                    <div key={v.id} className="p-4 bg-black/40 border border-white/5 rounded-lg flex items-center gap-4 hover:border-cmd-purple/30 transition-all group">
                      <div className="w-12 h-12 rounded-lg bg-gray-900 flex items-center justify-center text-xl shrink-0 border border-gray-800 group-hover:border-gray-600">🎬</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate group-hover:text-cmd-purple transition-colors">{v.metadata.original_filename}</p>
                        <p className="text-xs text-gray-500 font-mono mt-0.5 flex items-center gap-2">
                          <span className="bg-white/10 px-1 rounded text-[10px]">{v.metadata.profile_id}</span>
                          {new Date(v.uploaded_at).toLocaleTimeString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 opacity-80 group-hover:opacity-100">
                        <button onClick={() => handleApprove(v)} className="px-3 py-1.5 rounded-md bg-cmd-green/10 text-cmd-green border border-cmd-green/30 text-xs font-bold hover:bg-cmd-green hover:text-black transition-all shadow-[0_0_10px_transparent] hover:shadow-[0_0_10px_var(--cmd-green)]">APROVAR</button>
                        <button onClick={() => handleReject(v.id)} className="p-1.5 rounded-md bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white transition-all"><XMarkIcon className="w-4 h-4" /></button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          {/* RIGHT COLUMN: PROFILES & STATS */}
          <div className="flex flex-col gap-6 fade-in stagger-3">
            <div className="glass-card p-6">
              <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 border-b border-white/5 pb-2">Perfis Conectados</h3>
              <div className="space-y-2">
                {profiles.map(p => (
                  <div
                    key={p.id}
                    onClick={() => setSelectedProfile(p.id)}
                    className={`flex items-center gap-3 p-3 rounded-xl transition-all border cursor-pointer group ${selectedProfile === p.id ? 'bg-white/10 border-cmd-purple/50 shadow-lg' : 'bg-transparent border-transparent hover:bg-white/5 hover:border-white/10'}`}
                  >
                    <div className={`relative ${selectedProfile === p.id ? 'scale-105' : ''} transition-transform`}>
                      {p.avatar_url ? (
                        <img src={p.avatar_url} alt={p.label} className="w-10 h-10 rounded-full object-cover ring-2 ring-transparent group-hover:ring-white/20" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center text-lg shadow-inner">{p.icon || '👤'}</div>
                      )}
                      {selectedProfile === p.id && <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-cmd-green rounded-full border-2 border-[#151020] animate-pulse"></div>}
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-bold leading-tight ${selectedProfile === p.id ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'}`}>{p.label}</p>
                      <p className="text-xs text-xs text-gray-600 font-mono leading-tight mt-1 truncate">{p.username ? `@${p.username}` : 'Sem user'}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-xl border border-cmd-border bg-gradient-to-b from-cmd-card to-transparent">
              <h4 className="text-xs text-gray-500 font-bold mb-2 uppercase">Status do Sistema</h4>
              <div className="flex items-center gap-2 text-xs text-gray-400 font-mono">
                <div className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-cmd-green' : 'bg-red-500'}`}></div>
                {backendOnline ? 'ONLINE' : 'OFFLINE'}
              </div>
            </div>
          </div>
        </div>
      </main>
      {/* APPROVAL MODAL */}
      {showApprovalModal && selectedVideo && (
        <div className="fixed inset-0 bg-[#05040a]/80 backdrop-blur-md z-[100] flex items-center justify-center fade-in p-4">
          <div className="w-full max-w-md bg-[#161b22] border border-cmd-border rounded-2xl p-6 shadow-2xl transform transition-all scale-100 relative overflow-hidden">
            {/* Top Border Gradient */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-brand"></div>
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <span>🚀 Aprovar Publicação</span>
            </h2>

            <div className="p-4 bg-black/30 rounded-lg mb-6 flex items-center gap-3 border border-white/5">
              <div className="text-2xl">📄</div>
              <div className="overflow-hidden">
                <p className="text-sm text-white font-medium truncate">{selectedVideo.metadata.original_filename}</p>
                <p className="text-xs text-gray-500">{selectedVideo.profile}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <button onClick={() => setPostType('immediate')} className={`p-4 rounded-xl border transition-all relative overflow-hidden group ${postType === 'immediate' ? 'border-cmd-green bg-cmd-green/5' : 'border-gray-700 bg-gray-800/50 hover:border-gray-500'}`}>
                {postType === 'immediate' && <div className="absolute top-2 right-2 text-cmd-green"><CheckCircleIcon className="w-5 h-5" /></div>}
                <div className={`font-bold mb-1 ${postType === 'immediate' ? 'text-cmd-green' : 'text-gray-300'}`}>Imediato</div>
                <div className="text-xs text-gray-500">Publicar agora</div>
              </button>

              <button onClick={() => setPostType('scheduled')} className={`p-4 rounded-xl border transition-all relative overflow-hidden group ${postType === 'scheduled' ? 'border-cmd-purple bg-cmd-purple/5' : 'border-gray-700 bg-gray-800/50 hover:border-gray-500'}`}>
                {postType === 'scheduled' && <div className="absolute top-2 right-2 text-cmd-purple"><CheckCircleIcon className="w-5 h-5" /></div>}
                <div className={`font-bold mb-1 ${postType === 'scheduled' ? 'text-cmd-purple' : 'text-gray-300'}`}>Agendar</div>
                <div className="text-xs text-gray-500">Escolher data/hora</div>
              </button>
            </div>
            {postType === 'scheduled' && (
              <div className="space-y-3 mb-6 animate-pulse-slow bg-white/5 p-4 rounded-xl border border-white/10">
                <div>
                  <label className="text-xs text-gray-500 font-bold mb-1 block">DATA</label>
                  <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} className="w-full bg-black/50 border border-gray-600 rounded-lg p-2.5 text-white outline-none focus:border-cmd-purple transition-colors" />
                </div>
                <div>
                  <label className="text-xs text-gray-500 font-bold mb-1 block">HORÁRIO</label>
                  <input type="time" value={selectedTime} onChange={e => setSelectedTime(e.target.value)} className="w-full bg-black/50 border border-gray-600 rounded-lg p-2.5 text-white outline-none focus:border-cmd-purple transition-colors" />
                </div>
              </div>
            )}
            <div className="flex gap-3 mt-8">
              <button onClick={() => setShowApprovalModal(false)} className="flex-1 py-3 px-4 rounded-xl bg-transparent border border-gray-700 text-gray-300 font-bold hover:bg-white/5 transition-colors">Cancelar</button>
              <button onClick={handleConfirmApproval} className="flex-1 py-3 px-4 rounded-xl bg-gradient-brand text-white font-bold hover:opacity-90 transition-opacity shadow-[0_4px_20px_rgba(168,85,247,0.3)]">
                {postType === 'immediate' ? 'Publicar Agora' : 'Confirmar Agendamento'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
