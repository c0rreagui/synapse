'use client';
import { useState, useEffect } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { CalendarIcon, ChevronLeftIcon, ChevronRightIcon, PlusIcon, MusicalNoteIcon } from '@heroicons/react/24/outline';
import { ScheduleEvent, TikTokProfile } from '../types';
import Sidebar from '../components/Sidebar';
import { StitchCard } from '../components/StitchCard';
import { NeonButton } from '../components/NeonButton';
import SchedulingModal, { SchedulingData } from '../components/SchedulingModal';
import BatchUploadModal from '../components/BatchUploadModal';
import DayDetailsModal from '../components/DayDetailsModal';
import clsx from 'clsx';
import { toast } from 'sonner';

export default function SchedulerPage() {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState<ScheduleEvent[]>([]);
    const [viralBoost, setViralBoost] = useState(false);
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
    const [isDayDetailsOpen, setIsDayDetailsOpen] = useState(false);
    const [modalDate, setModalDate] = useState(new Date());

    // Load Events & Profiles
    const fetchData = async () => {
        try {
            const [eventsRes, profilesRes] = await Promise.all([
                fetch('http://localhost:8000/api/v1/scheduler/list'),
                fetch('http://localhost:8000/api/v1/profiles')
            ]);

            if (eventsRes.ok) setEvents(await eventsRes.json());
            if (profilesRes.ok) setProfiles(await profilesRes.json());
        } catch (err) {
            console.error("Erro ao carregar dados:", err);
            toast.error("Erro ao carregar dados do servidor");
        }
    };

    useEffect(() => {
        fetchData();
        // Set up interval to verify updates if needed, or rely on optimistic updates
    }, []);

    const openDayDetails = (date: Date) => {
        if (!isSameMonth(date, currentDate)) return; // Optional: Only allow current month interaction? No, allow all.
        setModalDate(date);
        setIsDayDetailsOpen(true);
    };

    const handleDeleteEvent = async (eventId: string) => {
        try {
            const res = await fetch(`http://localhost:8000/api/v1/scheduler/${eventId}`, { method: 'DELETE' });
            if (!res.ok) throw new Error("Falha ao deletar");

            // Optimistic update or refetch
            setEvents(prev => prev.filter(e => e.id !== eventId));
            toast.success("Agendamento removido");
        } catch (e) {
            console.error(e);
            toast.error("Erro ao remover");
        }
    };

    const handleEditEvent = async (eventId: string, newTime: string) => {
        // newTime is HH:mm. We need to combine it with the event's original date.
        const originalEvent = events.find(e => e.id === eventId);
        if (!originalEvent) return;

        const originalDate = new Date(originalEvent.scheduled_time);
        const [hours, minutes] = newTime.split(':').map(Number);

        const newDate = new Date(originalDate);
        newDate.setHours(hours, minutes);

        try {
            const res = await fetch(`http://localhost:8000/api/v1/scheduler/${eventId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scheduled_time: newDate.toISOString() })
            });
            if (!res.ok) throw new Error("Falha ao editar");

            // Optimistic Update
            setEvents(prev => prev.map(e =>
                e.id === eventId ? { ...e, scheduled_time: newDate.toISOString() } : e
            ));
            toast.success("Horário atualizado");
        } catch (e) {
            console.error(e);
            toast.error("Erro ao atualizar horário");
        }
    };

    const handleScheduleSubmit = async (data: SchedulingData) => {
        try {
            // Iterate over selected profiles and create an event for each
            const promises = data.profile_ids.map(async (profileId) => {
                const payload = {
                    profile_id: profileId,
                    video_path: "C:\\Videos\\viral_trend.mp4", // Mock for visualization
                    scheduled_time: data.scheduled_time,
                    viral_music_enabled: data.viral_music_enabled,
                    music_volume: data.music_volume, // Updated from intensity
                    trend_category: data.trend_category
                };

                const res = await fetch('http://localhost:8000/api/v1/scheduler/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.status === 409) {
                    // Propagate 409 to modal
                    const err = await res.json();
                    throw { status: 409, response: err.detail };
                }

                if (!res.ok) throw new Error("Falha ao agendar");
                return res.json();
            });

            await Promise.all(promises);

            // Refresh events
            fetchData();
            toast.success(`Agendado com sucesso para ${data.profile_ids.length} perfil(s)!`);
        } catch (e: any) {
            // If it's a conflict, rethrow so modal handles it
            if (e.status === 409) throw e;

            console.error("Erro ao agendar:", e);
            toast.error(e.message || "Erro ao agendar");
            throw e; // Ensure modal knows it failed
        }
    };

    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1));

    return (
        <div className="flex min-h-screen bg-synapse-bg text-synapse-text font-sans selection:bg-synapse-primary selection:text-white">
            <Sidebar />

            <main className="flex-1 p-8 overflow-y-auto bg-grid-pattern flex flex-col">
                <header className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-2xl font-bold text-white flex items-center gap-3 m-0">
                            <CalendarIcon className="w-8 h-8 text-synapse-purple" />
                            Smart Scheduler
                        </h2>
                        <p className="text-sm text-gray-500 font-mono m-0 mt-1">// PLANEJAMENTO_TEMPORAL</p>
                    </div>

                    <div className="flex items-center gap-4 bg-[#1c2128] p-2 rounded-xl border border-white/10 shadow-lg">
                        <button onClick={prevMonth} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white transition-colors">
                            <ChevronLeftIcon className="w-5 h-5" />
                        </button>
                        <span className="font-mono text-synapse-purple font-bold w-40 text-center uppercase tracking-wider text-sm">
                            {format(currentDate, 'MMMM yyyy', { locale: ptBR })}
                        </span>
                        <button onClick={nextMonth} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white transition-colors">
                            <ChevronRightIcon className="w-5 h-5" />
                        </button>
                    </div>

                    <button
                        onClick={() => setIsBatchModalOpen(true)}
                        className="flex items-center gap-2 px-6 py-2.5 bg-synapse-purple/10 border border-synapse-purple/30 hover:bg-synapse-purple/20 rounded-xl text-synapse-purple text-sm font-bold transition-all shadow-[0_0_15px_rgba(139,92,246,0.1)] hover:shadow-[0_0_20px_rgba(139,92,246,0.3)]"
                    >
                        <span>📦 Bulk Upload</span>
                    </button>
                </header>

                {/* Config Panel */}
                <StitchCard className="p-5 mb-6 flex items-center justify-between bg-black/40 backdrop-blur-md">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-synapse-purple/15 rounded-xl border border-synapse-purple/20">
                            <MusicalNoteIcon className="w-6 h-6 text-synapse-purple" />
                        </div>
                        <div>
                            <span className="text-base font-bold text-white block">Viral Audio Boost</span>
                            <span className="text-sm text-gray-500">Aplica top trend oculta para engajamento.</span>
                        </div>
                    </div>

                    <label className="relative inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            checked={viralBoost}
                            onChange={(e) => setViralBoost(e.target.checked)}
                            className="sr-only peer"
                        />
                        <div className="w-12 h-7 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-synapse-purple border border-gray-600 peer-checked:border-synapse-purple/50 shadow-inner"></div>
                    </label>
                </StitchCard>

                {/* Calendar Grid */}
                <StitchCard className="flex-1 p-6 relative bg-black/40 backdrop-blur-sm border border-white/5">
                    <div className="grid grid-cols-7 gap-4 mb-4 pb-4 border-b border-white/5">
                        {['DOM', 'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB'].map(day => (
                            <div key={day} className="text-center font-mono text-xs text-gray-500 font-bold uppercase tracking-widest opacity-70">
                                {day}
                            </div>
                        ))}
                    </div>

                    <div className="grid grid-cols-7 gap-2 h-[600px] overflow-y-auto custom-scrollbar">
                        {days.map((day) => {
                            const dayEvents = events.filter(e => isSameDay(new Date(e.scheduled_time), day));
                            const isToday = isSameDay(day, new Date());

                            return (
                                <div
                                    key={day.toISOString()}
                                    className={clsx(
                                        "min-h-[120px] rounded-xl border p-3 relative group transition-all duration-300 flex flex-col gap-2 cursor-pointer",
                                        isToday
                                            ? "bg-synapse-purple/5 border-synapse-purple/50 shadow-[inset_0_0_20px_rgba(139,92,246,0.05)]"
                                            : "bg-white/[0.02] border-white/5 hover:border-synapse-purple/30 hover:bg-white/5 hover:shadow-lg hover:shadow-synapse-purple/5"
                                    )}
                                    onClick={() => openDayDetails(day)}
                                >
                                    <span className={clsx(
                                        "text-sm font-mono block mb-1 p-1 w-7 h-7 flex items-center justify-center rounded-full transition-colors",
                                        isToday ? "bg-synapse-purple text-white font-bold shadow-lg shadow-synapse-purple/40" : "text-gray-500 group-hover:text-white"
                                    )}>
                                        {format(day, 'd')}
                                    </span>

                                    <div className="space-y-1.5 overflow-y-auto max-h-[80px] custom-scrollbar pointer-events-none">
                                        {dayEvents.map(event => (
                                            <div
                                                key={event.id}
                                                className={clsx(
                                                    "text-[10px] px-2 py-1.5 rounded-md truncate border flex items-center gap-1.5",
                                                    event.viral_music_enabled
                                                        ? "bg-synapse-purple/90 text-white border-transparent shadow-sm"
                                                        : "bg-synapse-purple/10 text-synapse-purple border-synapse-purple/20"
                                                )}
                                            >
                                                <span className="font-bold opacity-80">{format(new Date(event.scheduled_time), 'HH:mm')}</span>
                                                {event.viral_music_enabled && (
                                                    <MusicalNoteIcon className="w-3 h-3 text-white" />
                                                )}
                                            </div>
                                        ))}
                                        {dayEvents.length > 3 && (
                                            <div className="text-[9px] text-center text-gray-500 font-medium">
                                                +{dayEvents.length - 3} mais
                                            </div>
                                        )}
                                    </div>

                                    {/* Hover hint */}
                                    <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-b-xl" />
                                </div>
                            );
                        })}
                    </div>
                </StitchCard>

                {/* Modals */}
                <SchedulingModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSubmit={handleScheduleSubmit}
                    initialDate={modalDate}
                    initialViralBoost={viralBoost}
                    profiles={profiles}
                />

                <BatchUploadModal
                    isOpen={isBatchModalOpen}
                    onClose={() => setIsBatchModalOpen(false)}
                    onSuccess={() => {
                        fetchData();
                        setIsBatchModalOpen(false);
                        toast.success("Campanha iniciada com sucesso!");
                    }}
                    profiles={profiles}
                />

                <DayDetailsModal
                    isOpen={isDayDetailsOpen}
                    onClose={() => setIsDayDetailsOpen(false)}
                    date={modalDate}
                    events={events.filter(e => isSameDay(new Date(e.scheduled_time), modalDate))}
                    profiles={profiles}
                    onDeleteEvent={handleDeleteEvent}
                    onEditEvent={handleEditEvent}
                    onAddEvent={() => {
                        setIsDayDetailsOpen(false);
                        setIsModalOpen(true);
                    }}
                />
            </main>
        </div>
    );
}
