'use client';

import { useState, useEffect, useCallback } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { toast } from 'sonner';
import { NeonButton } from './NeonButton';
import { TikTokProfile } from '../types';
import { getApiUrl } from '../utils/apiClient';

interface ProfileRepairModalProps {
    isOpen: boolean;
    onClose: () => void;
    profile: TikTokProfile | null;
    onSuccess?: () => void;
}

export default function ProfileRepairModal({ isOpen, onClose, profile, onSuccess }: ProfileRepairModalProps) {
    const API_BASE = `${getApiUrl()}/api/v1`;

    // TAB STATE
    const [activeTab, setActiveTab] = useState<'auto' | 'manual'>('auto');

    // AUTO REPAIR STATE
    const [repairing, setRepairing] = useState(false);

    // MANUAL COOKIES STATE
    const [cookiesStr, setCookiesStr] = useState('');
    const [updatingCookies, setUpdatingCookies] = useState(false);

    // Reset state on open
    useEffect(() => {
        if (isOpen) {
            setCookiesStr('');
            setActiveTab('auto');
            setRepairing(false);
            setUpdatingCookies(false);
        }
    }, [isOpen, profile]);

    // POLL LOGIC
    const pollRepairStatus = useCallback(async (profileId: string, maxAttempts = 30) => {
        for (let i = 0; i < maxAttempts; i++) {
            await new Promise(resolve => setTimeout(resolve, 5000)); // 5s interval

            try {
                const res = await fetch(`${API_BASE}/profiles`);
                const data = await res.json();
                const p = data.find((prof: TikTokProfile) => prof.id === profileId);

                if (p && p.session_valid) {
                    toast.success('Sessão recuperada com sucesso!', {
                        description: `${p.label} está ativo novamente.`
                    });
                    setRepairing(false);
                    if (onSuccess) onSuccess();
                    onClose();
                    return true;
                }
            } catch (e) {
                // Continue polling
            }
        }
        setRepairing(false);
        return false;
    }, [API_BASE, onSuccess, onClose]);

    const handleAutoRepair = async () => {
        if (!profile) return;
        setRepairing(true);

        const toastId = toast.loading('Abrindo navegador no servidor...', {
            description: 'Faça login manualmente na janela que abrirá.'
        });

        try {
            const res = await fetch(`${API_BASE}/profiles/repair/${profile.id}`, { method: 'POST' });
            if (res.ok) {
                toast.success('Navegador aberto!', {
                    id: toastId,
                    description: 'Realize o login e feche o navegador. O sistema detectará automaticamente.',
                    duration: 10000
                });
                pollRepairStatus(profile.id);
            } else {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                toast.error('Erro ao abrir navegador', {
                    id: toastId,
                    description: err.detail
                });
                setRepairing(false);
            }
        } catch (e) {
            toast.error('Erro de conexão', { id: toastId });
            setRepairing(false);
        }
    };

    const handleManualUpdate = async () => {
        if (!profile || !cookiesStr) return;
        setUpdatingCookies(true);

        try {
            JSON.parse(cookiesStr); // Validate JSON

            const res = await fetch(`${API_BASE}/profiles/${profile.id}/cookies`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookies: cookiesStr })
            });

            if (res.ok) {
                toast.success('Cookies atualizados!', {
                    description: 'Validando sessão...'
                });
                // Trigger a refresh verification
                await fetch(`${API_BASE}/profiles/refresh-avatar/${profile.id}`, { method: 'POST' });

                if (onSuccess) onSuccess();
                onClose();
            } else {
                const err = await res.json();
                toast.error('Erro ao atualizar', { description: err.detail });
            }
        } catch (e) {
            toast.error('JSON Inválido', { description: 'Verifique o formato dos cookies.' });
        }
        setUpdatingCookies(false);
    };

    if (!profile) return null;

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-[9999]" onClose={() => { if (!repairing) onClose(); }}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-[#0f0a15] border border-synapse-purple/30 p-0 shadow-2xl transition-all">
                                {/* Header */}
                                <div className="p-6 border-b border-white/5 bg-gradient-to-r from-synapse-purple/10 to-transparent">
                                    <Dialog.Title as="h3" className="text-xl font-bold text-white flex items-center gap-3">
                                        <ExclamationTriangleIcon className="w-6 h-6 text-amber-500" />
                                        Recuperar Sessão
                                    </Dialog.Title>
                                    <div className="flex items-center gap-2 mt-2">
                                        <div className="w-6 h-6 rounded-full bg-gray-700 overflow-hidden ring-1 ring-white/20">
                                            {profile.avatar_url ? (
                                                <img src={profile.avatar_url} className="w-full h-full object-cover" />
                                            ) : (
                                                <span className="flex items-center justify-center h-full text-xs">👤</span>
                                            )}
                                        </div>
                                        <span className="text-gray-400 text-sm font-mono">@{profile.username || profile.label}</span>
                                    </div>
                                    <button onClick={onClose} className="absolute top-4 right-4 p-2 text-gray-500 hover:text-white transition-colors">
                                        <XMarkIcon className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Tabs */}
                                <div className="flex border-b border-white/5 bg-black/20">
                                    <button
                                        onClick={() => setActiveTab('auto')}
                                        className={`flex-1 py-3 text-sm font-bold transition-colors ${activeTab === 'auto' ? 'text-synapse-purple border-b-2 border-synapse-purple' : 'text-gray-500 hover:text-gray-300'}`}
                                    >
                                        Navegador Automático
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('manual')}
                                        className={`flex-1 py-3 text-sm font-bold transition-colors ${activeTab === 'manual' ? 'text-synapse-purple border-b-2 border-synapse-purple' : 'text-gray-500 hover:text-gray-300'}`}
                                    >
                                        Cookies Manuais
                                    </button>
                                </div>

                                {/* Content */}
                                <div className="p-6">
                                    {activeTab === 'auto' ? (
                                        <div className="flex flex-col gap-4 text-center py-4">
                                            <p className="text-sm text-gray-400">
                                                O sistema abrirá uma janela do navegador no servidor.<br />
                                                Faça login no TikTok manualmente e feche a janela.
                                            </p>

                                            <NeonButton
                                                variant="primary"
                                                onClick={handleAutoRepair}
                                                disabled={repairing}
                                                className="w-full py-4 flex items-center justify-center gap-2"
                                            >
                                                {repairing ? (
                                                    <>
                                                        <ArrowPathIcon className="w-5 h-5 animate-spin" />
                                                        Aguardando Login...
                                                    </>
                                                ) : (
                                                    <>
                                                        🚀 Abrir Navegador
                                                    </>
                                                )}
                                            </NeonButton>

                                            {repairing && (
                                                <div className="text-xs text-amber-500 animate-pulse font-mono mt-2">
                                                    Não feche este modal até concluir o login.
                                                </div>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="space-y-4">
                                            <p className="text-xs text-gray-400">
                                                Cole o JSON de cookies exportado da extensão <b>EditThisCookie</b>.
                                            </p>
                                            <textarea
                                                value={cookiesStr}
                                                onChange={(e) => setCookiesStr(e.target.value)}
                                                placeholder='[{"domain": ".tiktok.com", ...}]'
                                                className="w-full h-40 bg-black/50 border border-white/10 rounded-lg p-3 text-xs font-mono text-white focus:border-synapse-purple outline-none resize-none"
                                            />
                                            <NeonButton
                                                onClick={handleManualUpdate}
                                                disabled={!cookiesStr || updatingCookies}
                                                className="w-full"
                                            >
                                                {updatingCookies ? "Validando..." : "Salvar Cookies"}
                                            </NeonButton>
                                        </div>
                                    )}
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
