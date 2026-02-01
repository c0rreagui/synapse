import React from 'react';
import { useBatch } from './BatchContext';
import clsx from 'clsx';

export function BatchSidebar() {
    const { profiles, selectedProfiles, setSelectedProfiles } = useBatch();

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
            setSelectedProfiles(profiles.map(p => p.id));
        }
    };

    return (
        <div className="w-64 h-full border-r border-white/5 bg-black/20 flex flex-col">
            {/* Header */}
            <div className="p-5 border-b border-white/5">
                <h3 className="text-sm font-bold text-white flex items-center justify-between">
                    Publicar em
                    {profiles.length > 0 && (
                        <button
                            onClick={toggleAll}
                            className="text-[10px] text-gray-500 hover:text-white transition-colors"
                        >
                            {selectedProfiles.length === profiles.length ? 'Nenhum' : 'Todos'}
                        </button>
                    )}
                </h3>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
                {profiles.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 text-center p-4">
                        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center mb-3">
                            <span className="text-xl">👻</span>
                        </div>
                        <p className="text-xs text-gray-400 font-medium mb-1">Nenhuma conta</p>
                        <p className="text-[10px] text-gray-600">Conecte um perfil TikTok para começar.</p>
                    </div>
                ) : (
                    profiles.map(profile => {
                        const isSelected = selectedProfiles.includes(profile.id);
                        return (
                            <div
                                key={profile.id}
                                onClick={() => toggleProfile(profile.id)}
                                className={clsx(
                                    "flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200 group",
                                    isSelected
                                        ? "bg-synapse-purple/10 border border-synapse-purple/30"
                                        : "hover:bg-white/5 border border-transparent"
                                )}
                            >
                                {/* Checkbox Visual */}
                                <div className={clsx(
                                    "w-4 h-4 rounded-md border flex items-center justify-center transition-all",
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
                                <div className="flex items-center gap-2 overflow-hidden">
                                    <div className="w-6 h-6 rounded-full bg-gray-800 flex items-center justify-center text-xs overflow-hidden border border-white/10">
                                        {profile.avatar_url ? (
                                            <img src={profile.avatar_url} alt={profile.label} className="w-full h-full object-cover" />
                                        ) : (
                                            <span className="text-gray-400 font-bold">{profile.label?.charAt(0).toUpperCase() || '?'}</span>
                                        )}
                                    </div>
                                    <span className={clsx(
                                        "text-xs font-medium truncate",
                                        isSelected ? "text-white" : "text-gray-400 group-hover:text-gray-300"
                                    )}>
                                        {profile.label || profile.username}
                                    </span>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Footer / Add New */}
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
