'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { GlassPanel } from '@/components/design-system/GlassPanel';
import { Link as LinkIcon, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface TwitchTarget {
    id: number;
    channel_url: string;
    channel_name: string;
    broadcaster_id: string | null;
    active: boolean;
    status?: string;
}

export function TargetManager() {
    const [url, setUrl] = useState('');
    const queryClient = useQueryClient();

    // GET Targets
    const { data: targets, isLoading, error } = useQuery<TwitchTarget[]>({
        queryKey: ['clipper-targets'],
        queryFn: async () => {
            const res = await fetch('http://localhost:8000/api/clipper/targets');
            if (!res.ok) throw new Error('Falha ao carregar targets');
            return res.json();
        },
        refetchInterval: 15000 // Poll slightly just in case
    });

    // POST Target
    const createTarget = useMutation({
        mutationFn: async (channel_url: string) => {
            const res = await fetch('http://localhost:8000/api/clipper/targets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel_url })
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Erro ao criar target');
            }
            return res.json();
        },
        onSuccess: () => {
            toast.success('Canal adicionado ao monitoramento!');
            setUrl('');
            queryClient.invalidateQueries({ queryKey: ['clipper-targets'] });
        },
        onError: (err: any) => {
            toast.error(err.message);
        }
    });

    // DELETE Target
    const deleteTarget = useMutation({
        mutationFn: async (id: number) => {
            const res = await fetch(`http://localhost:8000/api/clipper/targets/${id}`, {
                method: 'DELETE'
            });
            if (!res.ok) throw new Error('Erro ao deletar target');
            return res.json();
        },
        onSuccess: () => {
            toast.success('Canal removido!');
            queryClient.invalidateQueries({ queryKey: ['clipper-targets'] });
        },
        onError: (err: any) => {
            toast.error(err.message);
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!url || !url.includes('twitch.tv')) {
            toast.error('Insira uma URL válida da Twitch');
            return;
        }
        createTarget.mutate(url);
    };

    return (
        <div className="w-full xl:w-[400px] flex flex-col gap-6 shrink-0 h-full">
            {/* Add URL Form Area */}
            <GlassPanel intensity="medium" className="p-6 flex flex-col gap-4">
                <div className="flex items-center gap-2 mb-2">
                    <LinkIcon className="text-neo-primary w-5 h-5" />
                    <h3 className="font-bold text-lg text-white tracking-wide">Monitorar Canal</h3>
                </div>
                <p className="text-sm text-gray-400 mb-2 font-light">
                    Insira a URL de um streamer da Twitch para extrair cortes automáticos diariamente.
                </p>

                <form onSubmit={handleSubmit} className="flex gap-2">
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://twitch.tv/loud_coringa"
                        className="flex-1 bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-neo-primary/50 transition-colors"
                        disabled={createTarget.isPending}
                    />
                    <button
                        type="submit"
                        disabled={createTarget.isPending}
                        className="px-4 py-2 bg-neo-primary hover:bg-neo-primary/80 text-white rounded-lg font-bold text-sm transition-all shadow-[0_0_15px_rgba(139,92,246,0.5)] disabled:opacity-50"
                    >
                        {createTarget.isPending ? 'Criando...' : 'Iniciar'}
                    </button>
                </form>
            </GlassPanel>

            {/* Active Targets List */}
            <GlassPanel intensity="low" className="p-6 flex-1 min-h-0 flex flex-col">
                <h3 className="font-bold text-lg text-white tracking-wide mb-4">Canais Monitorados</h3>

                <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                    {isLoading && <div className="text-sm text-gray-400">Carregando...</div>}
                    {error && <div className="text-sm text-red-400 flex items-center gap-2"><AlertCircle className="w-4 h-4" /> Erro ao carregar</div>}

                    {!isLoading && targets?.length === 0 && (
                        <div className="text-sm text-gray-500 italic">Nenhum canal monitorado no momento.</div>
                    )}

                    {targets?.map((target) => (
                        <div key={target.id} className="bg-black/40 border border-white/10 rounded-xl p-4 flex items-center justify-between group hover:border-neo-primary/30 transition-all">
                            <div className="min-w-0 pr-4">
                                <div className="font-bold text-white text-sm truncate" title={target.channel_name}>
                                    {target.channel_name}
                                </div>
                                <div className="text-xs text-emerald-400 font-mono flex items-center gap-1 mt-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                    Ativo
                                </div>
                            </div>
                            <button
                                onClick={() => {
                                    if (confirm(`Tem certeza que deseja remover e parar de monitorar ${target.channel_name}?`)) {
                                        deleteTarget.mutate(target.id);
                                    }
                                }}
                                disabled={deleteTarget.isPending}
                                className="shrink-0 text-xs text-red-500 hover:text-red-400 font-bold px-3 py-1.5 rounded bg-red-500/10 hover:bg-red-500/20 transition-colors disabled:opacity-50"
                            >
                                Remover
                            </button>
                        </div>
                    ))}
                </div>
            </GlassPanel>
        </div>
    );
}
