'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Toast from './components/Toast';
import ConnectionStatus from './components/ConnectionStatus';
import EmptyState from './components/EmptyState';
import CommandPalette from './components/CommandPalette';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import {
  PlayCircleIcon, CpuChipIcon, CheckCircleIcon,
  ExclamationTriangleIcon, ClockIcon, XCircleIcon, ArrowPathIcon, CalendarIcon, XMarkIcon,
  MagnifyingGlassIcon, Cog6ToothIcon, PlusCircleIcon, DocumentIcon
} from '@heroicons/react/24/outline';

// Types
interface Profile { id: string; label: string; }
interface IngestionStatus { queued: number; processing: number; completed: number; failed: number; }
interface ContentItem { filename: string; path?: string; }
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

interface CompletedVideo {
  id: string;
  filename: string;
  status: 'completed' | 'scheduled';
  caption?: string;
  profile?: string;
  schedule_time?: string;
  processed_at: string;
}

const API_BASE = 'http://localhost:8000/api/v1';

export default function Home() {
  // State
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [ingestionStatus, setIngestionStatus] = useState<IngestionStatus>({ queued: 0, processing: 0, completed: 0, failed: 0 });
  const [readyContent, setReadyContent] = useState<ContentItem[]>([]);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [isDragging, setIsDragging] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [recentUploads, setRecentUploads] = useState<{ name: string, time: string }[]>([]);
  const [toast, setToast] = useState<{ message: string, type: 'success' | 'error' | 'info' } | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [pendingVideos, setPendingVideos] = useState<PendingVideo[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<PendingVideo | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [postType, setPostType] = useState<'immediate' | 'scheduled'>('immediate');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('12:00');
  const [submitting, setSubmitting] = useState(false);
  const [completedVideos, setCompletedVideos] = useState<CompletedVideo[]>([]);
  const [showCommandPalette, setShowCommandPalette] = useState(false);

  // Keyboard shortcuts
  useKeyboardShortcuts([
    { key: 'k', ctrl: true, action: () => setShowCommandPalette(true), description: 'Abrir Command Palette' },
    { key: 'r', ctrl: true, action: () => fetchAllData(), description: 'Atualizar dados' },
  ]);

  // Command Palette commands
  const commands = [
    { id: 'refresh', title: 'Atualizar Dados', shortcut: 'Ctrl+R', icon: <ArrowPathIcon style={{ width: 18, height: 18 }} />, action: () => fetchAllData(), category: 'Ações' },
    { id: 'upload', title: 'Upload de Vídeo', icon: <PlusCircleIcon style={{ width: 18, height: 18 }} />, action: () => document.getElementById('file-input')?.click(), category: 'Ações' },
    { id: 'queue', title: 'Ver Fila de Aprovação', icon: <DocumentIcon style={{ width: 18, height: 18 }} />, action: () => window.location.href = '/queue', category: 'Navegação' },
    { id: 'logs', title: 'Ver Logs', icon: <DocumentIcon style={{ width: 18, height: 18 }} />, action: () => window.location.href = '/logs', category: 'Navegação' },
    { id: 'settings', title: 'Configurações', icon: <Cog6ToothIcon style={{ width: 18, height: 18 }} />, action: () => window.location.href = '/settings', category: 'Navegação' },
  ];

  // Show toast notification
  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    try {
      const healthRes = await fetch(`${API_BASE.replace('/api/v1', '')}/health`);
      setBackendOnline(healthRes.ok);

      const profilesRes = await fetch(`${API_BASE}/profiles/list`);
      if (profilesRes.ok) {
        const data = await profilesRes.json();
        setProfiles(data);
        if (data.length > 0 && !selectedProfile) setSelectedProfile(data[0].id);
      }

      const statusRes = await fetch(`${API_BASE}/ingest/status`);
      if (statusRes.ok) setIngestionStatus(await statusRes.json());

      const readyRes = await fetch(`${API_BASE}/content/ready`);
      if (readyRes.ok) setReadyContent(await readyRes.json());

      const pendingRes = await fetch(`${API_BASE}/queue/pending`);
      if (pendingRes.ok) {
        const pendingData = await pendingRes.json();
        setPendingCount(pendingData.length);
        setPendingVideos(pendingData);
      }

      // Fetch completed/scheduled videos
      const videosRes = await fetch(`${API_BASE}/videos/completed`);
      if (videosRes.ok) {
        setCompletedVideos(await videosRes.json());
      }

      setLastUpdate(new Date().toLocaleTimeString('pt-BR'));
    } catch {
      setBackendOnline(false);
    }
  }, [selectedProfile]);

  // Initial fetch on mount
  useEffect(() => {
    fetchAllData(); // Valid pattern: initial data fetch on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Polling interval
  useEffect(() => {
    const interval = setInterval(fetchAllData, 15000); // 15 seconds
    return () => clearInterval(interval);
  }, [fetchAllData]);

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
        setRecentUploads(prev => [{ name: file.name, time: 'agora' }, ...prev.slice(0, 4)]);
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

  const getProfileIcon = (id: string) => {
    if (id.includes('01') || id.toLowerCase().includes('corte')) return '✂️';
    if (id.includes('02') || id.toLowerCase().includes('ibope')) return '🔥';
    return '📹';
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
    setSubmitting(true);
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
        showToast(postType === 'immediate' ? 'Vídeo aprovado! Bot iniciando...' : `Agendado para ${selectedDate} às ${selectedTime}`, 'success');
      } else throw new Error('Falha');
    } catch {
      showToast('Erro ao aprovar vídeo', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  // Generate time options (5-min intervals)
  const timeOptions: string[] = [];
  for (let h = 0; h < 24; h++) {
    for (let m = 0; m < 60; m += 5) {
      timeOptions.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0d1117', color: '#c9d1d9', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Sidebar />

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type as 'success' | 'error' | 'info' | 'warning'}
          onClose={() => setToast(null)}
        />
      )}

      {/* Command Palette */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        commands={commands}
      />

      <main style={{ flex: 1, padding: '24px', overflowY: 'auto', maxHeight: '100vh' }}>
        {/* Header */}
        <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', backgroundColor: backendOnline ? 'rgba(63,185,80,0.1)' : 'rgba(248,81,73,0.1)', border: `1px solid ${backendOnline ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CpuChipIcon style={{ width: '28px', height: '28px', color: backendOnline ? '#3fb950' : '#f85149' }} />
            </div>
            <div>
              <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#fff', margin: 0 }}>Command Center</h2>
              <p style={{ fontSize: '12px', color: '#8b949e', margin: 0 }}>Última atualização: {lastUpdate || 'Carregando...'}</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Command Palette Trigger */}
            <button
              onClick={() => setShowCommandPalette(true)}
              title="Buscar comandos (Ctrl+K)"
              aria-label="Buscar comandos"
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                padding: '8px 14px', borderRadius: '8px',
                backgroundColor: 'transparent', border: '1px solid #30363d',
                cursor: 'pointer', color: '#8b949e', fontSize: '13px'
              }}
            >
              <MagnifyingGlassIcon style={{ width: '16px', height: '16px' }} />
              <span>Buscar...</span>
              <span style={{ fontSize: '10px', padding: '2px 6px', backgroundColor: '#21262d', borderRadius: '4px' }}>Ctrl+K</span>
            </button>
            <button onClick={fetchAllData} title="Atualizar dados (Ctrl+R)" aria-label="Atualizar dados" style={{ padding: '10px', borderRadius: '8px', backgroundColor: 'transparent', border: '1px solid #30363d', cursor: 'pointer' }}>
              <ArrowPathIcon style={{ width: '20px', height: '20px', color: '#8b949e' }} />
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
              { icon: ClockIcon, label: 'Na Fila', value: ingestionStatus.queued, accent: '#d29922' },
              { icon: CpuChipIcon, label: 'Processando', value: ingestionStatus.processing, accent: '#58a6ff' },
              { icon: CheckCircleIcon, label: 'Concluídos', value: ingestionStatus.completed, accent: '#3fb950' },
              { icon: XCircleIcon, label: 'Falhas', value: ingestionStatus.failed, accent: '#f85149' },
            ].map((card, i) => (
              <div
                key={i}
                className={`stat-card fade-in stagger-${i + 1}`}
                style={{
                  '--stat-accent': card.accent,
                  padding: '24px',
                } as React.CSSProperties}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div className="icon-container" style={{
                    background: `linear-gradient(135deg, ${card.accent}30 0%, ${card.accent}10 100%)`,
                    borderColor: `${card.accent}50`,
                  }}>
                    <card.icon style={{ width: '24px', height: '24px', color: card.accent }} />
                  </div>
                  <span style={{ fontSize: '11px', color: '#8b949e', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{card.label}</span>
                </div>
                <p className="count-animation" style={{ fontSize: '42px', fontWeight: 800, color: '#fff', margin: 0, letterSpacing: '-0.02em' }}>{card.value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Main Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Left Column - Upload + Pending */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Upload Zone Card */}
            <div className="glass-card fade-in" style={{ padding: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <h3 className="gradient-text" style={{ fontSize: '20px', fontWeight: 700, margin: 0 }}>🎬 Central de Ingestão</h3>
                  <p style={{ fontSize: '12px', color: '#8b949e', margin: '4px 0 0' }}>Arraste vídeos ou clique para upload</p>
                </div>
                <select
                  value={selectedProfile}
                  onChange={(e) => setSelectedProfile(e.target.value)}
                  title="Selecionar perfil de destino"
                  aria-label="Selecionar perfil de destino"
                  className="glass-card"
                  style={{ padding: '12px 16px', backgroundColor: 'rgba(22, 27, 34, 0.9)', color: '#c9d1d9', fontSize: '14px', cursor: 'pointer', fontWeight: 500 }}
                >
                  {profiles.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
              </div>

              {/* Drop Zone */}
              <div
                className={`upload-zone ${isDragging ? 'active' : ''}`}
                style={{
                  position: 'relative', width: '100%', height: '220px',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer'
                }}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={(e) => { e.preventDefault(); setIsDragging(false); if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]); }}
              >
                <input id="file-input" type="file" title="Selecionar arquivo de vídeo" aria-label="Selecionar arquivo de vídeo" style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} accept=".mp4,.mov,.avi,.webm" />
                <div className={isDragging ? 'float-animation' : ''}>
                  <PlayCircleIcon style={{ width: '64px', height: '64px', color: isDragging ? '#3fb950' : uploadStatus === 'uploading' ? '#58a6ff' : '#6e7681', marginBottom: '16px', transition: 'color 0.3s' }} />
                </div>
                <p style={{ fontSize: '18px', color: isDragging ? '#3fb950' : '#c9d1d9', margin: 0, fontWeight: 600 }}>
                  {uploadStatus === 'uploading' ? '⏳ Enviando...' : uploadStatus === 'success' ? '✓ Upload Completo!' : 'Solte seu vídeo aqui'}
                </p>
                <p style={{ fontSize: '13px', color: '#6e7681', margin: '8px 0 0' }}>MP4, MOV, AVI, WebM • Máx 500MB</p>
              </div>

              {/* Recent Uploads */}
              <div style={{ borderTop: '1px solid #30363d', marginTop: '24px', paddingTop: '16px' }}>
                <p style={{ fontSize: '10px', color: '#8b949e', fontFamily: 'monospace', marginBottom: '12px' }}>UPLOADS RECENTES</p>
                {recentUploads.length > 0 ? recentUploads.map((upload, i) => (
                  <p key={i} style={{ fontSize: '12px', color: '#c9d1d9', fontFamily: 'monospace', margin: '6px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ color: '#3fb950' }}>●</span> {upload.name} <span style={{ color: '#8b949e' }}>— {upload.time}</span>
                  </p>
                )) : (
                  <p style={{ fontSize: '12px', color: '#8b949e' }}>Nenhum upload recente</p>
                )}
              </div>
            </div>

            {/* Pending Approval Card */}
            <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid rgba(163,113,247,0.3)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: 'rgba(163,113,247,0.15)', border: '1px solid rgba(163,113,247,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ClockIcon style={{ width: '18px', height: '18px', color: '#a371f7' }} />
                  </div>
                  <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff', margin: 0 }}>Aprovação Manual</h3>
                </div>
                {pendingCount > 0 && (
                  <span style={{ fontSize: '11px', color: '#a371f7', fontFamily: 'monospace', padding: '4px 10px', backgroundColor: 'rgba(163,113,247,0.15)', borderRadius: '6px' }}>
                    {pendingCount} pendente{pendingCount !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
              {pendingVideos.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px 0' }}>
                  <p style={{ fontSize: '13px', color: '#8b949e', margin: 0 }}>Nenhum vídeo aguardando aprovação</p>
                  <p style={{ fontSize: '11px', color: '#6e7681', margin: '6px 0 0' }}>Uploads aparecerão aqui</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {pendingVideos.map((video) => (
                    <div key={video.id} style={{ padding: '14px', borderRadius: '10px', backgroundColor: '#161b22', border: '1px solid #30363d' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                        <div style={{ flex: 1 }}>
                          <p style={{ fontSize: '13px', color: '#fff', margin: 0, fontWeight: 500 }}>{video.metadata.original_filename || video.filename}</p>
                          <p style={{ fontSize: '10px', color: '#8b949e', margin: '4px 0 0' }}>Perfil: {video.metadata.profile_id || video.profile}</p>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button onClick={() => handleApprove(video)} style={{ flex: 1, padding: '8px 12px', borderRadius: '6px', background: 'linear-gradient(135deg, #238636, #1f6feb)', border: 'none', color: '#fff', fontSize: '12px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                          <CheckCircleIcon style={{ width: '14px', height: '14px' }} /> Aprovar
                        </button>
                        <button onClick={() => handleReject(video.id)} title="Rejeitar vídeo" aria-label="Rejeitar vídeo" style={{ padding: '8px 12px', borderRadius: '6px', backgroundColor: 'rgba(248,81,73,0.15)', border: '1px solid rgba(248,81,73,0.4)', color: '#f85149', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
                          <XMarkIcon style={{ width: '14px', height: '14px' }} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Profiles */}
            <div className="glass-card fade-in" style={{ padding: '20px' }}>
              <h3 className="gradient-text" style={{ fontSize: '16px', fontWeight: 700, margin: '0 0 16px' }}>👤 Perfis Ativos</h3>
              {profiles.length > 0 ? profiles.map((profile, i) => (
                <div key={i} className="video-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '24px' }}>{getProfileIcon(profile.id)}</span>
                    <div>
                      <p style={{ fontSize: '14px', color: '#fff', margin: 0, fontWeight: 500 }}>{profile.label}</p>
                      <p style={{ fontSize: '11px', color: '#6e7681', fontFamily: 'monospace', margin: 0 }}>{profile.id}</p>
                    </div>
                  </div>
                  <span className="profile-badge">ATIVO</span>
                </div>
              )) : (
                <EmptyState
                  title="Nenhum perfil"
                  description="Adicione perfis na página de configurações"
                  action={{ label: 'Adicionar Perfil', onClick: () => window.location.href = '/profiles' }}
                />
              )}
            </div>

            {/* Ready Content */}
            <div className="glass-card fade-in stagger-2" style={{ padding: '20px' }}>
              <h3 className="gradient-text" style={{ fontSize: '16px', fontWeight: 700, margin: '0 0 16px' }}>✅ Conteúdo Pronto</h3>
              {readyContent.length > 0 ? readyContent.slice(0, 5).map((item, i) => (
                <div key={i} className="video-card" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', marginBottom: '8px' }}>
                  <CheckCircleIcon style={{ width: '16px', height: '16px', color: '#3fb950' }} />
                  <span style={{ fontSize: '12px', color: '#c9d1d9', fontFamily: 'monospace' }}>{item.filename}</span>
                </div>
              )) : (
                <EmptyState
                  title="Nenhum conteúdo"
                  description="Faça upload de vídeos para começar"
                />
              )}
            </div>

            {/* Vídeos Processados/Agendados */}
            <div style={{ padding: '20px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff', margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CalendarIcon style={{ width: '18px', height: '18px', color: '#58a6ff' }} />
                Vídeos Recentes
              </h3>
              {completedVideos.length > 0 ? completedVideos.slice(0, 6).map((video, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px',
                  borderRadius: '8px',
                  backgroundColor: '#161b22',
                  border: '1px solid #30363d',
                  marginBottom: '8px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, overflow: 'hidden' }}>
                    {video.status === 'scheduled' ? (
                      <ClockIcon style={{ width: '16px', height: '16px', color: '#f0883e', flexShrink: 0 }} />
                    ) : (
                      <CheckCircleIcon style={{ width: '16px', height: '16px', color: '#3fb950', flexShrink: 0 }} />
                    )}
                    <div style={{ overflow: 'hidden' }}>
                      <p style={{ fontSize: '11px', color: '#c9d1d9', margin: 0, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                        {video.caption || video.filename}
                      </p>
                      <p style={{ fontSize: '9px', color: '#8b949e', margin: '2px 0 0', fontFamily: 'monospace' }}>
                        {video.profile && `@${video.profile} · `}
                        {video.schedule_time
                          ? `📅 ${new Date(video.schedule_time).toLocaleDateString('pt-BR')} ${new Date(video.schedule_time).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`
                          : new Date(video.processed_at).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  </div>
                  <span style={{
                    fontSize: '8px',
                    fontFamily: 'monospace',
                    padding: '3px 6px',
                    borderRadius: '4px',
                    backgroundColor: video.status === 'scheduled' ? 'rgba(240,136,62,0.15)' : 'rgba(63,185,80,0.15)',
                    color: video.status === 'scheduled' ? '#f0883e' : '#3fb950',
                    flexShrink: 0
                  }}>
                    {video.status === 'scheduled' ? 'AGENDADO' : 'PUBLICADO'}
                  </span>
                </div>
              )) : (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <p style={{ fontSize: '12px', color: '#8b949e', margin: 0 }}>Nenhum vídeo processado</p>
                  <p style={{ fontSize: '10px', color: '#6e7681', margin: '4px 0 0' }}>Uploads aparecerão aqui</p>
                </div>
              )}
            </div>

            {/* Backend Alert */}
            {!backendOnline && (
              <div style={{ padding: '16px', borderRadius: '12px', backgroundColor: 'rgba(248,81,73,0.1)', border: '1px solid rgba(248,81,73,0.3)' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <ExclamationTriangleIcon style={{ width: '18px', height: '18px', color: '#f85149', flexShrink: 0 }} />
                  <div>
                    <p style={{ fontSize: '13px', color: '#f85149', margin: 0, fontWeight: 500 }}>Backend Offline</p>
                    <p style={{ fontSize: '10px', color: '#8b949e', margin: '4px 0 0' }}>uvicorn app.main:app --reload</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Approval Modal */}
      {showApprovalModal && selectedVideo && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ width: '100%', maxWidth: '450px', padding: '28px', borderRadius: '16px', backgroundColor: '#1c2128', border: '1px solid #30363d', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#fff', margin: '0 0 6px' }}>Aprovar Vídeo</h2>
            <p style={{ fontSize: '12px', color: '#8b949e', margin: '0 0 20px' }}>{selectedVideo.metadata.original_filename}</p>

            <p style={{ fontSize: '13px', color: '#fff', fontWeight: 600, marginBottom: '12px' }}>Tipo de Postagem</p>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
              <button onClick={() => setPostType('immediate')} style={{ flex: 1, padding: '14px', borderRadius: '10px', border: postType === 'immediate' ? '2px solid #3fb950' : '2px solid #30363d', backgroundColor: postType === 'immediate' ? 'rgba(63,185,80,0.15)' : 'transparent', color: postType === 'immediate' ? '#3fb950' : '#8b949e', fontWeight: 600, cursor: 'pointer' }}>Post Imediato</button>
              <button onClick={() => setPostType('scheduled')} style={{ flex: 1, padding: '14px', borderRadius: '10px', border: postType === 'scheduled' ? '2px solid #a371f7' : '2px solid #30363d', backgroundColor: postType === 'scheduled' ? 'rgba(163,113,247,0.15)' : 'transparent', color: postType === 'scheduled' ? '#a371f7' : '#8b949e', fontWeight: 600, cursor: 'pointer' }}>Agendar</button>
            </div>

            {postType === 'scheduled' && (
              <div style={{ padding: '16px', borderRadius: '10px', backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid #30363d', marginBottom: '20px' }}>
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#fff', fontWeight: 500, marginBottom: '8px' }}>
                    <CalendarIcon style={{ width: '16px', height: '16px', color: '#a371f7' }} /> Data
                  </label>
                  <input type="date" title="Selecionar data de agendamento" aria-label="Data de agendamento" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} min={new Date().toISOString().split('T')[0]} style={{ width: '100%', padding: '12px', borderRadius: '8px', backgroundColor: '#161b22', border: '1px solid #30363d', color: '#fff', fontSize: '14px' }} />
                </div>
                <div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#fff', fontWeight: 500, marginBottom: '8px' }}>
                    <ClockIcon style={{ width: '16px', height: '16px', color: '#58a6ff' }} /> Horário (múltiplos de 5min)
                  </label>
                  <select title="Selecionar horário de agendamento" aria-label="Horário de agendamento" value={selectedTime} onChange={(e) => setSelectedTime(e.target.value)} style={{ width: '100%', padding: '12px', borderRadius: '8px', backgroundColor: '#161b22', border: '1px solid #30363d', color: '#fff', fontSize: '14px' }}>
                    {timeOptions.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button onClick={() => { setShowApprovalModal(false); setSelectedVideo(null); }} disabled={submitting} style={{ flex: 1, padding: '14px', borderRadius: '10px', backgroundColor: '#30363d', border: 'none', color: '#c9d1d9', fontWeight: 600, cursor: 'pointer' }}>Cancelar</button>
              <button onClick={handleConfirmApproval} disabled={submitting || (postType === 'scheduled' && !selectedDate)} style={{ flex: 1, padding: '14px', borderRadius: '10px', background: 'linear-gradient(135deg, #238636, #1f6feb)', border: 'none', color: '#fff', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                {submitting ? 'Processando...' : <><CheckCircleIcon style={{ width: '16px', height: '16px' }} /> Confirmar</>}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx global>{`
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        * { box-sizing: border-box; }
        body { margin: 0; }
        select:focus { outline: none; border-color: #58a6ff; }
      `}</style>
    </div>
  );
}
