import React from 'react';
import { useBatch } from './BatchContext';
import clsx from 'clsx';

export function BatchSidebar() {
    const { profiles, selectedProfiles, setSelectedProfiles } = useBatch();
    const [searchTerm, setSearchTerm] = React.useState(''); // [SYN-UX] Search for High Volume







    const toggleProfile = (id: string) => {
        if (selectedProfiles.includes(id)) {
            setSelectedProfiles(prev => prev.filter(p => p !== id));
        } else {
            setSelectedProfiles(prev => [...prev, id]);
        }
    };

    const toggleAll = () => {
        if (selectedProfiles.length === profiles.length) {
            setSelectedProfiles([]);
        } else {
            // Select all currently visible (filtered) or all? 
            // Standard UX: Select All usually means *All*, but filtered select is also common.
            // Let's select ALL for now as distinct from "Select Visible".
            setSelectedProfiles(profiles.map(p => p.id));
        }
    };

    const filteredProfiles = profiles.filter(p =>
        (p.label || p.username || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="w-64 h-full border-r border-white/5 bg-black/20 flex flex-col">
            {/* Header */}
            <div className="p-5 border-b border-white/5 space-y-3">
                <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white">Publicar em</h3>
                    {profiles.length > 0 && (
                        <button
                            onClick={toggleAll}
                            className="text-[10px] text-gray-500 hover:text-white transition-colors"
                        >
                            {selectedProfiles.length === profiles.length ? 'Nenhum' : 'Todos'}
                        </button>
                    )}
                </div>

                {/* [SYN-UX] Search Bar for High Volume */}
                <div className="relative group">
                    <input
                        type="text"
                        placeholder="Buscar perfil..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-[#0c0c0e] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-gray-600 focus:border-synapse-purple/50 outline-none transition-all"
                    />
                    <div className="absolute right-2 top-1.5 opacity-30 pointer-events-none">
                        <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">
                {filteredProfiles.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 text-center p-4">
                        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-3">
                            <span className="text-xl">👻</span>
                        </div>
                        <p className="text-xs text-gray-400 font-medium mb-1">
                            {profiles.length === 0 ? "Nenhuma conta" : "Sem resultados"}
                        </p>
                        <p className="text-[10px] text-gray-600">
                            {profiles.length === 0 ? "Conecte um perfil TikTok para começar." : "Tente outro termo de busca."}
                        </p>
                    </div>
                ) : (
                    filteredProfiles.map(profile => {
                        const isSelected = selectedProfiles.includes(profile.id);

                        // [SYN-UX] Status Logic
                        const isHealthy = profile.status === 'active' && profile.session_valid;
                        const hasError = !!profile.last_error_screenshot;
                        const isExpired = !profile.session_valid;

                        let statusColor = "bg-gray-500";
                        if (isHealthy) statusColor = "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]";
                        else if (hasError || isExpired) statusColor = "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]";

                        return (
                            <div
                                key={profile.id}
                                onClick={() => toggleProfile(profile.id)}
                                className={clsx(
                                    "flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200 group relative",
                                    isSelected
                                        ? "bg-synapse-purple/10 border border-synapse-purple/30"
                                        : "hover:bg-white/5 border border-transparent"
                                )}
                            >
                                {/* Checkbox Visual */}
                                <div className={clsx(
                                    "w-4 h-4 rounded-md border flex items-center justify-center transition-all shrink-0",
                                    isSelected
                                        ? "bg-synapse-purple border-synapse-purple text-white"
                                        : "border-white/20 group-hover:border-white/40 bg-transparent"
                                )}>
                                    {isSelected && (
                                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                        </svg>
                                    )}
                                </div>

                                {/* Info */}
                                <div className="flex items-center gap-2 overflow-hidden flex-1">
                                    <div className="relative shrink-0">
                                        <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-xs overflow-hidden border border-white/10">
                                            {profile.avatar_url ? (
                                                <img src={profile.avatar_url} alt={profile.label} className="w-full h-full object-cover" />
                                            ) : (
                                                <span className="text-gray-400 font-bold">{profile.label?.charAt(0).toUpperCase() || '?'}</span>
                                            )}
                                        </div>
                                        {/* Status Dot */}
                                        <div className={clsx(
                                            "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-[#161b22]",
                                            statusColor
                                        )} />
                                    </div>

                                    <div className="flex flex-col overflow-hidden">
                                        <span className={clsx(
                                            "text-xs font-medium truncate",
                                            isSelected ? "text-white" : "text-gray-400 group-hover:text-gray-300"
                                        )}>
                                            {profile.label || profile.username}
                                        </span>
                                        {!isHealthy && (
                                            <span className="text-[10px] text-red-400 truncate">
                                                {hasError ? "Erro" : isExpired ? "Expirado" : "Inativo"}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            <div className="p-4 border-t border-white/5">
                <button
                    onClick={() => {
                        // Redirect to integrations
                        window.location.href = '/integrations';
                    }}
                    className="w-full py-2 flex items-center justify-center gap-2 rounded-lg border border-dashed border-white/10 text-xs text-gray-500 hover:text-white hover:border-white/20 transition-all"
                >
                    <span>+</span> Conectar Conta
                </button>
            </div>
        </div>
    );
}
