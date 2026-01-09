'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import CommandCenter from './components/CommandCenter';
import Toast from './components/Toast';
import ConnectionStatus from './components/ConnectionStatus';
import CommandPalette from './components/CommandPalette';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import useWebSocket from './hooks/useWebSocket';
import {
  PlayCircleIcon, CpuChipIcon, CheckCircleIcon,
  ClockIcon, XCircleIcon, XMarkIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

// Types
interface Profile { id: string; label: string; icon?: string; avatar_url?: string; username?: string; }
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


const API_BASE = 'http://localhost:8000/api/v1';

export default function Home() {
  // State Definitions
  const [ingestionStatus, setIngestionStatus] = useState<IngestionStatus>({ queued: 0, processing: 0, completed: 0, failed: 0 });
  const [pendingVideos, setPendingVideos] = useState<PendingVideo[]>([]);
  // const [completedVideos, setCompletedVideos] = useState<CompletedVideo[]>([]);
  // const [readyContent, setReadyContent] = useState<ContentItem[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);

  // UI State
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [toast, setToast] = useState<{ message: string; type: string; duration?: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Skeleton Component
  const SkeletonLine = ({ width = '100%', height = '14px', marginBottom = '8px' }) => (
    <div className="skeleton-pulse" style={{ width, height, marginBottom, backgroundColor: '#30363d', borderRadius: '4px' }} />
  );

  // Modal State
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<PendingVideo | null>(null);
  const [postType, setPostType] = useState<'immediate' | 'scheduled'>('immediate');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('12:00');
  // const [submitting, setSubmitting] = useState(false);


  // System State
  const [backendOnline, setBackendOnline] = useState(false);
  const [lastUpdate, setLastUpdate] = useState('');
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  // WebSocket for real-time updates
  const { isConnected: wsConnected } = useWebSocket({
    onPipelineUpdate: (data) => {
      setIngestionStatus(data as IngestionStatus);
      setLastUpdate(new Date().toLocaleTimeString());
    },
  });

  // Helper: Show Toast
  const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info', duration = 3000) => {
    setToast({ message, type, duration });
    if (duration > 0) setTimeout(() => setToast(null), duration + 300); // Cleanup callback handled by Toast component effectively, but explicit nulling good for React state
  };


  // Fetch Data
  const fetchAllData = useCallback(async () => {
    try {
      setLastUpdate(new Date().toLocaleTimeString());

      // Check Health
      const healthRes = await fetch('http://localhost:8000/');
      setBackendOnline(healthRes.ok);
      if (!healthRes.ok) return;

      // Status
      const statusRes = await fetch(`${API_BASE}/ingest/status`);
      if (statusRes.ok) setIngestionStatus(await statusRes.json());

      // Queue (Pending)
      const queueRes = await fetch(`${API_BASE}/queue/pending`);
      if (queueRes.ok) {
        const data = await queueRes.json();
        setPendingVideos(data);

      }

      // Profiles
      const profilesRes = await fetch(`${API_BASE}/profiles/list`);
      if (profilesRes.ok) {
        const profs = await profilesRes.json();
        setProfiles(profs);
        if (!selectedProfile && profs.length > 0) setSelectedProfile(profs[0].id);
      }

      // Completed/Scheduled (Mock or from an endpoint if available, but let's assume we fetch logs or keep local state for now? 
      // Actually, completed videos should ideally come from an API. 
      // For now, I'll mock the 'completedVideos' list based on what we see in code or fetch if endpoint exists.
      // Assuming a /queue/history or similar might exist, or we just rely on IngestionStatus for numbers and mock the list for UI demo)
      // I will add a safe fetch for history if it existed, otherwise empty list is fine, user can see numbers.
      // Wait, the previous code had `completedVideos` state. Let's keep it empty or mock it for now to avoid errors.
      // Actually, I'll mock a few if backend is online to show the UI.
      if (healthRes.ok) {
        // setCompletedVideos([...]); // We don't have a history endpoint yet, keep empty or implementing later.
      }

    } catch (e) {
      setBackendOnline(false);
    } finally {
      setIsLoading(false);
    }
  }, [selectedProfile]);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  // Command Palette Hooks
  const commands = [
    { id: 'upload', title: 'Upload Video', key: 'u', description: 'Upload Video', action: () => document.getElementById('file-input')?.click() },
    { id: 'refresh', title: 'Refresh Data', key: 'r', description: 'Refresh Data', action: fetchAllData },
    { id: 'profiles', title: 'Manage Profiles', key: 'p', description: 'Manage Profiles', action: () => { } }
  ];
  useKeyboardShortcuts(commands);

  // Upload handler
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

  // Approval handlers
  const handleApprove = (video: PendingVideo) => {
    setSelectedVideo(video);
    setShowApprovalModal(true);
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setSelectedDate(tomorrow.toISOString().split('T')[0]);
  };

  const handleReject = async (videoId: string) => {
    if (!confirm('Tem certeza que deseja rejeitar este vídeo?')) return;
    try {
      await fetch(`${API_BASE}/queue/${videoId}`, { method: 'DELETE' });
      fetchAllData();
      showToast('Vídeo rejeitado', 'info');
    } catch {
      showToast('Erro ao rejeitar vídeo', 'error');
    }
  };

  const handleConfirmApproval = async () => {
    if (!selectedVideo) return;
    // setSubmitting(true); // removed unused
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
        showToast(postType === 'immediate' ? 'Vídeo aprovado!' : `Agendado para ${selectedDate} às ${selectedTime}`, 'success');
      } else throw new Error('Falha');
    } catch {
      showToast('Erro ao aprovar vídeo', 'error');
    } finally {
      // Clean up submitting state if needed
    }
  };



  // Derived

  const timeOptions = [];
  for (let h = 0; h < 24; h++) for (let m = 0; m < 60; m += 5) timeOptions.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0d1117', color: '#c9d1d9', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Sidebar />
      {toast && <Toast message={toast.message} type={toast.type as any} duration={toast.duration} onClose={() => setToast(null)} />}
      <CommandPalette isOpen={showCommandPalette} onClose={() => setShowCommandPalette(false)} commands={commands} />

      <main style={{ flex: 1, padding: '24px', overflowY: 'auto', maxHeight: '100vh' }}>

        {/* COMMAND CENTER */}
        <CommandCenter scheduledVideos={[]} />

        <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: backendOnline ? 'var(--cmd-green-bg)' : 'var(--cmd-red-bg)', border: `1px solid ${backendOnline ? 'var(--cmd-green-border)' : 'var(--cmd-red-border)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CpuChipIcon style={{ width: '28px', height: '28px', color: backendOnline ? 'var(--cmd-green)' : 'var(--cmd-red)' }} />
            </div>
            <div>
              <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#fff', margin: 0 }}>Dashboard</h2>
              <p style={{ fontSize: '12px', color: '#8b949e', margin: 0 }}>Última atualização: {lastUpdate || '...'}</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button onClick={() => setShowCommandPalette(true)} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', borderRadius: '8px', backgroundColor: 'transparent', border: '1px solid var(--cmd-border)', cursor: 'pointer', color: 'var(--cmd-text-muted)', fontSize: '13px' }}>
              <MagnifyingGlassIcon style={{ width: 16 }} /> Buscar... <span style={{ fontSize: '10px', background: '#21262d', padding: '2px 6px', borderRadius: '4px' }}>Ctrl+K</span>
            </button>
            <ConnectionStatus isOnline={backendOnline} lastUpdate={lastUpdate} />
          </div>
        </header>

        {/* Pipeline Status */}
        <section style={{ marginBottom: '32px' }} className="fade-in">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 className="gradient-text" style={{ fontSize: '20px', fontWeight: 700, margin: 0 }}>Pipeline Status</h3>
            <span style={{ fontSize: '12px', color: '#8b949e', fontFamily: 'monospace' }}>⚡ Atualiza a cada 5s</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            {[
              { icon: ClockIcon, label: 'Na Fila', value: ingestionStatus.queued, accent: 'var(--cmd-yellow)' },
              { icon: CpuChipIcon, label: 'Processando', value: ingestionStatus.processing, accent: 'var(--cmd-blue)' },
              { icon: CheckCircleIcon, label: 'Concluídos', value: ingestionStatus.completed, accent: 'var(--cmd-green)' },
              { icon: XCircleIcon, label: 'Falhas', value: ingestionStatus.failed, accent: 'var(--cmd-red)' },
            ].map((card, i) => (
              <div key={i} className={`stat-card fade-in stagger-${i + 1}`} style={{ '--stat-accent': card.accent, padding: '24px' } as any}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div className="icon-container" style={{ background: `linear-gradient(135deg, ${card.accent}30 0%, ${card.accent}10 100%)`, borderColor: `${card.accent}50` }}>
                    <card.icon style={{ width: '24px', height: '24px', color: card.accent }} />
                  </div>
                  <span style={{ fontSize: '11px', color: '#8b949e', fontFamily: 'monospace', textTransform: 'uppercase' }}>{card.label}</span>
                </div>
                <p className="count-animation" style={{ fontSize: '42px', fontWeight: 800, color: '#fff', margin: 0 }}>{card.value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Main Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Upload & Pending */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-card fade-in" style={{ padding: '28px' }}>
              {/* ... Upload UI ... */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div><h3 className="gradient-text" style={{ fontSize: '20px', fontWeight: 700, margin: 0 }}>🎬 Central de Ingestão</h3></div>
                <select value={selectedProfile} onChange={e => setSelectedProfile(e.target.value)} className="glass-card" style={{ padding: '12px', background: 'rgba(22,27,34,0.9)', color: '#c9d1d9' }}>{profiles.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}</select>
              </div>
              <div className={`upload-zone ${isDragging ? 'active' : ''}`} style={{ position: 'relative', height: '220px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '2px dashed #30363d', borderRadius: '12px' }} onDragOver={e => { e.preventDefault(); setIsDragging(true) }} onDragLeave={() => setIsDragging(false)} onDrop={e => { e.preventDefault(); setIsDragging(false); if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]) }}>
                <input type="file" style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} onChange={e => e.target.files?.[0] && handleUpload(e.target.files[0])} accept=".mp4,.mov,.avi" />
                <PlayCircleIcon style={{ width: 64, height: 64, color: isDragging ? '#3fb950' : '#6e7681', marginBottom: 16 }} />
                <p style={{ fontSize: 18, color: '#c9d1d9', fontWeight: 600 }}>{uploadStatus === 'uploading' ? 'Enviando...' : 'Solte seu vídeo aqui'}</p>
              </div>
            </div>

            {/* Pending List */}
            <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: 'var(--cmd-card)', border: '1px solid var(--cmd-purple-bg)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}><ClockIcon style={{ width: 18, color: '#a371f7' }} /> <h3>Aprovação Manual</h3></div>
                {/* Mass Approval Button Removed as Logic is WIP/Unused */}
              </div>
              {isLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[1, 2, 3].map(i => (
                    <div key={i} style={{ padding: 14, background: '#161b22', border: '1px solid #30363d', borderRadius: 10, display: 'flex', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <SkeletonLine width="60%" />
                        <SkeletonLine width="30%" height="10px" marginBottom="0" />
                      </div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <SkeletonLine width="60px" height="32px" marginBottom="0" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : pendingVideos.length === 0 ? <p style={{ textAlign: 'center', color: '#8b949e' }}>Nenhum vídeo pendente</p> :
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {pendingVideos.map(v => (
                    <div key={v.id} style={{ padding: 14, background: '#161b22', border: '1px solid #30363d', borderRadius: 10, display: 'flex', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <p style={{ color: '#fff', fontWeight: 500 }}>{v.metadata.original_filename}</p>
                        <p style={{ fontSize: 10, color: '#8b949e' }}>{v.metadata.profile_id}</p>
                      </div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button onClick={() => handleApprove(v)} style={{ padding: '8px 12px', borderRadius: 6, background: 'var(--gradient-brand)', border: 'none', color: '#fff' }}>Aprovar</button>
                        <button onClick={() => handleReject(v.id)} style={{ padding: '8px 12px', borderRadius: 6, background: 'rgba(248,81,73,0.15)', border: '1px solid rgba(248,81,73,0.4)', color: '#f85149' }}><XMarkIcon style={{ width: 14 }} /></button>
                      </div>
                    </div>
                  ))}
                </div>
              }
            </div>
          </div>

          {/* Right Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div className="glass-card fade-in" style={{ padding: 20 }}>
              <h3>👤 Perfis Ativos</h3>
              {profiles.map(p => (
                <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 10, marginBottom: 10 }}>
                  {/* Avatar Logic */}
                  {p.avatar_url ? (
                    <img
                      src={p.avatar_url}
                      alt={p.label}
                      style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover', backgroundColor: '#30363d' }}
                    />
                  ) : (
                    <span style={{ fontSize: 24 }}>{p.icon || '👤'}</span>
                  )}
                  <div>
                    <p style={{ color: '#fff', fontWeight: 500, margin: 0 }}>{p.label}</p>
                    {p.username && <p style={{ fontSize: 11, color: '#8b949e', margin: 0 }}>@{p.username}</p>}
                    <p style={{ fontSize: 10, color: '#484f58', margin: '2px 0 0', fontFamily: 'monospace' }}>{p.id}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </main >

      {/* Modals */}
      {
        showApprovalModal && selectedVideo && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
            <div style={{ width: 450, padding: 28, background: '#1c2128', border: '1px solid #30363d', borderRadius: 16 }}>
              <h2 style={{ color: '#fff' }}>Aprovar Vídeo</h2>
              <div style={{ display: 'flex', gap: 12, margin: '20px 0' }}>
                <button onClick={() => setPostType('immediate')} style={{ flex: 1, padding: 14, borderRadius: 10, border: postType === 'immediate' ? '2px solid #3fb950' : '2px solid #30363d', color: postType === 'immediate' ? '#3fb950' : '#8b949e' }}>Imediato</button>
                <button onClick={() => setPostType('scheduled')} style={{ flex: 1, padding: 14, borderRadius: 10, border: postType === 'scheduled' ? '2px solid #a371f7' : '2px solid #30363d', color: postType === 'scheduled' ? '#a371f7' : '#8b949e' }}>Agendar</button>
              </div>
              {postType === 'scheduled' && (
                <div style={{ marginBottom: 20 }}>
                  <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} style={{ width: '100%', padding: 12, background: '#161b22', border: '1px solid #30363d', color: '#fff', marginBottom: 10 }} />
                  <select value={selectedTime} onChange={e => setSelectedTime(e.target.value)} style={{ width: '100%', padding: 12, background: '#161b22', border: '1px solid #30363d', color: '#fff' }}>
                    {timeOptions.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              )}
              <div style={{ display: 'flex', gap: 12 }}>
                <button onClick={() => setShowApprovalModal(false)} style={{ flex: 1, padding: 14, background: '#30363d', border: 'none', color: '#c9d1d9' }}>Cancelar</button>
                <button onClick={handleConfirmApproval} style={{ flex: 1, padding: 14, background: 'var(--gradient-brand)', border: 'none', color: '#fff' }}>Confirmar</button>
              </div>
            </div>
          </div>
        )
      }

      <style jsx global>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes shimmer { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
        * { box-sizing: border-box; }
        body { margin: 0; }
        .fade-in { animation: pulse 0.5s ease-in; }
        .skeleton-pulse { animation: shimmer 1.5s infinite ease-in-out; }
        .glass-card { background: rgba(22, 27, 34, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(48, 54, 61, 0.5); border-radius: 12px; }
        .gradient-text { background: linear-gradient(135deg, #fff 0%, #8b949e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
      `}</style>
    </div >
  );
}
