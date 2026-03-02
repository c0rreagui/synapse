'use client';

import React, { useState, useEffect } from 'react';

interface Target {
    id: number;
    channel_url: string;
    channel_name: string;
    broadcaster_id?: string;
    active: boolean;
    status?: string;
}

export default function ClipperPage() {
    const [targets, setTargets] = useState<Target[]>([]);
    const [urlInput, setUrlInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const fetchTargets = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/clipper/targets');
            if (res.ok) {
                const data = await res.json();
                setTargets(data);
            }
        } catch (error) {
            console.error("Failed to fetch targets:", error);
        }
    };

    useEffect(() => {
        fetchTargets();
        const interval = setInterval(fetchTargets, 10000);
        return () => clearInterval(interval);
    }, []);

    const handleAddTarget = async () => {
        if (!urlInput.trim()) return;
        setIsLoading(true);
        try {
            const res = await fetch('http://localhost:8000/api/clipper/targets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel_url: urlInput.trim() })
            });
            if (res.ok) {
                setUrlInput("");
                await fetchTargets();
            } else {
                const errorData = await res.json();
                alert(`Erro: ${errorData.detail}`);
            }
        } catch (error) {
            console.error("Failed to add target:", error);
            alert("Erro de conexão com o painel orbital.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteTarget = async (id: number) => {
        if (!confirm("Tem certeza que deseja remover este alvo da órbita?")) return;
        try {
            const res = await fetch(`http://localhost:8000/api/clipper/targets/${id}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                await fetchTargets();
            }
        } catch (error) {
            console.error("Failed to delete target:", error);
        }
    };

    return (
        <div className="flex-1 flex flex-col max-w-[1600px] w-full mx-auto gap-10 relative z-10 h-full">

            {/* Header Area */}
            <div className="flex flex-col md:flex-row justify-between items-end gap-6 pb-2 border-b border-white/5 relative mt-6">
                <div className="absolute bottom-0 right-0 w-1/3 h-px bg-gradient-to-l from-cyan-400/50 to-transparent"></div>
                <div className="relative">
                    <h1 className="text-5xl lg:text-6xl font-bold tracking-tighter text-white uppercase drop-shadow-[0_0_25px_rgba(0,240,255,0.2)] font-display">
                        Vigilância do <span className="text-cyan-400 block text-3xl lg:text-4xl tracking-[0.2em] font-mono mt-2 font-normal drop-shadow-[0_0_10px_rgba(0,240,255,0.8)]">Espaço Profundo</span>
                    </h1>
                    <div className="absolute -right-24 top-0 w-20 h-20 border-r border-t border-cyan-400/50 rounded-tr-3xl hidden lg:block shadow-[2px_-2px_10px_rgba(0,240,255,0.2)]"></div>
                    <div className="absolute -right-20 top-4 text-[10px] font-mono text-cyan-400/50 rotate-90 hidden lg:block animate-pulse">SETOR_SEG_07 // AO VIVO</div>
                </div>

                <div className="flex flex-col items-end gap-1">
                    <div className="flex items-center gap-4 text-xs font-mono text-cyan-400/70">
                        <span className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm animate-spin-slow">memory</span>
                            CARGA_CPU: 12%
                        </span>
                        <span className="w-px h-3 bg-white/20"></span>
                        <span className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-sm animate-pulse">wifi_tethering</span>
                            FLUXO_REDE: 450Mbps
                        </span>
                    </div>
                    <div className="w-full h-1 bg-surface-border mt-1 relative overflow-hidden rounded-full">
                        <div className="absolute inset-0 bg-cyan-400/80 w-1/3 animate-scan-laser" style={{ animationDuration: '3s' }}></div>
                    </div>
                </div>
            </div>

            {/* Input Target Section */}
            <section className="flex justify-center py-12 relative shrink-0">
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-[600px] h-[600px] border border-white/5 rounded-full absolute animate-spin-slow opacity-50" style={{ animationDuration: '60s' }}></div>
                    <div className="w-[400px] h-[400px] border border-dashed border-cyan-400/30 rounded-full absolute animate-spin-slow" style={{ animationDirection: 'reverse', animationDuration: '40s' }}></div>
                </div>

                <div className="relative w-full max-w-2xl group">
                    <div className="absolute -inset-4 border border-cyan-400/40 rounded-full border-t-transparent border-l-transparent animate-spin-slow shadow-[0_0_30px_rgba(0,240,255,0.1)]"></div>
                    <div className="bg-black/80 backdrop-blur-xl border border-cyan-400/60 rounded-full p-2 relative shadow-[0_0_50px_-10px_rgba(0,240,255,0.25)] aperture-ring transition-all duration-500 flex items-center overflow-hidden">
                        <div className="laser-sweep animate-scan-laser"></div>
                        <div className="pl-6 pr-4 text-cyan-400 animate-pulse z-10">
                            <span className="material-symbols-outlined text-3xl drop-shadow-[0_0_8px_rgba(0,240,255,0.8)]">filter_center_focus</span>
                        </div>
                        <div className="flex-1 aperture-input relative z-10">
                            <input
                                type="text"
                                value={urlInput}
                                onChange={(e) => setUrlInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleAddTarget()}
                                placeholder="INSERIR_COORDENADAS_ALVO [URL da Twitch]..."
                                className="w-full bg-transparent border-none text-white text-lg font-mono placeholder:text-cyan-400/40 focus:ring-0 py-4 tracking-wider uppercase focus:outline-none"
                                disabled={isLoading}
                            />
                        </div>
                        <button
                            onClick={handleAddTarget}
                            disabled={isLoading}
                            className="z-10 bg-cyan-400/10 hover:bg-cyan-400 hover:text-black text-cyan-400 border border-cyan-400/50 rounded-full px-8 py-3 mr-1 transition-all duration-300 flex items-center gap-2 group/btn shadow-[0_0_15px_rgba(0,240,255,0.1)] hover:shadow-[0_0_25px_rgba(0,240,255,0.6)] disabled:opacity-50 disabled:cursor-not-allowed">
                            {isLoading ? (
                                <span className="material-symbols-outlined animate-spin text-sm">autorenew</span>
                            ) : (
                                <>
                                    <span className="font-mono font-bold tracking-widest text-sm">INICIAR</span>
                                    <span className="material-symbols-outlined group-hover/btn:translate-x-1 transition-transform text-sm">sensors</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </section>

            {/* Targets Section */}
            <section className="flex-1 overflow-y-auto custom-scrollbar pb-10">
                <div className="flex items-center justify-between mb-6 border-b border-cyan-400/20 pb-2">
                    <h3 className="text-xl font-bold text-white flex items-center gap-3 font-mono">
                        <span className="material-symbols-outlined text-cyan-400 animate-pulse">grid_view</span>
                        ALVOS_DE_RECONHECIMENTO_ORBITAL
                    </h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {targets.length === 0 && (
                        <div className="col-span-full py-20 text-center text-cyan-400/50 font-mono flex flex-col items-center gap-4">
                            <span className="material-symbols-outlined text-5xl">satellite_alt</span>
                            NENHUM_ALVO_DETECTADO_NO_RADAR
                        </div>
                    )}

                    {targets.map(target => (
                        <div key={target.id} className={`group relative bg-[#050a0f] border border-[#122026] hover:border-cyan-400/60 transition-all duration-300 overflow-hidden rounded-lg shadow-[0_0_0_1px_rgba(0,0,0,0)] hover:shadow-[0_0_20px_rgba(0,240,255,0.15)] ${!target.active ? 'opacity-60 hover:opacity-100 grayscale contrast-125' : ''}`}>
                            <div className="absolute inset-0 bg-[linear-gradient(transparent_0%,rgba(0,240,255,0.08)_50%,transparent_100%)] h-[200%] w-full -translate-y-1/2 group-hover:translate-y-0 transition-transform duration-1000 ease-in-out pointer-events-none z-20 opacity-0 group-hover:opacity-100"></div>

                            <div className="absolute top-0 left-0 w-full z-10 flex justify-between items-start p-4">
                                {target.active ? (
                                    <div className="bg-black/70 backdrop-blur border border-red-500/50 text-red-500 px-3 py-1 text-[10px] font-bold font-mono uppercase tracking-widest flex items-center gap-2 shadow-[0_0_15px_rgba(255,42,42,0.3)]">
                                        <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-ping"></span>
                                        SINAL_AO_VIVO
                                    </div>
                                ) : (
                                    <div className="bg-black/60 backdrop-blur border border-slate-600/50 text-slate-400 px-3 py-1 text-[10px] font-bold font-mono uppercase tracking-widest flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 bg-slate-500 rounded-full"></span>
                                        SINAL_INATIVO
                                    </div>
                                )}
                            </div>

                            <div className={`h-48 bg-[#0a0a0a] relative ${target.active ? 'group-hover:scale-105 transition-transform duration-700' : ''}`}>
                                <div className="absolute inset-0 bg-gradient-to-t from-[#050a0f] via-[#050a0f]/30 to-transparent z-10"></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <span className="material-symbols-outlined text-white/10 text-6xl">videocam</span>
                                </div>
                                {target.active && (
                                    <div className="absolute bottom-4 left-4 right-4 h-12 flex items-end gap-1 justify-center opacity-90 pb-2 border-b border-cyan-400/20 z-20">
                                        <div className="waveform-bar h-full" style={{ animationDuration: '0.6s' }}></div>
                                        <div className="waveform-bar h-full" style={{ animationDuration: '0.8s', animationDelay: '0.1s' }}></div>
                                        <div className="waveform-bar h-full" style={{ animationDuration: '1.1s', animationDelay: '0.2s' }}></div>
                                        <div className="waveform-bar h-full" style={{ animationDuration: '0.7s', animationDelay: '0.05s' }}></div>
                                    </div>
                                )}
                            </div>

                            <div className="p-5 relative z-10 -mt-10">
                                <div className="flex items-end gap-4 mb-4">
                                    <div className={`size-12 rounded border ${target.active ? 'border-cyan-400/50 shadow-[0_0_15px_rgba(0,240,255,0.3)]' : 'border-slate-700'} bg-[#111] flex items-center justify-center overflow-hidden`}>
                                        <span className={`${target.active ? 'text-cyan-400' : 'text-slate-500'} text-xs font-bold font-mono`}>
                                            {target.channel_name ? target.channel_name.substring(0, 4).toUpperCase() : '---'}
                                        </span>
                                    </div>
                                    <div>
                                        <h4 className={`font-bold text-lg font-mono ${target.active ? 'text-white group-hover:text-cyan-400' : 'text-slate-400'} transition-colors truncate max-w-[150px]`}>
                                            {target.channel_name || 'Desconhecido'}
                                        </h4>
                                        <p className={`${target.active ? 'text-cyan-400/60' : 'text-slate-600'} text-xs font-mono uppercase tracking-wider flex items-center gap-1`}>
                                            {target.active && <span className="size-1 bg-cyan-400 rounded-full"></span>}
                                            {target.active ? 'Modo de Transmissão: Ativo' : 'Offline'}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => handleDeleteTarget(target.id)} className="flex-1 bg-white/5 hover:bg-red-500/20 hover:text-red-500 hover:border-red-500/50 text-white text-xs font-mono uppercase tracking-wider py-2 border border-white/10 transition-all duration-300">
                                        Pausar / Deletar
                                    </button>
                                    <button className={`flex-1 ${target.active ? 'bg-cyan-400/10 hover:bg-cyan-400/30 text-cyan-400 border-cyan-400/30 hover:shadow-[0_0_10px_rgba(0,240,255,0.1)]' : 'bg-white/5 hover:bg-white/10 text-white border-white/10'} text-xs font-mono uppercase tracking-wider py-2 border transition-all duration-300`}>
                                        <a href={target.channel_url} target="_blank" rel="noreferrer">
                                            Abrir Radar
                                        </a>
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}

