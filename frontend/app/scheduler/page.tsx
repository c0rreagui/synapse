'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { getApiUrl } from '../utils/apiClient';
import { ScheduleEvent, TikTokProfile } from '../types';
import { getSavedProfiles, SavedProfile } from '../../services/profileService';
import ScheduledVideosModal from '../components/ScheduledVideosModal';
import EditScheduleModal from '../components/EditScheduleModal';
import { toast } from 'sonner';

// ─── Helpers ───────────────────────────────────────────────
function getMonthName(date: Date): string {
    return date.toLocaleDateString('pt-BR', { month: 'long' }).toUpperCase();
}

function isSameDay(d1: Date, d2: Date): boolean {
    return d1.getFullYear() === d2.getFullYear()
        && d1.getMonth() === d2.getMonth()
        && d1.getDate() === d2.getDate();
}

function dateKey(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

interface CalendarDay {
    date: Date;
    day: number;
    isCurrentMonth: boolean;
    isToday: boolean;
    events: ScheduleEvent[];
}

function generateCalendarDays(year: number, month: number, eventsMap: Map<string, ScheduleEvent[]>, today: Date): CalendarDay[] {
    const firstDay = new Date(year, month, 1);
    // Monday = 0, Sunday = 6 (ISO week)
    let startOffset = firstDay.getDay() - 1;
    if (startOffset < 0) startOffset = 6;

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const days: CalendarDay[] = [];

    // Previous month fill
    for (let i = startOffset - 1; i >= 0; i--) {
        const d = new Date(year, month, -i);
        days.push({
            date: d,
            day: d.getDate(),
            isCurrentMonth: false,
            isToday: false,
            events: eventsMap.get(dateKey(d)) || [],
        });
    }

    // Current month
    for (let i = 1; i <= daysInMonth; i++) {
        const d = new Date(year, month, i);
        days.push({
            date: d,
            day: i,
            isCurrentMonth: true,
            isToday: isSameDay(d, today),
            events: eventsMap.get(dateKey(d)) || [],
        });
    }

    // Next month fill (to complete 35 or 42 cells)
    const totalCells = days.length <= 35 ? 35 : 42;
    let nextDay = 1;
    while (days.length < totalCells) {
        const d = new Date(year, month + 1, nextDay++);
        days.push({
            date: d,
            day: d.getDate(),
            isCurrentMonth: false,
            isToday: false,
            events: eventsMap.get(dateKey(d)) || [],
        });
    }

    return days;
}

// ─── Status Colors ─────────────────────────────────────────
const STATUS_CRYSTAL: Record<string, { color: string; label: string }> = {
    pending: { color: '#f59e0b', label: 'Pendente' },
    ready: { color: '#22d3ee', label: 'Pronto' },
    processing: { color: '#a855f7', label: 'Processando' },
    completed: { color: '#22c55e', label: 'Publicado' },
    posted: { color: '#22c55e', label: 'Publicado' },
    done: { color: '#22c55e', label: 'Publicado' },
    failed: { color: '#ef4444', label: 'Falhou' },
    error: { color: '#ef4444', label: 'Erro' },
    paused_login_required: { color: '#f97316', label: 'Login Req.' },
};

// ─── Main Component ────────────────────────────────────────
export default function SchedulerPage() {
    // Core state
    const [currentDate, setCurrentDate] = useState<Date | null>(null);
    const [viewDate, setViewDate] = useState<Date>(new Date());
    const [events, setEvents] = useState<ScheduleEvent[]>([]);
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);
    const [loading, setLoading] = useState(true);

    // Modal state
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);
    const [isVideosModalOpen, setIsVideosModalOpen] = useState(false);
    const [editingEvent, setEditingEvent] = useState<ScheduleEvent | null>(null);

    // Drag state
    const [draggedEvent, setDraggedEvent] = useState<ScheduleEvent | null>(null);
    const [dragOverDate, setDragOverDate] = useState<string | null>(null);

    // ─── Data Loading ──────────────────────────────────────
    useEffect(() => {
        setCurrentDate(new Date());
    }, []);

    const fetchEvents = useCallback(async () => {
        try {
            const API = getApiUrl();
            const res = await axios.get(`${API}/api/v1/scheduler/list`);
            setEvents(res.data || []);
        } catch (err) {
            console.error('Error fetching schedule:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchProfiles = useCallback(async () => {
        try {
            const list = await getSavedProfiles();
            // Convert SavedProfile to TikTokProfile-compatible shape
            const mapped: TikTokProfile[] = list.map((p: SavedProfile) => ({
                id: p.id,
                label: p.label || p.username || p.id,
                username: p.username,
                status: 'active' as const,
            }));
            setProfiles(mapped);
        } catch (err) {
            console.error('Error fetching profiles:', err);
        }
    }, []);

    useEffect(() => {
        fetchEvents();
        fetchProfiles();
    }, [fetchEvents, fetchProfiles]);

    // ─── Events Map ────────────────────────────────────────
    const eventsMap = useMemo(() => {
        const map = new Map<string, ScheduleEvent[]>();
        events.forEach(ev => {
            if (!ev.scheduled_time) return;
            const d = new Date(ev.scheduled_time);
            const key = dateKey(d);
            if (!map.has(key)) map.set(key, []);
            map.get(key)!.push(ev);
        });
        return map;
    }, [events]);

    // ─── Calendar Grid ─────────────────────────────────────
    const today = currentDate || new Date();
    const calendarDays = useMemo(
        () => generateCalendarDays(viewDate.getFullYear(), viewDate.getMonth(), eventsMap, today),
        [viewDate, eventsMap, today]
    );

    // Dock: videos with status ready
    const dockItems = useMemo(
        () => events.filter(e => e.status === 'ready' || e.status === 'pending'),
        [events]
    );

    // ─── Navigation ────────────────────────────────────────
    const prevMonth = () => setViewDate(d => new Date(d.getFullYear(), d.getMonth() - 1, 1));
    const nextMonth = () => setViewDate(d => new Date(d.getFullYear(), d.getMonth() + 1, 1));
    const goToday = () => setViewDate(new Date());

    // ─── Day Click → Open Modal ────────────────────────────
    const handleDayClick = (day: CalendarDay) => {
        setSelectedDate(day.date);
        setIsVideosModalOpen(true);
    };

    // ─── Drag & Drop ───────────────────────────────────────
    const handleDragStart = (ev: ScheduleEvent) => {
        setDraggedEvent(ev);
    };

    const handleDragOver = (e: React.DragEvent, day: CalendarDay) => {
        e.preventDefault();
        setDragOverDate(dateKey(day.date));
    };

    const handleDragLeave = () => {
        setDragOverDate(null);
    };

    const handleDrop = async (e: React.DragEvent, day: CalendarDay) => {
        e.preventDefault();
        setDragOverDate(null);
        if (!draggedEvent) return;

        // Default to 12:00 of the target day
        const targetDate = new Date(day.date);
        targetDate.setHours(12, 0, 0, 0);
        const isoTime = targetDate.toISOString();

        try {
            const API = getApiUrl();
            if (draggedEvent.id && draggedEvent.status !== 'ready') {
                // Update existing event time
                await axios.patch(`${API}/api/v1/scheduler/${draggedEvent.id}`, {
                    scheduled_time: isoTime,
                });
                toast.success(`Evento movido para ${day.day}/${viewDate.getMonth() + 1}`);
            } else {
                // Schedule a ready item
                await axios.post(`${API}/api/v1/scheduler`, {
                    profile_id: draggedEvent.profile_id,
                    video_path: draggedEvent.video_path,
                    scheduled_time: isoTime,
                });
                toast.success(`Vídeo agendado para ${day.day}/${viewDate.getMonth() + 1}`);
            }
            await fetchEvents();
        } catch (err: any) {
            const msg = err?.response?.data?.detail || 'Erro ao mover evento';
            toast.error(msg);
        }
        setDraggedEvent(null);
    };

    // ─── Profile Helper ────────────────────────────────────
    const getProfileLabel = (id: string) => {
        const p = profiles.find(pr => pr.id === id);
        return p?.label || p?.username || id?.slice(0, 8) || '?';
    };

    // ─── Delete/Update Handlers for Modals ─────────────────
    const handleDeleteEvent = async (id: string) => {
        try {
            const API = getApiUrl();
            await axios.delete(`${API}/api/v1/scheduler/${id}`);
            toast.success('Evento removido');
            await fetchEvents();
        } catch {
            toast.error('Erro ao remover evento');
        }
    };

    const handleEditSave = async (eventId: string, data: any) => {
        try {
            const API = getApiUrl();
            await axios.patch(`${API}/api/v1/scheduler/${eventId}`, data);
            toast.success('Evento atualizado');
            setEditingEvent(null);
            await fetchEvents();
        } catch {
            toast.error('Erro ao atualizar evento');
        }
    };

    // ─── Display ───────────────────────────────────────────
    const displayMonth = viewDate ? getMonthName(viewDate) : '...';
    const displayYear = viewDate ? viewDate.getFullYear() : '';
    const rows = Math.ceil(calendarDays.length / 7);

    return (
        <div className="flex-1 flex flex-col relative overflow-hidden bg-background-dark text-slate-100 min-h-screen selection:bg-primary/30 w-full">
            <div className="parallax-bg"></div>

            <main className="flex-1 flex flex-col relative overflow-hidden w-full h-full max-w-[1600px] mx-auto">
                {/* ── Header ─────────────────────────────── */}
                <div className="px-8 py-6 flex flex-wrap gap-4 items-end justify-between z-30 relative pointer-events-none mt-4">
                    <div className="pointer-events-auto">
                        <div className="flex items-center gap-2 text-xs font-mono text-cyan-400/60 mb-2 tech-stencil">
                            <span className="material-symbols-outlined text-[14px]">history</span>
                            <span>Operações Temporais</span>
                            <span className="text-slate-600">/</span>
                            <span className="text-white font-bold">Visão em Grade</span>
                        </div>
                        <h1 className="text-5xl font-bold text-white tracking-tight flex items-center gap-4 font-display">
                            {displayMonth} <span className="text-slate-600 font-light">{displayYear}</span>
                            <div className="flex items-center gap-2 px-2 py-1 bg-cyan-400/10 border border-cyan-400/30 rounded-none backdrop-blur-sm">
                                <span className="size-1.5 bg-cyan-400 rounded-full animate-pulse-slow"></span>
                                <span className="text-[10px] font-mono font-bold text-cyan-400 tracking-widest">AO VIVO</span>
                            </div>
                        </h1>
                    </div>

                    {/* Navigation Controls */}
                    <div className="flex items-center gap-2 bg-black/60 p-1 border border-white/10 backdrop-blur-md shadow-2xl pointer-events-auto">
                        <button onClick={prevMonth} className="size-8 flex items-center justify-center hover:bg-white/5 border border-transparent hover:border-white/10 text-slate-300 transition-all">
                            <span className="material-symbols-outlined text-[18px]">chevron_left</span>
                        </button>
                        <button onClick={goToday} className="px-4 h-8 flex items-center justify-center bg-cyan-400/20 border border-cyan-400/50 text-cyan-400 font-bold text-[10px] tech-stencil hover:bg-cyan-400/30 transition-all shadow-[0_0_15px_rgba(7,182,213,0.15)]">
                            Presente
                        </button>
                        <button onClick={nextMonth} className="size-8 flex items-center justify-center hover:bg-white/5 border border-transparent hover:border-white/10 text-slate-300 transition-all">
                            <span className="material-symbols-outlined text-[18px]">chevron_right</span>
                        </button>
                    </div>
                </div>

                {/* ── Body: Grid + Dock ───────────────────── */}
                <div className="flex-1 px-8 pb-8 overflow-hidden flex gap-8 perspective-container relative z-10">
                    {/* Calendar Grid */}
                    <div className="flex-1 relative">
                        <div className="tilted-grid w-full h-full flex flex-col pt-8">
                            {/* Day Headers */}
                            <div className="grid grid-cols-7 mb-2 transform-style-3d">
                                {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map((day, i) => (
                                    <div key={day} className={`text-center text-[10px] font-bold ${i < 5 ? 'text-cyan-400/60 border-cyan-400/20' : 'text-slate-600 border-slate-800'} tech-stencil pb-2 border-b`}>
                                        {day}
                                    </div>
                                ))}
                            </div>

                            {/* Day Cells */}
                            <div className={`flex-1 grid grid-cols-7 grid-rows-${rows} gap-3 pb-12`}>
                                {calendarDays.map((cd, idx) => {
                                    const isDragTarget = dragOverDate === dateKey(cd.date);

                                    // Calculate Rate Limit (SYN-100)
                                    // A profile can only have 3 posts per day.
                                    const maxEventsOnSingleProfile = cd.events.reduce((acc, ev) => {
                                        acc[ev.profile_id] = (acc[ev.profile_id] || 0) + 1;
                                        return acc;
                                    }, {} as Record<string, number>);
                                    const profileRateLimitReached = Object.values(maxEventsOnSingleProfile).some(count => count >= 3);

                                    return (
                                        <div
                                            key={idx}
                                            onClick={() => cd.isCurrentMonth && handleDayClick(cd)}
                                            onDragOver={(e) => handleDragOver(e, cd)}
                                            onDragLeave={handleDragLeave}
                                            onDrop={(e) => handleDrop(e, cd)}
                                            className={`
                                                grid-cell relative p-2 group transition-all cursor-pointer
                                                ${cd.isToday
                                                    ? 'bg-[#060b0c]/80 border border-cyan-400/50 shadow-neon z-20 overflow-visible'
                                                    : cd.isCurrentMonth
                                                        ? 'bg-[#0c1618]/60 border border-white/10 hover:border-cyan-400/30'
                                                        : 'bg-[#060b0c]/20 border border-white/5'
                                                }
                                                ${isDragTarget ? 'border-cyan-400 bg-cyan-400/10 scale-[1.02]' : ''}
                                                ${profileRateLimitReached ? 'ring-1 ring-red-500/50' : ''}
                                            `}
                                        >
                                            {/* Today beam */}
                                            {cd.isToday && (
                                                <>
                                                    <div className="beam-of-light"></div>
                                                    <div className="beam-core"></div>
                                                </>
                                            )}

                                            {/* Day number */}
                                            <div className="flex justify-between items-start relative z-20">
                                                <span className={`font-mono text-xs ${cd.isToday ? 'text-cyan-400 font-bold text-sm drop-shadow-[0_0_5px_#0bf]' : cd.isCurrentMonth ? 'text-slate-400 group-hover:text-cyan-400 transition-colors' : 'text-slate-700'}`}>
                                                    {String(cd.day).padStart(2, '0')}
                                                </span>
                                                {cd.isToday && (
                                                    <span className="text-[8px] bg-cyan-400 text-black font-bold px-1 py-0.5 uppercase tracking-wider">Hoje</span>
                                                )}
                                                {cd.events.length > 0 && !cd.isToday && (
                                                    <span className="text-[8px] text-slate-500 font-mono">{cd.events.length}</span>
                                                )}
                                                {profileRateLimitReached && (
                                                    <span className="material-symbols-outlined text-[10px] text-red-400 opacity-80" aria-label="Rate Limit Atingido p/ Perfil (3/dia)">warning</span>
                                                )}
                                            </div>

                                            {/* Event Crystals (max 2 visible) */}
                                            {cd.events.slice(0, 2).map((ev, evi) => {
                                                const crystal = STATUS_CRYSTAL[ev.status] || STATUS_CRYSTAL.pending;
                                                const time = ev.scheduled_time ? new Date(ev.scheduled_time).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '--:--';
                                                return (
                                                    <div
                                                        key={ev.id || evi}
                                                        draggable
                                                        onDragStart={(e) => { e.stopPropagation(); handleDragStart(ev); }}
                                                        className="time-crystal mt-2 p-2 rounded-sm cursor-grab active:cursor-grabbing hover:brightness-125 transition-all"
                                                        style={{ '--crystal-color': crystal.color } as React.CSSProperties}
                                                    >
                                                        <div className="chronos-connector" style={{ '--color': crystal.color } as React.CSSProperties}></div>
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <span className="text-[9px] font-bold uppercase tracking-wider truncate" style={{ color: crystal.color }}>
                                                                {getProfileLabel(ev.profile_id)}
                                                            </span>
                                                            <span className="ml-auto size-1 rounded-full shadow-[0_0_5px]" style={{ backgroundColor: crystal.color, boxShadow: `0 0 5px ${crystal.color}` }}></span>
                                                        </div>
                                                        <div className="text-[10px] text-slate-300 font-mono">{time}</div>
                                                    </div>
                                                );
                                            })}
                                            {cd.events.length > 2 && (
                                                <div className="text-[9px] text-slate-500 font-mono mt-1 text-center font-bold">+{cd.events.length - 2} mais</div>
                                            )}

                                            {/* Empty State Visual Hint for Drag & Drop */}
                                            {cd.events.length === 0 && cd.isCurrentMonth && (
                                                <div className="absolute inset-0 m-auto w-8 h-8 rounded-full border border-dashed border-cyan-400/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-cyan-400 pointer-events-none mt-10">
                                                    <span className="material-symbols-outlined text-[16px]">add</span>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    {/* ── Staging Dock Panel ──────────────── */}
                    <div className="w-80 flex-shrink-0 flex flex-col gap-4 z-50">
                        <div className="glass-panel p-0 rounded-none flex-1 flex flex-col h-full border border-white/10 shadow-[0_0_20px_rgba(0,0,0,0.5)] relative overflow-hidden backdrop-blur-3xl">
                            <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-cyan-400/40"></div>
                            <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-cyan-400/40"></div>

                            <div className="p-5 border-b border-white/10 bg-[#060b0c]/80 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-cyan-400 text-[20px] animate-pulse-slow">precision_manufacturing</span>
                                    <h3 className="text-white font-bold text-xs tech-stencil">Doca de Preparação</h3>
                                </div>
                                <span className="text-[10px] font-mono text-slate-500">{dockItems.length} itens</span>
                            </div>

                            <div className="flex flex-col gap-0 overflow-y-auto flex-1 dock-slot scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                                {loading ? (
                                    <div className="p-8 text-center text-slate-600 text-xs font-mono animate-pulse">Carregando...</div>
                                ) : dockItems.length === 0 ? (
                                    <div className="p-8 text-center text-slate-600 text-xs font-mono">Nenhum vídeo na fila</div>
                                ) : (
                                    dockItems.map((ev) => {
                                        const crystal = STATUS_CRYSTAL[ev.status] || STATUS_CRYSTAL.pending;
                                        const filename = ev.video_path?.split(/[\\/]/).pop() || 'video.mp4';
                                        return (
                                            <div
                                                key={ev.id}
                                                draggable
                                                onDragStart={() => handleDragStart(ev)}
                                                className="p-4 border-b border-white/5 hover:bg-white/5 cursor-grab active:cursor-grabbing group transition-all relative payload-ready"
                                            >
                                                <div className="absolute left-0 top-0 bottom-0 w-0.5 group-hover:bg-cyan-400 transition-all" style={{ backgroundColor: `${crystal.color}33` }}></div>
                                                <div className="flex gap-4">
                                                    <div className="size-12 bg-black border border-white/10 relative overflow-hidden group-hover:border-cyan-400/50 transition-colors shrink-0 flex items-center justify-center">
                                                        <span className="material-symbols-outlined text-slate-600 text-[24px]">movie</span>
                                                        <div className="absolute bottom-0 right-0 bg-black/80 px-1 py-0.5 text-[8px] font-mono border-t border-l border-white/10" style={{ color: crystal.color }}>
                                                            {crystal.label}
                                                        </div>
                                                    </div>
                                                    <div className="flex-1 min-w-0 flex flex-col justify-center">
                                                        <h4 className="text-slate-200 text-xs font-bold truncate font-mono">{filename}</h4>
                                                        <div className="flex items-center gap-3 mt-1.5">
                                                            <div className="flex items-center gap-1 text-[10px] text-slate-500">
                                                                <span className="material-symbols-outlined text-[12px]">person</span>
                                                                {getProfileLabel(ev.profile_id)}
                                                            </div>
                                                            <div className="flex items-center gap-1 text-[10px]" style={{ color: crystal.color }}>
                                                                <span className="material-symbols-outlined text-[12px]">circle</span>
                                                                {crystal.label}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center justify-center text-slate-600 group-hover:text-cyan-400 transition-colors">
                                                        <span className="material-symbols-outlined text-[20px]">drag_indicator</span>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>

                        {/* Uplink Rate Panel */}
                        <div className="glass-panel p-4 rounded-none border border-white/10 relative overflow-hidden backdrop-blur-3xl">
                            <div className="absolute top-0 left-0 w-full h-[1px] bg-cyan-400/50 shadow-[0_0_10px_#0bf] animate-[scan_2s_ease-in-out_infinite]"></div>
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-[10px] font-bold text-slate-400 tech-stencil">Eventos Agendados</span>
                                <span className="text-cyan-400 text-xs font-mono font-bold">
                                    {events.filter(e => e.status === 'pending').length} pendentes
                                </span>
                            </div>
                            <div className="relative h-12 w-full flex items-end gap-[2px] opacity-80">
                                {/* Mini bar chart of events per day (next 8 days) */}
                                {Array.from({ length: 8 }).map((_, i) => {
                                    const d = new Date();
                                    d.setDate(d.getDate() + i);
                                    const key = dateKey(d);
                                    const count = eventsMap.get(key)?.length || 0;
                                    const height = count ? Math.min(count * 25, 90) : 5;
                                    return (
                                        <div
                                            key={i}
                                            className="flex-1 bg-gradient-to-t from-cyan-400/10 to-cyan-400/50 transition-all"
                                            style={{ height: `${height}%` }}
                                        ></div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            {/* ── Modals ─────────────────────────────────── */}
            <ScheduledVideosModal
                isOpen={isVideosModalOpen}
                onClose={() => setIsVideosModalOpen(false)}
                profiles={profiles}
                onDelete={handleDeleteEvent}
                onUpdate={fetchEvents}
            />

            <EditScheduleModal
                isOpen={!!editingEvent}
                onClose={() => setEditingEvent(null)}
                event={editingEvent}
                profiles={profiles}
                onSave={handleEditSave}
            />
        </div>
    );
}
