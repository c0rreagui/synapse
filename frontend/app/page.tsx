'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
// import Sidebar from './components/Sidebar'; // Legacy Sidebar removed
import CommandCenter from './components/CommandCenter';
import ConnectionStatus from './components/ConnectionStatus';
import CommandPalette from './components/CommandPalette';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { TikTokProfile, ScheduleEvent } from './types';
import { toast } from 'sonner';
import axios from 'axios';
import {
  PlayCircleIcon, CpuChipIcon, CheckCircleIcon,
  ClockIcon, XCircleIcon, XMarkIcon,
  MagnifyingGlassIcon, ArrowPathIcon, CloudArrowUpIcon, CalendarIcon
} from '@heroicons/react/24/outline';
import useWebSocket from './hooks/useWebSocket';
import MetricsModal from './components/MetricsModal';
import { StitchCard } from './components/StitchCard';
import { NeonButton } from './components/NeonButton';
import clsx from 'clsx';
import BatchUploadModal from './components/BatchUploadModal';
import AudioSuggestionCard, { AudioSuggestion } from './components/AudioSuggestionCard';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace('localhost', '127.0.0.1') + '/api/v1';

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
  const [scheduledEvents, setScheduledEvents] = useState<ScheduleEvent[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Metrics Modal State
  const [isMetricsModalOpen, setIsMetricsModalOpen] = useState(false);
  const [metricsModalTab, setMetricsModalTab] = useState('processing');

  // UI State
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  // Batch State
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [batchFiles, setBatchFiles] = useState<File[]>([]);

  // Selection State
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

  // Audio Suggestion State
  const [audioSuggestions, setAudioSuggestions] = useState<AudioSuggestion[]>([]);
  const [showAudioSuggestion, setShowAudioSuggestion] = useState(false);
  const [lastUploadedFile, setLastUploadedFile] = useState<string>('');

  // Validation & Confirmation State
  const [confirmModal, setConfirmModal] = useState<{ isOpen: boolean; title: string; onConfirm: () => void; type: 'delete' | 'success' }>({ isOpen: false, title: '', onConfirm: () => { }, type: 'delete' });

  // Real-time Schedule Updates
  useWebSocket({
    onScheduleUpdate: (events) => {
      setScheduledEvents(events);
    }
  });

  // Modal State
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<PendingVideo | null>(null);
  const [postType, setPostType] = useState<'immediate' | 'scheduled'>('immediate');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('12:00');
  const [viralMusicEnabled, setViralMusicEnabled] = useState(false);
  const [privacyLevel, setPrivacyLevel] = useState('public_to_everyone'); // public_to_everyone, mutual_follow_friends, self_only

  // System State
  const [backendOnline, setBackendOnline] = useState(false);
  const [lastUpdate, setLastUpdate] = useState('');
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  // Note: WebSocket is managed by CommandCenter component
  const fetchAllData = useCallback(async () => {
    try {
      setLastUpdate(new Date().toLocaleTimeString());
      const apiUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace('localhost', '127.0.0.1');
      const healthRes = await fetch(`${apiUrl}/`);
      setBackendOnline(healthRes.ok);
      // Se backend offline, não tenta o resto para evitar spam de erros
      if (!healthRes.ok) return;

      const [statusRes, queueRes, profilesRes, scheduleRes] = await Promise.all([
        fetch(`${API_BASE}/ingest/status`),
        fetch(`${API_BASE}/queue/pending`),
        fetch(`${API_BASE}/profiles/list`),
        fetch(`${API_BASE}/scheduler/list`)
      ]);

      if (statusRes.ok) setIngestionStatus(await statusRes.json());
      if (queueRes.ok) setPendingVideos(await queueRes.json());
      if (scheduleRes.ok) setScheduledEvents(await scheduleRes.json());
      if (profilesRes.ok) {
        const profs = await profilesRes.json();
        setProfiles(profs);
        // Fix: Use functional update to avoid dependency on selectedProfile
        if (profs.length > 0) {
          setSelectedProfile(prev => prev || profs[0].id);
        }
      }
    } catch {
      setBackendOnline(false);
    } finally {
      setIsLoading(false);
    }
  }, []); // Fix: Removed selectedProfile dependency

  // Polling como fallback e para dados não-socket
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const commands = [
    { id: 'upload', title: 'Upload Video', key: 'u', description: 'Abrir seletor de arquivo', action: () => fileInputRef.current?.click() },
    { id: 'refresh', title: 'Atualizar Dados', key: 'r', description: 'Recarregar dashboard', action: fetchAllData },
  ];

  useKeyboardShortcuts(commands);

  const handleUpload = async (file: File) => {
    setUploadStatus('uploading');
    setUploadProgress(0);
    toast.info(`Enviando ${file.name}...`);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("profile_id", selectedProfile || "p1");

    try {
      await axios.post(`${API_BASE}/ingest/upload`, formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || file.size));
          setUploadProgress(percentCompleted);
        }
      });

      setUploadStatus('success');
      toast.success(`✓ ${file.name} enviado com sucesso!`);
      setLastUploadedFile(file.name);
      fetchAllData();

      // 🎵 Buscar sugestões de áudio após upload
      try {
        // Usar 'general' como nicho padrão
        const niche = 'general';

        const suggestRes = await fetch(`${API_BASE}/audio/suggest`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ niche, limit: 3 })
        });

        if (suggestRes.ok) {
          const data = await suggestRes.json();
          if (data.suggestions && data.suggestions.length > 0) {
            setAudioSuggestions(data.suggestions);
            setShowAudioSuggestion(true);
          }
        }
      } catch (audioError) {
        console.log('Audio suggestions not available:', audioError);
      }

    } catch (error) {
      setUploadStatus('error');
      toast.error(`✕ Erro ao enviar ${file.name}`);
      console.error(error);
    } finally {
      setTimeout(() => {
        setUploadStatus('idle');
        setUploadProgress(0);
      }, 3000);
    }
  };

  const handleApprove = (video: PendingVideo) => {
    setSelectedVideo(video);
    setShowApprovalModal(true);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setSelectedDate(tomorrow.toISOString().split('T')[0]);
  };

  const handleConfirmApproval = async () => {
    if (!selectedVideo) return;
    try {
      const scheduleTime = postType === 'scheduled' ? `${selectedDate}T${selectedTime}:00` : null;
      const response = await fetch(`${API_BASE}/queue/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: selectedVideo.id,
          action: postType,
          schedule_time: scheduleTime,
          viral_music_enabled: viralMusicEnabled,
          privacy_level: privacyLevel
        })
      });

      if (response.ok) {
        setShowApprovalModal(false);
        setSelectedVideo(null);
        fetchAllData();
        toast.success('Processado com sucesso!');
      } else {
        throw new Error('Falha na resposta');
      }
    } catch {
      toast.error('Erro na aprovação');
    }
  };

  const handleReject = async (id: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Rejeitar este vídeo? Esta ação não pode ser desfeita.',
      type: 'delete',
      onConfirm: async () => {
        try {
          await fetch(`${API_BASE}/queue/${id}`, { method: 'DELETE' });
          toast.success('Vídeo rejeitado', { icon: '🗑️' });
          fetchAllData();
        } catch {
          toast.error('Erro ao rejeitar');
        }
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
      }
    });
  };

  // Bulk Actions
  const toggleSelection = (id: string) => {
    const newSet = new Set(selectedItems);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedItems(newSet);
  };

  const toggleSelectAll = () => {
    if (selectedItems.size === pendingVideos.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(pendingVideos.map(v => v.id)));
    }
  };

  const handleBulkReject = async () => {
    if (selectedItems.size === 0) return;

    setConfirmModal({
      isOpen: true,
      title: `Rejeitar ${selectedItems.size} vídeos selecionados?`,
      type: 'delete',
      onConfirm: async () => {
        let successCount = 0;
        for (const id of Array.from(selectedItems)) {
          try {
            await fetch(`${API_BASE}/queue/${id}`, { method: 'DELETE' });
            successCount++;
          } catch (e) { console.error(`Failed to delete ${id}`, e); }
        }

        toast.success(`${successCount} vídeos rejeitados`);
        setSelectedItems(new Set());
        fetchAllData();
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
      }
    });
  };

  const handleBulkApprove = async () => {
    if (!confirm(`Aprovar ${selectedItems.size} vídeos (Imediato)?`)) return;

    let successCount = 0;
    for (const id of Array.from(selectedItems)) {
      try {
        await fetch(`${API_BASE}/queue/approve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id, action: 'immediate' })
        });
        successCount++;
      } catch (e) { console.error(`Failed to approve ${id}`, e); }
    }

    toast.success(`${successCount} vídeos aprovados!`);
    setSelectedItems(new Set());
    fetchAllData();
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'Recente';
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? 'Recente' : d.toLocaleTimeString();
  };

  return (
    <>
      <CommandPalette isOpen={showCommandPalette} onClose={() => setShowCommandPalette(false)} commands={commands} />

      {/* HEADER */}
      <header className="flex items-center justify-between mb-10 relative">
        {/* Decorative Top Line */}
        <div className="absolute -top-8 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        <div className="flex items-center gap-6">
          <div className={`w-14 h-14 relative flex items-center justify-center border transition-all duration-500 ${backendOnline ? 'bg-synapse-emerald/5 border-synapse-emerald/20' : 'bg-red-500/5 border-red-500/20'}`}>
            <div className="absolute inset-0 border-[0.5px] border-white/5 m-1 pointer-events-none" />
            <CpuChipIcon className={`w-8 h-8 ${backendOnline ? 'text-synapse-emerald shadow-[0_0_15px_rgba(16,185,129,0.4)]' : 'text-red-500'}`} />

            {/* Corner Accents */}
            <div className="absolute top-0 left-0 w-1.5 h-1.5 border-t border-l border-white/30" />
            <div className="absolute bottom-0 right-0 w-1.5 h-1.5 border-b border-r border-white/30" />
          </div>

          <div>
            <h2 className="text-4xl font-bold text-white tracking-tighter uppercase font-mono">
              Synapse<span className="text-synapse-primary">_OS</span>
            </h2>
            <div className="flex items-center gap-4 mt-1">
              <p className="text-[10px] text-gray-500 font-mono flex items-center gap-1.5 uppercase tracking-widest border-r border-white/10 pr-4">
                <ClockIcon className="w-3 h-3" /> T-SYNC: {lastUpdate || 'INITIALIZING...'}
              </p>
              <div className="flex items-center gap-1.5">
                <div className={`w-1.5 h-1.5 rounded-full ${backendOnline ? 'bg-synapse-emerald animate-pulse' : 'bg-red-500'}`} />
                <span className={`text-[10px] uppercase font-bold tracking-wider ${backendOnline ? 'text-synapse-emerald' : 'text-red-500'}`}>
                  {backendOnline ? 'SYSTEM ONLINE' : 'CRITICAL FAILURE'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Tech Buttons */}
          <button onClick={() => fetchAllData()} className="h-10 px-4 flex items-center gap-2 border border-white/10 bg-black/40 hover:bg-white/5 hover:border-synapse-primary/50 transition-all group active:scale-95">
            <ArrowPathIcon className="w-4 h-4 text-gray-400 group-hover:text-synapse-primary group-hover:rotate-180 transition-all duration-700" />
            <span className="text-xs font-mono text-gray-400 group-hover:text-white uppercase">Refresh</span>
          </button>

          <button onClick={() => setShowCommandPalette(true)} className="hidden md:flex h-10 items-center gap-3 px-5 border border-white/10 bg-black/40 hover:bg-white/5 hover:border-synapse-primary/50 transition-all group active:scale-95 relative overflow-hidden">
            <div className="absolute inset-0 bg-synapse-primary/5 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
            <MagnifyingGlassIcon className="w-4 h-4 text-gray-400 group-hover:text-white relative z-10" />
            <span className="text-xs font-mono text-gray-400 group-hover:text-white uppercase relative z-10">Command Line</span>
            <kbd className="text-[9px] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-gray-500 font-mono relative z-10 group-hover:border-synapse-primary/30 group-hover:text-synapse-primary">CTRL+K</kbd>
          </button>
        </div>
      </header>

      {/* COMMAND CENTER VISUALS */}
      <div className="mb-8">
        <CommandCenter scheduledVideos={scheduledEvents} />
      </div>

      {/* METRICS GRID */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest pl-1">Metrics & Telemetry</h3>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {[
            { key: 'queued', icon: ClockIcon, label: 'Fila', value: ingestionStatus.queued, color: 'text-synapse-amber', bg: 'bg-synapse-amber/10', border: 'border-synapse-amber/30' },
            { key: 'scheduled', icon: CalendarIcon, label: 'Agendados', value: scheduledEvents.length, color: 'text-synapse-purple', bg: 'bg-synapse-purple/10', border: 'border-synapse-purple/30' },
            { key: 'processing', icon: CpuChipIcon, label: 'Processando', value: ingestionStatus.processing, color: 'text-synapse-cyan', bg: 'bg-synapse-cyan/10', border: 'border-synapse-cyan/30' },
            { key: 'completed', icon: CheckCircleIcon, label: 'Concluídos', value: ingestionStatus.completed, color: 'text-synapse-emerald', bg: 'bg-synapse-emerald/10', border: 'border-synapse-emerald/30' },
            { key: 'failed', icon: XCircleIcon, label: 'Falhas', value: ingestionStatus.failed, color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30' },
          ].map((card, i) => (
            <StitchCard
              key={i}
              className="p-6 flex flex-col justify-between h-32 relative group cursor-pointer hover:border-white/20 active:scale-[0.98] transition-all"
              onClick={() => {
                setMetricsModalTab(card.key);
                setIsMetricsModalOpen(true);
              }}
            >
              <div className="flex justify-between items-start relative z-10">
                <div className={`p-2 rounded-lg ${card.bg} border ${card.border} transition-colors`}>
                  <card.icon className={`w-5 h-5 ${card.color}`} />
                </div>
                <span className="text-[10px] uppercase tracking-wider text-gray-500 font-mono">{card.label}</span>
              </div>
              <p className="text-4xl font-extrabold text-white mt-2 relative z-10">{card.value}</p>
              {/* Background Glow */}
              <div className={`absolute -bottom-4 -right-4 w-24 h-24 rounded-full blur-2xl opacity-0 group-hover:opacity-20 transition-opacity duration-500 ${card.bg.replace('/10', '')}`}></div>
            </StitchCard>
          ))}
        </div>
      </section>

      {/* MAIN SPLIT */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* LEFT COLUMN: UPLOAD & PENDING */}
        <div className="xl:col-span-2 flex flex-col gap-6">

          {/* UPLOAD CARD */}
          <StitchCard className="p-8 group">
            <div className="flex justify-between items-center mb-6 relative z-10">
              <h3 className="text-xl font-bold text-white flex items-center gap-3">
                <span className="w-1.5 h-6 bg-gradient-to-b from-synapse-primary to-synapse-secondary rounded-full block shadow-[0_0_10px_rgba(139,92,246,0.5)]"></span>
                Central de Ingestão
              </h3>
              <div className="relative group/select">
                <select
                  value={selectedProfile}
                  onChange={e => setSelectedProfile(e.target.value)}
                  className="appearance-none bg-[#0d1117] border border-white/20 text-white text-sm rounded-lg pl-4 pr-10 py-2.5 focus:ring-2 focus:ring-synapse-primary/50 focus:border-synapse-primary outline-none cursor-pointer transition-all hover:border-synapse-primary/50 shadow-lg min-w-[200px]"
                >
                  {profiles.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400 group-hover/select:text-synapse-primary transition-colors">▼</div>
              </div>
            </div>

            <div
              className={`h-64 flex flex-col items-center justify-center transition-all duration-300 border-2 border-dashed rounded-xl relative overflow-hidden ${isDragging ? 'border-synapse-emerald bg-synapse-emerald/5 scale-[0.99] shadow-[inset_0_0_30px_rgba(16,185,129,0.1)]' : 'border-white/10 hover:border-synapse-primary/30 hover:bg-white/5'}`}
              onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={e => {
                e.preventDefault();
                setIsDragging(false);
                if (e.dataTransfer.files.length > 1) {
                  // Bulk Mode
                  setBatchFiles(Array.from(e.dataTransfer.files));
                  setShowBatchModal(true);
                } else if (e.dataTransfer.files[0]) {
                  // Single Mode
                  handleUpload(e.dataTransfer.files[0]);
                }
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                id="file-input"
                type="file"
                multiple
                className="hidden"
                onChange={e => {
                  const files = e.target.files;
                  if (files && files.length > 1) {
                    // Múltiplos arquivos -> abre BatchUploadModal
                    setBatchFiles(Array.from(files));
                    setShowBatchModal(true);
                  } else if (files && files[0]) {
                    // Um arquivo -> upload direto
                    handleUpload(files[0]);
                  }
                  // Reset input para permitir selecionar o mesmo arquivo novamente
                  e.target.value = '';
                }}
                accept=".mp4,.mov,.avi"
              />

              <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-4 transition-all duration-500 shadow-xl z-10 ${isDragging ? 'bg-synapse-emerald/20 text-synapse-emerald scale-110' : 'bg-[#1c2128] text-gray-500 group-hover:text-white'}`}>
                {uploadStatus === 'uploading' ? (
                  <CloudArrowUpIcon className="w-10 h-10 animate-bounce" />
                ) : (
                  <PlayCircleIcon className="w-10 h-10" />
                )}
              </div>

              <div className="text-lg font-medium text-gray-300 z-10 text-center">
                {uploadStatus === 'uploading' ? (
                  <span className="flex flex-col items-center gap-2">
                    <span className="animate-pulse text-synapse-primary font-mono">Enviando... {uploadProgress}%</span>
                    <span className="w-48 h-1.5 bg-gray-700 rounded-full overflow-hidden mt-2">
                      <span className="block h-full bg-synapse-primary transition-all duration-300" style={{ width: `${uploadProgress}%` }}></span>
                    </span>
                  </span>
                ) : (
                  <>
                    <span className="group-hover:text-white transition-colors">Arraste seu vídeo aqui</span>
                    <p className="text-sm text-gray-500 mt-2">ou clique para selecionar do computador</p>
                  </>
                )}
              </div>
            </div>
          </StitchCard>

          {/* 🎵 AUDIO SUGGESTION - Mostra após upload */}
          {showAudioSuggestion && audioSuggestions.length > 0 && (
            <StitchCard className="p-4 relative backdrop-blur-sm border-purple-500/30">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎵</span>
                  <h4 className="text-sm font-bold text-white">Sugestão de Música IA</h4>
                  <span className="text-[10px] px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded-full font-mono">
                    para {lastUploadedFile}
                  </span>
                </div>
                <button
                  onClick={() => setShowAudioSuggestion(false)}
                  className="text-gray-500 hover:text-white transition-colors"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>

              <AudioSuggestionCard
                suggestion={audioSuggestions[0]}
                onSelect={(selected) => {
                  toast.success(`🎵 Música "${selected.title}" selecionada!`);
                  setShowAudioSuggestion(false);
                  // TODO: Associar música ao vídeo recém-uploadado
                }}
                onDismiss={() => setShowAudioSuggestion(false)}
                compact={false}
              />
            </StitchCard>
          )}

          {/* PENDING LIST */}
          <StitchCard className="p-6 relative backdrop-blur-sm">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <ClockIcon className="w-5 h-5 text-synapse-primary" /> Fila de Aprovação
              </h3>
              {pendingVideos.length > 0 && (
                <span className="animate-pulse text-xs px-2 py-0.5 rounded-full bg-synapse-primary/20 text-synapse-primary border border-synapse-primary/30 font-bold">
                  ATIVO
                </span>
              )}

              {pendingVideos.length > 0 && (
                <div className="flex items-center gap-2 ml-auto">
                  <label className="flex items-center gap-2 text-xs text-gray-400 hover:text-white cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={pendingVideos.length > 0 && selectedItems.size === pendingVideos.length}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 rounded border-gray-600 bg-black/50 text-synapse-primary focus:ring-synapse-primary focus:ring-offset-0"
                    />
                    Selecionar Tudo
                  </label>
                </div>
              )}
            </div>
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
              {pendingVideos.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500 border-2 border-dashed border-white/10 rounded-lg">
                  <CheckCircleIcon className="w-10 h-10 mb-2 opacity-20" />
                  <p>Nenhum vídeo aguardando aprovação.</p>
                </div>
              ) : (
                pendingVideos.map(v => (
                  <div key={v.id} className={clsx("p-4 border rounded-lg flex items-center gap-4 transition-all group",
                    selectedItems.has(v.id) ? 'bg-synapse-primary/10 border-synapse-primary/50' : 'bg-black/40 border-white/5 hover:border-synapse-primary/30'
                  )}>
                    <input
                      type="checkbox"
                      checked={selectedItems.has(v.id)}
                      onChange={() => toggleSelection(v.id)}
                      className="w-5 h-5 rounded border-gray-600 bg-black/50 text-synapse-primary focus:ring-synapse-primary focus:ring-offset-0 cursor-pointer"
                    />
                    <div className="w-12 h-12 rounded-lg bg-gray-900 flex items-center justify-center text-xl shrink-0 border border-gray-800 group-hover:border-synapse-primary/30 transition-colors">🎬</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate group-hover:text-synapse-primary transition-colors">{v.metadata.original_filename}</p>
                      <p className="text-xs text-gray-500 font-mono mt-0.5 flex items-center gap-2">
                        <span className="bg-white/10 px-1 rounded text-[10px]">{v.metadata.profile_id}</span>
                        {formatDate(v.uploaded_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 opacity-80 group-hover:opacity-100 transition-opacity">
                      <NeonButton variant="ghost" className="text-xs h-8 text-synapse-emerald hover:text-white hover:bg-synapse-emerald border-synapse-emerald/30" onClick={() => handleApprove(v)}>APROVAR</NeonButton>
                      <button onClick={() => handleReject(v.id)} className="p-1.5 rounded-md bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white transition-all"><XMarkIcon className="w-4 h-4" /></button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* BULK ACTION BAR */}
            {selectedItems.size > 0 && (
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-[#1c2128] border border-white/20 rounded-xl shadow-2xl p-2 flex items-center gap-2 animate-in slide-in-from-bottom-5 fade-in duration-300 z-20">
                <span className="px-3 text-xs font-bold text-gray-400 border-r border-gray-700">{selectedItems.size} selecionados</span>
                <NeonButton variant="ghost" className="text-xs h-8 text-synapse-emerald hover:bg-synapse-emerald hover:text-black" onClick={handleBulkApprove}>Aprovar</NeonButton>
                <NeonButton variant="danger" className="text-xs h-8" onClick={handleBulkReject}>Excluir</NeonButton>
              </div>
            )}
          </StitchCard>
        </div>

        {/* RIGHT COLUMN: PROFILES */}
        <div className="xl:col-span-1 flex flex-col gap-4">
          <StitchCard className="p-5">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
              <span className="w-1.5 h-4 bg-gradient-to-b from-synapse-cyan to-synapse-emerald rounded-full"></span>
              Perfis TikTok
            </h3>
            <div className="space-y-3">
              {profiles.length === 0 ? (
                <div className="text-center py-8 text-gray-600 text-sm">
                  Nenhum perfil cadastrado
                </div>
              ) : (
                profiles.map(p => (
                  <div
                    key={p.id}
                    onClick={() => setSelectedProfile(p.id)}
                    className={clsx(
                      "p-3 rounded-xl border cursor-pointer transition-all group",
                      selectedProfile === p.id
                        ? "bg-synapse-primary/10 border-synapse-primary/50 shadow-[0_0_15px_rgba(139,92,246,0.15)]"
                        : "bg-black/30 border-white/5 hover:border-white/20 hover:bg-white/5"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className={clsx(
                        "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all",
                        selectedProfile === p.id
                          ? "bg-synapse-primary/20 border-synapse-primary text-synapse-primary"
                          : "bg-gray-800 border-gray-700 text-gray-400 group-hover:border-synapse-primary/50"
                      )}>
                        {p.avatar_url ? (
                          <img src={p.avatar_url} alt={p.label} className="w-full h-full rounded-full object-cover" />
                        ) : (
                          p.label.charAt(0).toUpperCase()
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={clsx(
                          "text-sm font-medium truncate transition-colors",
                          selectedProfile === p.id ? "text-white" : "text-gray-300 group-hover:text-white"
                        )}>
                          {p.label}
                        </p>
                        <p className="text-[10px] text-gray-500 font-mono">@{p.username || p.id}</p>
                      </div>
                      {selectedProfile === p.id && (
                        <div className="w-2 h-2 rounded-full bg-synapse-primary animate-pulse shadow-[0_0_8px_rgba(139,92,246,0.8)]"></div>
                      )}
                    </div>

                    {/* Quick Stats */}
                    <div className="mt-2 pt-2 border-t border-white/5 grid grid-cols-2 gap-2">
                      <div className="text-center">
                        <p className="text-[10px] text-gray-500 uppercase">Agendados</p>
                        <p className="text-sm font-bold text-synapse-cyan">
                          {scheduledEvents.filter(e => e.profile_id === p.id).length}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-[10px] text-gray-500 uppercase">Status</p>
                        <p className="text-[10px] px-2 py-0.5 rounded-full bg-synapse-emerald/20 text-synapse-emerald inline-block font-bold">
                          ATIVO
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </StitchCard>

          {/* Próximas Transmissões */}
          <StitchCard className="p-5">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
              <ClockIcon className="w-4 h-4 text-synapse-amber" />
              Próximos Posts
            </h3>
            <div className="space-y-2">
              {scheduledEvents.slice(0, 3).map((event, i) => (
                <div key={event.id || i} className="flex items-center gap-3 p-2 rounded-lg bg-black/30 border border-white/5">
                  <div className="w-8 h-8 rounded bg-synapse-amber/10 flex items-center justify-center text-synapse-amber text-xs font-mono">
                    {new Date(event.scheduled_time).getHours().toString().padStart(2, '0')}:{new Date(event.scheduled_time).getMinutes().toString().padStart(2, '0')}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-white truncate">{event.video_path?.split(/[/\\]/).pop() || 'Vídeo'}</p>
                    <p className="text-[10px] text-gray-500">{event.profile_id}</p>
                  </div>
                </div>
              ))}
              {scheduledEvents.length === 0 && (
                <p className="text-center text-gray-600 text-sm py-4">Nenhum agendamento</p>
              )}
              {scheduledEvents.length > 3 && (
                <p className="text-center text-synapse-primary text-xs cursor-pointer hover:underline">
                  +{scheduledEvents.length - 3} mais
                </p>
              )}
            </div>
          </StitchCard>
        </div>
      </div>

      {/* APPROVAL MODAL */}
      {
        showApprovalModal && selectedVideo && (
          <div className="fixed inset-0 bg-[#05040a]/80 backdrop-blur-md z-[100] flex items-center justify-center fade-in p-4">
            <StitchCard className="w-full max-w-md bg-[#161b22] border-synapse-primary/30 p-6 shadow-2xl relative overflow-hidden">
              {/* Top Border Gradient */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-synapse-primary to-synapse-secondary"></div>
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
                <button onClick={() => setPostType('immediate')} className={`p-4 rounded-xl border transition-all relative overflow-hidden group ${postType === 'immediate' ? 'border-synapse-emerald bg-synapse-emerald/5' : 'border-gray-700 bg-gray-800/50 hover:border-gray-500'}`}>
                  {postType === 'immediate' && <div className="absolute top-2 right-2 text-synapse-emerald"><CheckCircleIcon className="w-5 h-5" /></div>}
                  <div className={`font-bold mb-1 ${postType === 'immediate' ? 'text-synapse-emerald' : 'text-gray-300'}`}>Imediato</div>
                  <div className="text-xs text-gray-500">Publicar agora</div>
                </button>

                <button onClick={() => setPostType('scheduled')} className={`p-4 rounded-xl border transition-all relative overflow-hidden group ${postType === 'scheduled' ? 'border-synapse-primary bg-synapse-primary/5' : 'border-gray-700 bg-gray-800/50 hover:border-gray-500'}`}>
                  {postType === 'scheduled' && <div className="absolute top-2 right-2 text-synapse-primary"><CheckCircleIcon className="w-5 h-5" /></div>}
                  <div className={`font-bold mb-1 ${postType === 'scheduled' ? 'text-synapse-primary' : 'text-gray-300'}`}>Agendar</div>
                  <div className="text-xs text-gray-500">Escolher data/hora</div>
                </button>
              </div>

              {/* Viral Music Toggle */}
              <div className={`p-4 rounded-xl border mb-6 transition-all cursor-pointer select-none ${viralMusicEnabled ? 'bg-synapse-purple/10 border-synapse-purple' : 'bg-black/40 border-gray-700 hover:border-gray-500'}`} onClick={() => setViralMusicEnabled(!viralMusicEnabled)}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${viralMusicEnabled ? 'bg-synapse-purple text-white shadow-[0_0_15px_rgba(192,132,252,0.5)]' : 'bg-gray-800 text-gray-400'}`}>
                      🎵
                    </div>
                    <div>
                      <h4 className={`text-sm font-bold ${viralMusicEnabled ? 'text-white' : 'text-gray-400'}`}>Viral Boost</h4>
                      <p className="text-xs text-gray-500">Adicionar música em alta (Mudo)</p>
                    </div>
                  </div>
                  <div className={`w-6 h-6 rounded border flex items-center justify-center transition-colors ${viralMusicEnabled ? 'bg-synapse-purple border-synapse-purple' : 'border-gray-600'}`}>
                    {viralMusicEnabled && <CheckCircleIcon className="w-4 h-4 text-white" />}
                  </div>
                </div>
              </div>

              {/* Privacy Selector */}
              <div className="mb-6">
                <label className="text-xs text-gray-500 font-bold mb-2 block uppercase tracking-wider">Privacidade</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'public_to_everyone', label: 'Todos', icon: '🌍' },
                    { id: 'mutual_follow_friends', label: 'Amigos', icon: '👥' },
                    { id: 'self_only', label: 'Somente Eu', icon: '🔒' }
                  ].map(opt => (
                    <button
                      key={opt.id}
                      onClick={() => setPrivacyLevel(opt.id)}
                      className={`p-2 rounded-lg border text-xs font-bold flex flex-col items-center gap-1 transition-all ${privacyLevel === opt.id ? 'bg-synapse-primary/20 border-synapse-primary text-synapse-primary' : 'bg-black/40 border-gray-700 text-gray-400 hover:border-gray-500'}`}
                    >
                      <span className="text-lg">{opt.icon}</span>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {postType === 'scheduled' && (
                <div className="space-y-3 mb-6 animate-pulse-slow bg-white/5 p-4 rounded-xl border border-white/10">
                  <div>
                    <label className="text-xs text-gray-500 font-bold mb-1 block">DATA</label>
                    <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} className="w-full bg-black/50 border border-gray-600 rounded-lg p-2.5 text-white outline-none focus:border-synapse-primary transition-colors" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 font-bold mb-1 block">HORÁRIO</label>
                    <input type="time" value={selectedTime} onChange={e => setSelectedTime(e.target.value)} className="w-full bg-black/50 border border-gray-600 rounded-lg p-2.5 text-white outline-none focus:border-synapse-primary transition-colors" />
                  </div>
                </div>
              )}

              <div className="flex gap-3 mt-8">
                <NeonButton variant="ghost" onClick={() => setShowApprovalModal(false)} className="flex-1">Cancelar</NeonButton>
                <NeonButton onClick={handleConfirmApproval} className="flex-1 shadow-lg shadow-purple-500/20">
                  {postType === 'immediate' ? 'Publicar Agora' : 'Confirmar Agendamento'}
                </NeonButton>
              </div>
            </StitchCard>
          </div>
        )
      }

      {/* CONFIRM MODAL */}
      {
        confirmModal.isOpen && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 fade-in">
            <StitchCard className="w-[400px] bg-[#161b22] border-synapse-border p-6 shadow-2xl scale-in">
              <h3 className="text-lg font-bold text-white mb-4">{confirmModal.title}</h3>
              <div className="flex justify-end gap-3">
                <NeonButton variant="ghost" onClick={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}>
                  Cancelar
                </NeonButton>
                <NeonButton
                  variant={confirmModal.type === 'delete' ? 'danger' : 'primary'}
                  onClick={confirmModal.onConfirm}
                >
                  {confirmModal.type === 'delete' ? 'Confirmar Exclusão' : 'Confirmar'}
                </NeonButton>
              </div>
            </StitchCard>
          </div>
        )
      }

      {/* BATCH UPLOAD MODAL */}
      <MetricsModal
        isOpen={isMetricsModalOpen}
        onClose={() => setIsMetricsModalOpen(false)}
        initialTab={metricsModalTab}
      />
      <BatchUploadModal
        isOpen={showBatchModal}
        onClose={() => { setShowBatchModal(false); setBatchFiles([]); }}
        onSuccess={() => { toast.success("Campanha agendada com sucesso!"); fetchAllData(); }}
        profiles={profiles}
        initialFiles={batchFiles}
      />

    </>
  );
}
