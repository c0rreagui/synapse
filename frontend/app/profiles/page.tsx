'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import {
    ArrowLeftIcon, CheckCircleIcon, PlusIcon, TrashIcon, UserGroupIcon
} from '@heroicons/react/24/outline';

interface Profile {
    id: string;
    label: string;
    avatar_url?: string;
    username?: string;
    icon?: string;
}

const API_BASE = 'http://localhost:8000/api/v1';

export default function ProfilesPage() {
    const [profiles, setProfiles] = useState<Profile[]>([]);
    const [loading, setLoading] = useState(true);
    const [showImportModal, setShowImportModal] = useState(false);
    const [importLabel, setImportLabel] = useState('');
    const [importCookies, setImportCookies] = useState('');
    const [error, setError] = useState<string | null>(null);

    async function fetchProfiles() {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE}/profiles/list`);
            if (!res.ok) throw new Error('Falha ao carregar perfis');
            setProfiles(await res.json());
        } catch (err) {
            console.error(err);
            setError('Não foi possível conectar ao servidor. Verifique se o backend está rodando.');
        }
        setLoading(false);
    }

    useEffect(() => {
        fetchProfiles();
    }, []);

    const handleImport = async () => {
        if (!importLabel || !importCookies) return;

        try {
            // Validate JSON basics
            JSON.parse(importCookies);

            const res = await fetch(`${API_BASE}/profiles/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ label: importLabel, cookies: importCookies })
            });

            if (res.ok) {
                setShowImportModal(false);
                setImportLabel('');
                setImportCookies('');
                fetchProfiles(); // Refresh list
            } else {
                const err = await res.json();
                alert(`Erro: ${err.detail}`);
            }
        } catch (e) {
            console.error(e);
            alert('JSON inválido ou erro de conexão.');
        }
    };

    const getProfileIcon = (id: string, customIcon?: string) => {
        if (customIcon && customIcon !== "👤") return customIcon;
        if (id.includes('01')) return '✂️';
        if (id.includes('02')) return '🔥';
        return '👤';
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0d1117', color: '#c9d1d9', fontFamily: 'Inter, system-ui, sans-serif' }}>
            <Sidebar />

            {/* MAIN */}
            <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
                <header style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                    <Link href="/">
                        <div style={{ width: '40px', height: '40px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #30363d', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
                            <ArrowLeftIcon style={{ width: '20px', height: '20px', color: '#8b949e' }} />
                        </div>
                    </Link>
                    <div>
                        <h2 style={{ fontSize: '24px', fontWeight: 'bold', color: '#fff', margin: 0 }}>Perfis TikTok</h2>
                        <p style={{ fontSize: '12px', color: '#8b949e', margin: 0 }}>Gerenciar sessões de upload</p>
                    </div>
                </header>

                {error && (
                    <div style={{ padding: '16px', marginBottom: '24px', borderRadius: '8px', backgroundColor: 'rgba(248,81,73,0.1)', border: '1px solid #f85149', color: '#f85149' }}>
                        {error}
                    </div>
                )}

                {/* Profiles Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                    {loading ? (
                        <p style={{ color: '#8b949e' }}>Carregando perfis...</p>
                    ) : profiles.length > 0 ? (
                        profiles.map((profile, i) => (
                            <div key={i} style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d', position: 'relative' }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        {/* Avatar Logic */}
                                        {profile.avatar_url ? (
                                            <img
                                                src={profile.avatar_url}
                                                alt={profile.label}
                                                style={{ width: '48px', height: '48px', borderRadius: '50%', objectFit: 'cover', backgroundColor: '#30363d' }}
                                            />
                                        ) : (
                                            <span style={{ fontSize: '32px' }}>{getProfileIcon(profile.id, profile.icon)}</span>
                                        )}

                                        <div>
                                            <h3 style={{ fontSize: '16px', color: '#fff', margin: 0 }}>{profile.label}</h3>
                                            {profile.username && (
                                                <p style={{ fontSize: '12px', color: '#8b949e', margin: '2px 0 0' }}>@{profile.username}</p>
                                            )}
                                            <p style={{ fontSize: '10px', color: '#484f58', fontFamily: 'monospace', margin: '4px 0 0' }}>{profile.id}</p>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 8px', borderRadius: '4px', backgroundColor: 'rgba(63,185,80,0.15)' }}>
                                        <CheckCircleIcon style={{ width: '14px', height: '14px', color: '#3fb950' }} />
                                        <span style={{ fontSize: '10px', color: '#3fb950', fontWeight: 600 }}>ATIVO</span>
                                    </div>
                                </div>


                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                                    <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#161b22' }}>
                                        <p style={{ fontSize: '10px', color: '#8b949e', margin: 0 }}>SESSÃO</p>
                                        <p style={{ fontSize: '14px', color: '#fff', margin: '4px 0 0' }}>Válida</p>
                                    </div>
                                    <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: '#161b22' }}>
                                        <p style={{ fontSize: '10px', color: '#8b949e', margin: 0 }}>UPLOADS</p>
                                        <p style={{ fontSize: '14px', color: '#fff', margin: '4px 0 0' }}>—</p>
                                    </div>
                                </div>

                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button style={{ flex: 1, padding: '10px', borderRadius: '8px', backgroundColor: '#238636', border: 'none', color: '#fff', fontSize: '14px', cursor: 'pointer' }}>
                                        Usar Perfil
                                    </button>

                                    {/* Validate Button */}
                                    <button
                                        onClick={async () => {
                                            const btn = document.getElementById(`validate-${i}`);
                                            if (btn) btn.innerText = "⏳";
                                            try {
                                                const res = await fetch(`${API_BASE}/profiles/validate/${profile.id}`, { method: 'POST' });
                                                if (res.ok) fetchProfiles();
                                                else alert('Erro ao validar.');
                                            } catch {
                                                alert('Erro de conexão.');
                                            }
                                            if (btn) btn.innerHTML = `🔄`;
                                        }}
                                        id={`validate-${i}`}
                                        title="Atualizar dados do TikTok"
                                        style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #30363d', color: '#8b949e', cursor: 'pointer' }}
                                    >
                                        🔄
                                    </button>

                                    <button title="Excluir perfil" aria-label="Excluir perfil" style={{ padding: '10px', borderRadius: '8px', backgroundColor: '#1c2128', border: '1px solid #30363d', color: '#8b949e', cursor: 'pointer' }}>
                                        <TrashIcon style={{ width: '16px', height: '16px' }} />
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div style={{ padding: '48px', textAlign: 'center', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                            <UserGroupIcon style={{ width: '48px', height: '48px', color: '#8b949e', margin: '0 auto 16px' }} />
                            <p style={{ color: '#8b949e', margin: 0 }}>Nenhum perfil encontrado</p>
                            <p style={{ fontSize: '12px', color: '#8b949e', margin: '8px 0 0' }}>Adicione sessões TikTok em backend/data/sessions/</p>
                        </div>
                    )}

                    {/* Add Profile Card */}
                    <div
                        onClick={() => setShowImportModal(true)}
                        style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '2px dashed #30363d', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '200px', cursor: 'pointer', transition: 'all 0.2s' }}
                    >
                        <PlusIcon style={{ width: '32px', height: '32px', color: '#8b949e', marginBottom: '12px' }} />
                        <p style={{ color: '#8b949e', margin: 0 }}>Importar Novo Perfil</p>
                    </div>
                </div>

                {/* Import Modal */}
                {
                    showImportModal && (
                        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                            <div style={{ width: '500px', backgroundColor: '#161b22', borderRadius: '12px', border: '1px solid #30363d', padding: '24px' }}>
                                <h3 style={{ margin: '0 0 16px', color: '#fff' }}>Importar Cookies</h3>

                                <div style={{ marginBottom: '16px' }}>
                                    <label style={{ display: 'block', color: '#8b949e', fontSize: '12px', marginBottom: '8px' }}>Nome do Perfil</label>
                                    <input
                                        type="text"
                                        value={importLabel}
                                        onChange={(e) => setImportLabel(e.target.value)}
                                        placeholder="Ex: Canal de Cortes"
                                        style={{ width: '100%', padding: '12px', borderRadius: '6px', backgroundColor: '#0d1117', border: '1px solid #30363d', color: '#fff' }}
                                    />
                                </div>

                                <div style={{ marginBottom: '24px' }}>
                                    <label style={{ display: 'block', color: '#8b949e', fontSize: '12px', marginBottom: '8px' }}>JSON de Cookies (EditThisCookie)</label>
                                    <textarea
                                        value={importCookies}
                                        onChange={(e) => setImportCookies(e.target.value)}
                                        placeholder='[{"domain": ".tiktok.com", ...}]'
                                        style={{ width: '100%', height: '150px', padding: '12px', borderRadius: '6px', backgroundColor: '#0d1117', border: '1px solid #30363d', color: '#fff', fontFamily: 'monospace', fontSize: '12px' }}
                                    />
                                </div>

                                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                                    <button onClick={() => setShowImportModal(false)} style={{ padding: '8px 16px', borderRadius: '6px', backgroundColor: 'transparent', border: '1px solid #30363d', color: '#c9d1d9', cursor: 'pointer' }}>
                                        Cancelar
                                    </button>
                                    <button onClick={handleImport} style={{ padding: '8px 16px', borderRadius: '6px', backgroundColor: '#238636', border: 'none', color: '#fff', cursor: 'pointer' }}>
                                        Importar
                                    </button>
                                </div>
                            </div>
                        </div>
                    )
                }
            </main >
        </div >
    );
}

