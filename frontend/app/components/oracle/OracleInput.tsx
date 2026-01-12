import React, { useState, useEffect, useRef } from 'react';
import { NeonButton } from '../NeonButton';
import { motion, AnimatePresence } from 'framer-motion';
import { getSavedProfiles, SavedProfile } from '../../../services/profileService';

interface OracleInputProps {
    onAnalyze: (username: string) => void;
    isLoading: boolean;
}

export const OracleInput: React.FC<OracleInputProps> = ({ onAnalyze, isLoading }) => {
    const [username, setUsername] = useState('');
    const [profiles, setProfiles] = useState<SavedProfile[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Fetch profiles on mount
        getSavedProfiles().then(setProfiles);

        // Click outside listener
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setShowSuggestions(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (username.trim()) {
            onAnalyze(username);
            setShowSuggestions(false);
        }
    };

    const handleSelectProfile = (label: string) => {
        // Extract username from label if it's formatted like "username (metrics)"
        // But usually label depends on filename. Let's assume label IS the username or closest to it.
        // If file is session_@username.json, label might be @username.
        let cleanName = label;
        if (cleanName.startsWith('session_')) cleanName = cleanName.replace('session_', '');
        if (cleanName.endsWith('.json')) cleanName = cleanName.replace('.json', '');

        setUsername(cleanName);
        setShowSuggestions(false);
    };

    // Filter profiles based on input
    const filteredProfiles = profiles.filter(p =>
        p.label.toLowerCase().includes(username.toLowerCase()) ||
        p.filename.toLowerCase().includes(username.toLowerCase())
    );

    return (
        <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={handleSubmit}
            className="flex flex-col items-center gap-4 w-full max-w-2xl mx-auto relative"
        >
            <div className="relative w-full" ref={wrapperRef}>
                <input
                    type="text"
                    value={username}
                    onChange={(e) => {
                        setUsername(e.target.value);
                        setShowSuggestions(true);
                    }}
                    onFocus={() => setShowSuggestions(true)}
                    placeholder="@username ou Selecionar Perfil"
                    className="w-full bg-[#0a0a0f]/80 border border-[#00f3ff]/30 text-[#00f3ff] text-2xl px-6 py-4 rounded-xl focus:outline-none focus:border-[#00f3ff] focus:shadow-[0_0_20px_rgba(0,243,255,0.3)] transition-all placeholder-[#00f3ff]/30 font-mono text-center relative z-20"
                    disabled={isLoading}
                    autoComplete="off"
                />

                {isLoading && (
                    <div className="absolute inset-0 rounded-xl bg-[#00f3ff]/10 animate-pulse pointer-events-none z-10" />
                )}

                {/* Suggestions Dropdown */}
                <AnimatePresence>
                    {showSuggestions && filteredProfiles.length > 0 && !isLoading && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute top-full left-0 right-0 mt-2 bg-[#0f0a15] border border-[#00f3ff]/20 rounded-xl shadow-2xl overflow-hidden z-30 max-h-60 overflow-y-auto custom-scrollbar"
                        >
                            {filteredProfiles.map((profile, idx) => (
                                <div
                                    key={idx}
                                    onClick={() => handleSelectProfile(profile.label || profile.filename)}
                                    className="px-6 py-3 hover:bg-[#00f3ff]/10 cursor-pointer border-b border-white/5 last:border-0 flex items-center justify-between group transition-colors"
                                >
                                    <span className="text-gray-300 font-mono group-hover:text-[#00f3ff] transition-colors truncate">
                                        {profile.label || profile.filename}
                                    </span>
                                    <span className="text-xs text-gray-600 group-hover:text-[#00f3ff]/50 uppercase tracking-widest">
                                        SAVED
                                    </span>
                                </div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <NeonButton
                onClick={() => { }}
                disabled={isLoading}
                variant="primary"
                className="px-12 py-3 text-lg"
            >
                {isLoading ? 'ANALISANDO...' : 'INICIAR SCAN'}
            </NeonButton>

            {/* Quick Profile Select Grid */}
            {profiles.length > 0 && !isLoading && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="w-full mt-8"
                >
                    <h3 className="text-gray-500 text-xs uppercase tracking-widest mb-4 text-center">Perfis Identificados</h3>
                    <div className="flex flex-wrap justify-center gap-4">
                        {profiles.map((profile, idx) => (
                            <div
                                key={idx}
                                onClick={() => handleSelectProfile(profile.label || profile.filename)}
                                className="group cursor-pointer flex flex-col items-center gap-2 p-4 rounded-xl bg-white/5 border border-white/5 hover:bg-[#00f3ff]/10 hover:border-[#00f3ff]/30 transition-all w-32"
                            >
                                <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-transparent group-hover:border-[#00f3ff] transition-colors bg-gray-800 flex items-center justify-center">
                                    {profile.avatar_url ? (
                                        /* eslint-disable-next-line @next/next/no-img-element */
                                        <img src={profile.avatar_url} alt={profile.label} className="w-full h-full object-cover" />
                                    ) : (
                                        <span className="text-xl text-gray-500 group-hover:text-[#00f3ff]">👤</span>
                                    )}
                                </div>
                                <div className="text-center">
                                    <div className="text-xs font-bold text-gray-300 group-hover:text-white truncate max-w-[100px]">{profile.label}</div>
                                    <div className="text-[10px] text-gray-500 group-hover:text-[#00f3ff] truncate max-w-[100px]">@{profile.username || 'unknown'}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>
            )}
        </motion.form>
    );
};
