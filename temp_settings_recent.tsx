"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Cog6ToothIcon,
    KeyIcon,
    ServerIcon,
    LanguageIcon,
    CpuChipIcon,
    CheckCircleIcon,
    ExclamationCircleIcon
} from "@heroicons/react/24/outline";
import { toast } from "sonner";
import axios from "axios";

// --- COMPONENTS ---
const TabButton = ({ active, onClick, icon: Icon, label }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 ${active
                ? "bg-white/10 text-white shadow-[0_0_15px_rgba(255,255,255,0.1)] border border-white/10"
                : "text-zinc-400 hover:text-white hover:bg-white/5"
            }`}
    >
        <Icon className="w-5 h-5" />
        <span className="font-medium text-sm">{label}</span>
    </button>
);

const SettingSection = ({ title, children }) => (
    <div className="bg-[#0c0c0c]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 mb-6">
        <h3 className="text-lg font-semibold text-white/90 mb-4 flex items-center gap-2">
            {title}
        </h3>
        <div className="space-y-4">
            {children}
        </div>
    </div>
);

const InputField = ({ label, value, onChange, type = "text", placeholder = "", mask = false }) => (
    <div className="group">
        <label className="block text-xs font-medium text-zinc-500 mb-1 ml-1 uppercase tracking-wider group-focus-within:text-purple-400 transition-colors">
            {label}
        </label>
        <div className="relative">
            <input
                type={type}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all placeholder:text-zinc-700"
            />
            {mask && value && (
                <div className="absolute right-3 top-3 text-xs text-zinc-500 bg-black/60 px-2 py-0.5 rounded">
                    MASKED
                </div>
            )}
        </div>
    </div>
);

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState("integrations");
    const [loading, setLoading] = useState(true);
    const [settings, setSettings] = useState<any>({});
    const [health, setHealth] = useState<any>(null);

    // Fetch Settings
    useEffect(() => {
        fetchSettings();
        checkHealth();
    }, []);

    const fetchSettings = async () => {
        try {
            const res = await axios.get("http://localhost:8000/api/v1/system/settings");
            setSettings(res.data);
            setLoading(false);
        } catch (e) {
            toast.error("Failed to load settings");
        }
    };

    const checkHealth = async () => {
        try {
            const res = await axios.get("http://localhost:8000/api/v1/system/system/health");
            setHealth(res.data);
        } catch (e) {
            setHealth({ status: "offline" });
        }
    };

    const saveSettings = async () => {
        try {
            // Optimistic Update
            const oldSettings = { ...settings };

            const payload = { settings };
            await axios.post("http://localhost:8000/api/v1/system/settings", payload);

            toast.success("Settings saved successfully");
            fetchSettings(); // Refresh (to get masked keys back if needed)
        } catch (e) {
            toast.error("Failed to save settings");
        }
    };

    // Handlers for nested state updates
    const updateNested = (section: string, key: string, value: any) => {
        setSettings(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [key]: value
            }
        }));
    };

    if (loading) return <div className="p-10 text-center text-zinc-500 animate-pulse">Loading Neuro-config...</div>;

    return (
        <div className="min-h-screen bg-[#050505] text-white p-8 pl-24"> {/* Added pl-24 for sidebar offset if needed */}

            {/* HEADER */}
            <header className="flex items-center justify-between mb-10">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-500">
                        Synapse Config
                    </h1>
                    <p className="text-zinc-500 text-sm mt-1">Global System Preferences & Integrations</p>
                </div>
                <div className="flex items-center gap-4">
                    {health && (
                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${health.status === "online"
                                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                                : "bg-red-500/10 border-red-500/20 text-red-400"
                            } text-xs font-medium`}>
                            <div className={`w-2 h-2 rounded-full ${health.status === "online" ? "bg-emerald-500" : "bg-red-500"} animate-pulse`} />
                            {health.status === "online" ? "SYSTEM ONLINE" : "SYSTEM OFFLINE"}
                        </div>
                    )}
                    <button
                        onClick={saveSettings}
                        className="bg-white text-black px-6 py-2.5 rounded-xl font-bold text-sm hover:scale-105 active:scale-95 transition-all shadow-[0_0_20px_rgba(255,255,255,0.2)]"
                    >
                        Save Changes
                    </button>
                </div>
            </header>

            {/* TABS */}
            <div className="flex gap-2 mb-8 border-b border-white/5 pb-1 overflow-x-auto">
                <TabButton
                    active={activeTab === "integrations"}
                    onClick={() => setActiveTab("integrations")}
                    icon={KeyIcon}
                    label="Integrações & Keys"
                />
                <TabButton
                    active={activeTab === "system"}
                    onClick={() => setActiveTab("system")}
                    icon={CpuChipIcon}
                    label="System Defaults"
                />
                <TabButton
                    active={activeTab === "logs"}
                    onClick={() => setActiveTab("logs")}
                    icon={ServerIcon}
                    label="System Logs"
                />
            </div>

            {/* CONTENT */}
            <AnimatePresence mode="wait">

                {/* --- INTEGRATIONS TAB --- */}
                {activeTab === "integrations" && (
                    <motion.div
                        key="integrations"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-5xl"
                    >
                        <SettingSection title="Artificial Intelligence">
                            <InputField
                                label="OpenAI API Key (GPT-4)"
                                value={settings.integrations?.openai_api_key || ""}
                                onChange={(v) => updateNested("integrations", "openai_api_key", v)}
                                placeholder="sk-..."
                                mask={settings.integrations?.openai_api_key?.includes("...")}
                            />
                            <div className="bg-purple-500/5 border border-purple-500/10 rounded-lg p-3 text-xs text-purple-300 mt-2 flex gap-2">
                                <KeyIcon className="w-4 h-4 flex-shrink-0" />
                                Used for text generation, SEO logic, and complex reasoning.
                            </div>

                            <div className="mt-4">
                                <InputField
                                    label="Groq API Key (Llama 3)"
                                    value={settings.integrations?.groq_api_key || ""}
                                    onChange={(v) => updateNested("integrations", "groq_api_key", v)}
                                    placeholder="gsk_..."
                                    mask={settings.integrations?.groq_api_key?.includes("...")}
                                />
                            </div>
                        </SettingSection>

                        <SettingSection title="TikTok Network">
                            <InputField
                                label="Cookies File Path"
                                value={settings.integrations?.tiktok_cookie_path || ""}
                                onChange={(v) => updateNested("integrations", "tiktok_cookie_path", v)}
                                placeholder="data/cookies.json"
                            />
                            <p className="text-xs text-zinc-500 mt-2">
                                Path relative to project root. Required for authenticated scraping.
                            </p>
                        </SettingSection>
                    </motion.div>
                )}

                {/* --- SYSTEM TAB --- */}
                {activeTab === "system" && (
                    <motion.div
                        key="system"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-5xl"
                    >
                        <SettingSection title="Localization & Defaults">
                            <div className="grid grid-cols-2 gap-4">
                                <InputField
                                    label="System Language"
                                    value={settings.system?.language || "pt-BR"}
                                    onChange={(v) => updateNested("system", "language", v)}
                                />
                                <InputField
                                    label="Timezone"
                                    value={settings.system?.timezone || "America/Sao_Paulo"}
                                    onChange={(v) => updateNested("system", "timezone", v)}
                                />
                            </div>
                        </SettingSection>

                        <SettingSection title="Performance">
                            <InputField
                                label="Max Concurrent Tasks"
                                type="number"
                                value={settings.system?.max_concurrent_tasks || 3}
                                onChange={(v) => updateNested("system", "max_concurrent_tasks", parseInt(v))}
                            />
                            <p className="text-xs text-zinc-500 mt-2">
                                Higher values increase speed but require more RAM/CPU. Recommended: 3.
                            </p>
                        </SettingSection>

                        <SettingSection title="Niche Detection">
                            <div className="flex items-center justify-between bg-black/40 p-3 rounded-xl border border-white/10">
                                <span className="text-sm text-zinc-300">Auto-Detect Niche via AI</span>
                                <input
                                    type="checkbox"
                                    checked={settings.niche?.auto_detect || false}
                                    onChange={(e) => updateNested("niche", "auto_detect", e.target.checked)}
                                    className="w-5 h-5 accent-purple-500 rounded cursor-pointer"
                                />
                            </div>
                            <div className="mt-4">
                                <InputField
                                    label="Default Niche Fallback"
                                    value={settings.niche?.default_niche || "General"}
                                    onChange={(v) => updateNested("niche", "default_niche", v)}
                                />
                            </div>
                        </SettingSection>
                    </motion.div>
                )}

                {/* --- LOGS TAB --- */}
                {activeTab === "logs" && (
                    <motion.div
                        key="logs"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                        className="max-w-6xl"
                    >
                        <div className="bg-[#0c0c0c] border border-white/10 rounded-xl overflow-hidden font-mono text-xs">
                            <div className="bg-white/5 px-4 py-2 border-b border-white/5 flex justify-between items-center">
                                <span className="text-zinc-400">Application Logs (Live Tail) - Placeholder</span>
                                <span className="text-emerald-500">● Live</span>
                            </div>
                            <div className="p-4 h-[500px] overflow-y-auto text-zinc-300 space-y-1">
                                <div className="text-zinc-500">[2023-10-25 10:00:01] SYSTEM: Settings module initialized.</div>
                                <div className="text-zinc-500">[2023-10-25 10:00:02] ORACLE: Connected to Groq API.</div>
                                <div>[2023-10-25 10:05:00] <span className="text-blue-400">INFO</span>: Scheduler checked 0 pending items.</div>
                                {/* Real log streaming would go here via WebSocket */}
                            </div>
                        </div>
                    </motion.div>
                )}

            </AnimatePresence>
        </div>
    );
}
