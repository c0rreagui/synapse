'use client';

import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import {
  PlayCircleIcon, CpuChipIcon, CheckCircleIcon,
  ExclamationTriangleIcon, ClockIcon, XCircleIcon, ArrowPathIcon
} from '@heroicons/react/24/outline';

// Types
interface Profile { id: string; label: string; }
interface IngestionStatus { queued: number; processing: number; completed: number; failed: number; }
interface ContentItem { filename: string; path?: string; }

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
    const interval = setInterval(fetchAllData, 5000);
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

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0d1117', color: '#c9d1d9', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <Sidebar />

      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed', top: '24px', right: '24px', zIndex: 1000,
          padding: '12px 20px', borderRadius: '8px',
          backgroundColor: toast.type === 'success' ? '#238636' : toast.type === 'error' ? '#da3633' : '#1f6feb',
          color: '#fff', fontSize: '14px', fontWeight: 500,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          animation: 'slideIn 0.3s ease'
        }}>
          {toast.message}
        </div>
      )}

      <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
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
            <button onClick={fetchAllData} title="Atualizar dados" aria-label="Atualizar dados" style={{ padding: '10px', borderRadius: '8px', backgroundColor: 'transparent', border: '1px solid #30363d', cursor: 'pointer' }}>
              <ArrowPathIcon style={{ width: '20px', height: '20px', color: '#8b949e' }} />
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', borderRadius: '8px', backgroundColor: backendOnline ? 'rgba(63,185,80,0.15)' : 'rgba(248,81,73,0.15)', border: `1px solid ${backendOnline ? 'rgba(63,185,80,0.3)' : 'rgba(248,81,73,0.3)'}` }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: backendOnline ? '#3fb950' : '#f85149', animation: backendOnline ? 'pulse 2s infinite' : 'none' }} />
              <span style={{ fontSize: '12px', fontWeight: 600, color: backendOnline ? '#3fb950' : '#f85149', textTransform: 'uppercase' }}>{backendOnline ? 'Online' : 'Offline'}</span>
            </div>
          </div>
        </header>

        {/* Pipeline Status */}
        <section style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#fff', margin: 0 }}>Pipeline Status</h3>
            <span style={{ fontSize: '12px', color: '#8b949e', fontFamily: 'monospace' }}>Atualiza a cada 5s</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            {[
              { icon: ClockIcon, label: 'Na Fila', value: ingestionStatus.queued, accent: '#d29922' },
              { icon: CpuChipIcon, label: 'Processando', value: ingestionStatus.processing, accent: '#58a6ff' },
              { icon: CheckCircleIcon, label: 'Concluídos', value: ingestionStatus.completed, accent: '#3fb950' },
              { icon: XCircleIcon, label: 'Falhas', value: ingestionStatus.failed, accent: '#f85149' },
            ].map((card, i) => (
              <div key={i} style={{ padding: '20px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d', transition: 'transform 0.2s, box-shadow 0.2s' }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = `0 4px 12px ${card.accent}20`; }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: `${card.accent}15`, border: `1px solid ${card.accent}30`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <card.icon style={{ width: '20px', height: '20px', color: card.accent }} />
                  </div>
                  <span style={{ fontSize: '10px', color: '#8b949e', fontFamily: 'monospace', textTransform: 'uppercase' }}>{card.label}</span>
                </div>
                <p style={{ fontSize: '36px', fontWeight: 'bold', color: '#fff', margin: 0 }}>{card.value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Main Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Upload Zone */}
          <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#fff', margin: 0 }}>Central de Ingestão</h3>
                <p style={{ fontSize: '12px', color: '#8b949e', margin: '4px 0 0' }}>Arraste vídeos ou clique para upload</p>
              </div>
              <select
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
                title="Selecionar perfil de destino"
                aria-label="Selecionar perfil de destino"
                style={{ padding: '10px 14px', borderRadius: '8px', backgroundColor: '#161b22', border: '1px solid #30363d', color: '#c9d1d9', fontSize: '14px', cursor: 'pointer' }}
              >
                {profiles.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
              </select>
            </div>

            {/* Drop Zone */}
            <div
              style={{
                position: 'relative', width: '100%', height: '200px',
                border: `2px dashed ${isDragging ? '#3fb950' : uploadStatus === 'success' ? '#3fb950' : '#30363d'}`,
                borderRadius: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                backgroundColor: isDragging ? 'rgba(63,185,80,0.05)' : 'transparent',
                transition: 'all 0.3s ease', cursor: 'pointer'
              }}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => { e.preventDefault(); setIsDragging(false); if (e.dataTransfer.files?.[0]) handleUpload(e.dataTransfer.files[0]); }}
            >
              <input type="file" title="Selecionar arquivo de vídeo" aria-label="Selecionar arquivo de vídeo" style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])} accept=".mp4,.mov,.avi,.webm" />
              <PlayCircleIcon style={{ width: '56px', height: '56px', color: isDragging ? '#3fb950' : uploadStatus === 'uploading' ? '#58a6ff' : '#8b949e', marginBottom: '12px', transition: 'color 0.3s' }} />
              <p style={{ fontSize: '16px', color: isDragging ? '#3fb950' : '#8b949e', margin: 0, fontWeight: 500 }}>
                {uploadStatus === 'uploading' ? '⏳ Enviando...' : uploadStatus === 'success' ? '✓ Sucesso!' : 'Solte seu vídeo aqui'}
              </p>
              <p style={{ fontSize: '12px', color: '#8b949e', margin: '8px 0 0' }}>MP4, MOV, AVI, WebM</p>
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

          {/* Right Panel */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Profiles */}
            <div style={{ padding: '20px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff', margin: '0 0 16px' }}>Perfis Ativos</h3>
              {profiles.length > 0 ? profiles.map((profile, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', borderRadius: '8px', backgroundColor: '#161b22', border: '1px solid #30363d', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '18px' }}>{getProfileIcon(profile.id)}</span>
                    <div>
                      <p style={{ fontSize: '13px', color: '#fff', margin: 0 }}>{profile.label}</p>
                      <p style={{ fontSize: '10px', color: '#8b949e', fontFamily: 'monospace', margin: 0 }}>{profile.id}</p>
                    </div>
                  </div>
                  <span style={{ fontSize: '9px', color: '#3fb950', fontFamily: 'monospace', padding: '2px 6px', backgroundColor: 'rgba(63,185,80,0.15)', borderRadius: '4px' }}>ATIVO</span>
                </div>
              )) : (
                <p style={{ fontSize: '12px', color: '#8b949e' }}>Nenhum perfil</p>
              )}
            </div>

            {/* Ready Content */}
            <div style={{ padding: '20px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#fff', margin: '0 0 16px' }}>Conteúdo Pronto</h3>
              {readyContent.length > 0 ? readyContent.slice(0, 5).map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px', borderRadius: '6px', backgroundColor: '#161b22', marginBottom: '6px' }}>
                  <CheckCircleIcon style={{ width: '14px', height: '14px', color: '#3fb950' }} />
                  <span style={{ fontSize: '11px', color: '#c9d1d9', fontFamily: 'monospace' }}>{item.filename}</span>
                </div>
              )) : (
                <p style={{ fontSize: '12px', color: '#8b949e' }}>Nenhum conteúdo</p>
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
