import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { getApiUrl } from '../utils/apiClient';

interface Proxy {
    id: number;
    name: string;
    nickname?: string;
    server: string;
    username?: string;
    password?: string;
    active: boolean;
    fingerprint_ua?: string;
    fingerprint_locale?: string;
    fingerprint_timezone?: string;
}

export default function ProxySettings() {
    const [proxies, setProxies] = useState<Proxy[]>([]);
    const [loading, setLoading] = useState(true);

    const [isEditing, setIsEditing] = useState(false);
    const [currentProxy, setCurrentProxy] = useState<Partial<Proxy>>({});

    // Testing state
    const [testingId, setTestingId] = useState<number | null>(null);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    const loadProxies = async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${getApiUrl()}/api/v1/proxies`);
            setProxies(res.data);
        } catch (e) {
            toast.error("Failed to load proxies.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadProxies();
    }, []);

    const saveProxy = async () => {
        if (!currentProxy.server) {
            toast.error("Proxy server is required.");
            return;
        }

        try {
            if (currentProxy.id) {
                await axios.put(`${getApiUrl()}/api/v1/proxies/${currentProxy.id}`, currentProxy);
                toast.success("Proxy updated.");
            } else {
                await axios.post(`${getApiUrl()}/api/v1/proxies`, currentProxy);
                toast.success("Proxy created.");
            }
            setIsEditing(false);
            setCurrentProxy({});
            loadProxies();
        } catch (e) {
            toast.error("Error saving proxy.");
        }
    };

    const deleteProxy = async (id: number) => {
        if (deletingId === id) {
            try {
                await axios.delete(`${getApiUrl()}/api/v1/proxies/${id}`);
                toast.success("Proxy node severed.");
                setDeletingId(null);
                loadProxies();
            } catch (e: any) {
                const msg = e?.response?.data?.detail || e.message;
                toast.error(`Error severing proxy node: ${msg}`);
                setDeletingId(null);
            }
        } else {
            setDeletingId(id);
            setTimeout(() => setDeletingId(curr => curr === id ? null : curr), 3000);
        }
    };

    const testProxy = async (id: number) => {
        setTestingId(id);
        toast.info("Testing connection...", { id: `test-${id}` });
        try {
            const res = await axios.post(`${getApiUrl()}/api/v1/proxies/${id}/test`);
            if (res.data.status === 'success') {
                toast.success(
                    <div className="flex flex-col gap-1 font-mono text-xs">
                        <span className="font-bold text-emerald-400">Connection Optimal</span>
                        <span><b>IP:</b> {res.data.proxy_ip}</span>
                        <span><b>Loc:</b> {res.data.location}</span>
                        {res.data.isp && <span><b>ISP:</b> {res.data.isp}</span>}
                    </div>,
                    { id: `test-${id}`, duration: 6000 }
                );
            } else {
                toast.error(`Connection Failed: ${res.data.message}`, { id: `test-${id}`, duration: 5000 });
            }
        } catch (e: any) {
            toast.error(`Connection Failed: ${e?.response?.data?.detail || e.message}`, { id: `test-${id}` });
        } finally {
            setTestingId(null);
        }
    };

    return (
        <section className="bg-[#0b101b]/60 border border-slate-800 p-1 relative overflow-hidden group hover:shadow-[0_0_40px_-10px_rgba(16,185,129,0.15)] transition-all duration-500 mt-8">
            <div className="absolute inset-0 bg-grid-pattern blueprint-grid opacity-10 pointer-events-none"></div>
            <div className="border border-slate-700 p-8 relative z-10 backdrop-blur-sm">
                <div className="flex items-center justify-between mb-8 border-b border-emerald-500/20 pb-4">
                    <div className="flex items-center gap-4">
                        <div className="p-2 border border-emerald-500/30 text-emerald-500 bg-emerald-500/5 shadow-[0_0_15px_-5px_rgba(16,185,129,0.5)]">
                            <span className="material-symbols-outlined">router</span>
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-white font-mono uppercase tracking-[0.2em]">Proxy & Fingerprint Routing</h2>
                            <p className="text-xs text-slate-400 font-mono">:: External routing nodes and anti-detect profiles</p>
                        </div>
                    </div>

                    {!isEditing && (
                        <button onClick={() => { setCurrentProxy({ active: true, name: 'New Proxy Node' }); setIsEditing(true); }} className="ripple-btn px-4 py-2 border border-emerald-500/50 text-emerald-500 text-[10px] font-bold font-mono uppercase hover:bg-emerald-500 hover:text-black transition-all shadow-[0_0_15px_-5px_#10b981]">
                            [+ Add Routing Node]
                        </button>
                    )}
                </div>

                {isEditing ? (
                    <div className="space-y-4 bg-black/40 p-4 border border-slate-700">
                        <h3 className="text-xs font-mono text-emerald-400 uppercase tracking-widest">{currentProxy.id ? 'Edit Node' : 'New Node Configuration'}</h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label htmlFor={`nodeName_${currentProxy.id}`} className="block text-[10px] text-slate-400 font-mono mb-1">NODE_NAME</label>
                                <input id={`nodeName_${currentProxy.id}`} type="text" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.name || ""} onChange={e => setCurrentProxy({ ...currentProxy, name: e.target.value })} placeholder="E.g., US-East-1 Residential" />
                            </div>
                            <div>
                                <label htmlFor={`nodeNick_${currentProxy.id}`} className="block text-[10px] text-slate-400 font-mono mb-1">NICKNAME (optional)</label>
                                <input id={`nodeNick_${currentProxy.id}`} type="text" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.nickname || ""} onChange={e => setCurrentProxy({ ...currentProxy, nickname: e.target.value })} placeholder="E.g., fast-proxy" />
                            </div>
                            <div>
                                <label htmlFor={`serverUrl_${currentProxy.id}`} className="block text-[10px] text-slate-400 font-mono mb-1">SERVER_URL (http/socks5)</label>
                                <input id={`serverUrl_${currentProxy.id}`} type="text" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.server || ""} onChange={e => setCurrentProxy({ ...currentProxy, server: e.target.value })} placeholder="http://192.168.1.1:8080" />
                            </div>
                            <div>
                                <label className="block text-[10px] text-slate-400 font-mono mb-1">AUTH_USER (optional)</label>
                                <input type="text" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.username || ""} onChange={e => setCurrentProxy({ ...currentProxy, username: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-[10px] text-slate-400 font-mono mb-1">AUTH_PASS (optional)</label>
                                <input type="password" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.password || ""} onChange={e => setCurrentProxy({ ...currentProxy, password: e.target.value })} />
                            </div>
                            <div className="col-span-2">
                                <label className="block text-[10px] text-slate-400 font-mono mb-1">FINGERPRINT_UA_OVERRIDE (optional)</label>
                                <input type="text" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.fingerprint_ua || ""} onChange={e => setCurrentProxy({ ...currentProxy, fingerprint_ua: e.target.value })} placeholder="Mozilla/5.0 (Windows NT 10.0; Win64; x64)..." />
                            </div>
                            <div>
                                <label className="block text-[10px] text-slate-400 font-mono mb-1">LOCALE_OVERRIDE (optional)</label>
                                <input type="text" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.fingerprint_locale || ""} onChange={e => setCurrentProxy({ ...currentProxy, fingerprint_locale: e.target.value })} placeholder="en-US  (deixe vazio para pt-BR padrão)" />
                            </div>
                            <div>
                                <label className="block text-[10px] text-slate-400 font-mono mb-1">TIMEZONE_OVERRIDE (optional)</label>
                                <input type="text" className="w-full bg-[#050a14] border border-slate-700 p-2 text-xs font-mono text-white focus:border-emerald-500 outline-none"
                                    value={currentProxy.fingerprint_timezone || ""} onChange={e => setCurrentProxy({ ...currentProxy, fingerprint_timezone: e.target.value })} placeholder="America/New_York  (deixe vazio para Sao_Paulo padrão)" />
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-700">
                            <button onClick={() => setIsEditing(false)} className="px-4 py-2 border border-slate-600 text-slate-400 text-xs font-mono hover:text-white transition-colors">CANCEL</button>
                            <button onClick={saveProxy} className="px-6 py-2 border border-emerald-500 bg-emerald-500/10 text-emerald-400 font-bold text-xs font-mono hover:bg-emerald-500 hover:text-black transition-colors shadow-[0_0_10px_-2px_#10b981]">SAVE_NODE</button>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {loading ? (
                            <div className="text-center p-4 font-mono text-xs text-slate-500 animate-pulse">Scanning routing matrix...</div>
                        ) : proxies.length === 0 ? (
                            <div className="text-center p-8 font-mono text-xs text-slate-500 border border-dashed border-slate-800 bg-black/20">
                                No external routing nodes configured. Direct connection active.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 gap-4">
                                {proxies.map(p => (
                                    <div key={p.id} className="border border-slate-800 bg-black/40 p-4 relative group/card hover:border-emerald-500/30 transition-colors overflow-hidden">
                                        <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500/50 hidden group-hover/card:block blur-sm"></div>

                                        <div className="flex flex-col gap-3 mb-3">

                                            {/* Row 1: Name and Actions */}
                                            <div className="flex w-full items-start justify-between gap-3">
                                                <div className="flex items-center gap-2 min-w-0">
                                                    <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${p.active ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-red-500'}`}></div>
                                                    <h4 className="font-mono text-sm text-white font-bold truncate min-w-0" title={p.name}>{p.name}</h4>
                                                </div>
                                                <div className="flex items-center gap-1.5 flex-shrink-0">
                                                    <button onClick={() => testProxy(p.id)} disabled={testingId === p.id} className="text-sky-500 hover:text-sky-300 disabled:opacity-50 p-1 flex items-center justify-center transition-colors" title="Test Connection">
                                                        <span className={`material-symbols-outlined text-[16px] ${testingId === p.id ? 'animate-spin' : ''}`}>online_prediction</span>
                                                    </button>
                                                    <button onClick={() => { setCurrentProxy(p); setIsEditing(true); }} className="text-slate-400 hover:text-white p-1 flex items-center justify-center transition-colors" title="Edit">
                                                        <span className="material-symbols-outlined text-[16px]">edit</span>
                                                    </button>
                                                    <button onClick={() => deleteProxy(p.id)} className={`transition-colors rounded px-2 py-1 flex items-center justify-center min-w-[40px] h-[28px] ${deletingId === p.id ? 'bg-red-500 text-white shadow-[0_0_10px_-2px_#ef4444]' : 'text-red-500/50 hover:text-red-400'}`} title="Delete">
                                                        {deletingId === p.id ? <span className="text-[10px] font-bold">YES?</span> : <span className="material-symbols-outlined text-[16px]">delete</span>}
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Row 2: Nickname Container */}
                                            {p.nickname && (
                                                <div className="w-full">
                                                    <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] p-2 rounded font-mono leading-relaxed break-words whitespace-pre-wrap flex flex-col">
                                                        <span className="text-[9px] uppercase tracking-widest text-emerald-500/50 mb-1">Nickname / Alias</span>
                                                        {p.nickname}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                        <div className="text-[10px] font-mono text-slate-500 truncate max-w-full"><span className="text-emerald-500/50">SERVER:</span> {p.server}</div>
                                        {p.username && <div className="text-[10px] font-mono text-slate-500"><span className="text-emerald-500/50">AUTH:</span> {p.username}:****</div>}
                                        {p.fingerprint_ua && <div className="text-[10px] font-mono text-slate-500 truncate mt-1"><span className="text-emerald-500/50">UA Override:</span> {p.fingerprint_ua.substring(0, 30)}...</div>}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </section>
    );
}
