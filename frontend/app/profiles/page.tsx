'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import { TikTokProfile } from '../types';
import useWebSocket from '../hooks/useWebSocket';
import {
    ArrowLeftIcon, CheckCircleIcon, PlusIcon, TrashIcon, UserGroupIcon, ArrowPathIcon
} from '@heroicons/react/24/outline';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import clsx from 'clsx';

const API_BASE = 'http://localhost:8000/api/v1';

export default function ProfilesPage() {
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
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

    useWebSocket({
        onProfileChange: (updatedProfile) => {
            setProfiles(prev => {
                const idx = prev.findIndex(p => p.id === updatedProfile.id);
                if (idx === -1) return [...prev, updatedProfile];
                const newArr = [...prev];
                newArr[idx] = updatedProfile;
                return newArr;
            });
        }
    });

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
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans selection:bg-synapse-primary selection:text-white">
            <Sidebar />

            {/* MAIN */}
            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern">
                <header className="flex items-center gap-4 mb-8">
                    <Link href="/">
                        <div className="w-10 h-10 rounded-lg bg-[#1c2128] border border-white/10 flex items-center justify-center cursor-pointer hover:border-synapse-primary/50 transition-colors group">
                            <ArrowLeftIcon className="w-5 h-5 text-gray-400 group-hover:text-synapse-primary" />
                        </div>
                    </Link>
                    <div>
                        <h2 className="text-2xl font-bold text-white m-0">Perfis TikTok</h2>
                        <p className="text-sm text-gray-500 m-0">Gerenciar sessões de upload</p>
                    </div>
                </header>

                {error && (
                    <StitchCard className="p-4 mb-6 !bg-red-500/10 !border-red-500/30 text-red-400">
                        {error}
                    </StitchCard>
                )}

                {/* Profiles Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {loading ? (
                        <p className="text-gray-500 col-span-full text-center py-12">Carregando perfis...</p>
                    ) : profiles.length > 0 ? (
                        profiles.map((profile, i) => (
                            <StitchCard key={i} className="p-6 relative group">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        {/* Avatar Logic */}
                                        {profile.avatar_url ? (
                                            <img
                                                src={profile.avatar_url}
                                                alt={profile.label}
                                                className="w-12 h-12 rounded-full object-cover bg-[#30363d] ring-2 ring-transparent group-hover:ring-synapse-primary/50 transition-all"
                                            />
                                        ) : (
                                            <span className="text-4xl">{getProfileIcon(profile.id, profile.icon)}</span>
                                        )}

                                        <div>
                                            <h3 className="text-base font-bold text-white m-0">{profile.label}</h3>
                                            {profile.username && (
                                                <p className="text-xs text-gray-400 m-0 mt-0.5">@{profile.username}</p>
                                            )}
                                            <p className="text-[10px] text-gray-600 font-mono m-0 mt-1">{profile.id}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-synapse-emerald/15 border border-synapse-emerald/20">
                                        <CheckCircleIcon className="w-3.5 h-3.5 text-synapse-emerald" />
                                        <span className="text-[10px] text-synapse-emerald font-bold">ATIVO</span>
                                    </div>
                                </div>


                                <div className="grid grid-cols-2 gap-3 mb-4">
                                    <div className="p-3 rounded-lg bg-black/30 border border-white/5">
                                        <p className="text-[10px] text-gray-500 m-0 uppercase font-mono">SESSÃO</p>
                                        <p className="text-sm text-white font-medium m-0 mt-1">Válida</p>
                                    </div>
                                    <div className="p-3 rounded-lg bg-black/30 border border-white/5">
                                        <p className="text-[10px] text-gray-500 m-0 uppercase font-mono">UPLOADS</p>
                                        <p className="text-sm text-white font-medium m-0 mt-1">—</p>
                                    </div>
                                </div>

                                <div className="flex gap-2">
                                    <NeonButton variant="primary" className="flex-1 text-xs">
                                        Usar Perfil
                                    </NeonButton>

                                    {/* Refresh Avatar Button */}
                                    <button
                                        onClick={async () => {
                                            const btn = document.getElementById(`validate-${i}`);
                                            if (btn) btn.classList.add('animate-spin');
                                            try {
                                                const res = await fetch(`${API_BASE}/profiles/refresh-avatar/${profile.id}`, { method: 'POST' });
                                                if (res.ok) fetchProfiles();
                                                else alert('Erro ao atualizar avatar.');
                                            } catch {
                                                alert('Erro de conexão.');
                                            }
                                            if (btn) btn.classList.remove('animate-spin');
                                        }}
                                        className="p-2.5 rounded-lg bg-[#1c2128] border border-white/10 text-gray-400 hover:text-white hover:border-synapse-primary/50 transition-all"
                                        title="Atualizar avatar do TikTok"
                                    >
                                        <ArrowPathIcon id={`validate-${i}`} className="w-4 h-4" />
                                    </button>

                                    <button
                                        title="Excluir perfil"
                                        className="p-2.5 rounded-lg bg-[#1c2128] border border-white/10 text-gray-400 hover:text-red-400 hover:border-red-500/50 transition-all"
                                    >
                                        <TrashIcon className="w-4 h-4" />
                                    </button>
                                </div>
                            </StitchCard>
                        ))
                    ) : (
                        <StitchCard className="p-12 text-center col-span-full flex flex-col items-center justify-center">
                            <UserGroupIcon className="w-12 h-12 text-gray-600 mb-4" />
                            <p className="text-gray-400 m-0">Nenhum perfil encontrado</p>
                            <p className="text-xs text-gray-600 mt-2">Adicione sessões TikTok em backend/data/sessions/</p>
                        </StitchCard>
                    )}

                    {/* Add Profile Card */}
                    <div
                        onClick={() => setShowImportModal(true)}
                        className="p-6 rounded-xl bg-white/5 border-2 border-dashed border-white/10 flex flex-col items-center justify-center min-h-[200px] cursor-pointer hover:border-synapse-primary/50 hover:bg-white/10 transition-all group"
                    >
                        <PlusIcon className="w-8 h-8 text-gray-500 group-hover:text-synapse-primary mb-3 transition-colors" />
                        <p className="text-gray-500 group-hover:text-gray-300 transition-colors m-0">Importar Novo Perfil</p>
                    </div>
                </div>

                {/* Import Modal */}
                {
                    showImportModal && (
                        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[100] fade-in p-4">
                            <StitchCard className="w-full max-w-lg bg-[#161b22] border-synapse-border p-6 shadow-2xl relative">
                                <h3 className="text-xl font-bold text-white mb-4">Importar Cookies</h3>

                                <div className="mb-4">
                                    <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">Nome do Perfil</label>
                                    <input
                                        type="text"
                                        value={importLabel}
                                        onChange={(e) => setImportLabel(e.target.value)}
                                        placeholder="Ex: Canal de Cortes"
                                        className="w-full px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all"
                                    />
                                </div>

                                <div className="mb-6">
                                    <label className="block text-xs text-gray-400 mb-2 uppercase font-bold">JSON de Cookies (EditThisCookie)</label>
                                    <textarea
                                        value={importCookies}
                                        onChange={(e) => setImportCookies(e.target.value)}
                                        placeholder='[{"domain": ".tiktok.com", ...}]'
                                        className="w-full h-40 px-4 py-3 rounded-lg bg-black/50 border border-white/10 text-white font-mono text-xs focus:border-synapse-primary focus:ring-1 focus:ring-synapse-primary outline-none transition-all custom-scrollbar resize-none"
                                    />
                                </div>

                                <div className="flex justify-end gap-3">
                                    <NeonButton variant="ghost" onClick={() => setShowImportModal(false)}>
                                        Cancelar
                                    </NeonButton>
                                    <NeonButton onClick={handleImport}>
                                        Importar
                                    </NeonButton>
                                </div>
                            </StitchCard>
                        </div>
                    )
                }
            </main >
        </div >
    );
}
