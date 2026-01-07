'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import {
    ArrowLeftIcon, CheckCircleIcon, PlusIcon, TrashIcon, UserGroupIcon
} from '@heroicons/react/24/outline';

interface Profile { id: string; label: string; }

const API_BASE = 'http://localhost:8000/api/v1';

export default function ProfilesPage() {
    const [profiles, setProfiles] = useState<Profile[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchProfiles() {
            try {
                const res = await fetch(`${API_BASE}/profiles/list`);
                if (res.ok) setProfiles(await res.json());
            } catch { /* Backend offline */ }
            setLoading(false);
        }
        fetchProfiles();
    }, []);

    const getProfileIcon = (id: string) => {
        if (id.includes('01')) return '✂️';
        if (id.includes('02')) return '🔥';
        return '📹';
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

                {/* Profiles Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                    {loading ? (
                        <p style={{ color: '#8b949e' }}>Carregando perfis...</p>
                    ) : profiles.length > 0 ? (
                        profiles.map((profile, i) => (
                            <div key={i} style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '1px solid #30363d' }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <span style={{ fontSize: '32px' }}>{getProfileIcon(profile.id)}</span>
                                        <div>
                                            <h3 style={{ fontSize: '16px', color: '#fff', margin: 0 }}>{profile.label}</h3>
                                            <p style={{ fontSize: '12px', color: '#8b949e', fontFamily: 'monospace', margin: '4px 0 0' }}>{profile.id}</p>
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
                    <div style={{ padding: '24px', borderRadius: '12px', backgroundColor: '#1c2128', border: '2px dashed #30363d', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '200px', cursor: 'pointer' }}>
                        <PlusIcon style={{ width: '32px', height: '32px', color: '#8b949e', marginBottom: '12px' }} />
                        <p style={{ color: '#8b949e', margin: 0 }}>Adicionar Novo Perfil</p>
                    </div>
                </div>
            </main>
        </div>
    );
}
