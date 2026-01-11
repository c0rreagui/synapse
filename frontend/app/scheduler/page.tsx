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
import clsx from 'clsx';

export default function SchedulerPage() {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState<ScheduleEvent[]>([]);
    const [viralBoost, setViralBoost] = useState(false);
    const [profiles, setProfiles] = useState<TikTokProfile[]>([]);

    // Modal State
    const [isModalOpen, setIsModalOpen] = useState(false);
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
        }
    };

    useEffect(() => {
        fetchData();
        // Set up interval to verify updates if needed, or rely on optimistic updates
    }, []);

    const openModal = (date: Date) => {
        setModalDate(date);
        setIsModalOpen(true);
    };

    const handleScheduleSubmit = async (data: SchedulingData) => {
        try {
            // Iterate over selected profiles and create an event for each
            const promises = data.profile_ids.map(profileId => {
                const newEvent = {
                    profile_id: profileId,
                    video_path: "C:\\Videos\\viral_trend.mp4", // Mock for visualization
                    scheduled_time: data.scheduled_time,
                    viral_music_enabled: data.viral_music_enabled
                };

                return fetch('http://localhost:8000/api/v1/scheduler/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newEvent)
                });
            });

            await Promise.all(promises);

            // Refresh events
            fetchData();
            // alert(`Agendado com sucesso para ${data.profile_ids.length} perfil(s)!`); // Removed alert for smoother E2E
        } catch (e) {
            console.error("Erro ao agendar:", e);
            alert("Erro ao agendar");
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

                    <div className="flex items-center gap-4 bg-[#1c2128] p-2 rounded-xl border border-white/10">
                        <button onClick={prevMonth} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors">
                            <ChevronLeftIcon className="w-5 h-5" />
                        </button>
                        <span className="font-mono text-synapse-purple font-bold w-40 text-center uppercase tracking-wider">
                            {format(currentDate, 'MMMM yyyy', { locale: ptBR })}
                        </span>
                        <button onClick={nextMonth} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors">
                            <ChevronRightIcon className="w-5 h-5" />
                        </button>
                    </div>
                </header>

                {/* Config Panel */}
                <StitchCard className="p-5 mb-6 flex items-center justify-between">
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
                        <div className="w-12 h-7 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-synapse-purple border border-gray-600 peer-checked:border-synapse-purple/50"></div>
                    </label>
                </StitchCard>

                {/* Calendar Grid */}
                <StitchCard className="flex-1 p-6 relative">
                    <div className="grid grid-cols-7 gap-4 mb-4 pb-4 border-b border-white/5">
                        {['DOM', 'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB'].map(day => (
                            <div key={day} className="text-center font-mono text-xs text-gray-500 font-bold uppercase tracking-widest">
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
                                        "min-h-[100px] rounded-xl border p-3 relative group transition-all duration-300 flex flex-col gap-2",
                                        isToday
                                            ? "bg-synapse-purple/10 border-synapse-purple/50"
                                            : "bg-black/20 border-white/5 hover:border-synapse-purple/30 hover:bg-white/5"
                                    )}
                                    // Clicking anywhere on the day cell opens the modal
                                    onClick={(e) => {
                                        // Prevent triggering if clicked on an event
                                        if ((e.target as HTMLElement).closest('.event-item')) return;
                                        openModal(day);
                                    }}
                                >
                                    <span className={clsx(
                                        "text-sm font-mono block mb-1",
                                        isToday ? "text-synapse-purple font-bold" : "text-gray-500"
                                    )}>
                                        {format(day, 'd')}
                                    </span>

                                    <div className="space-y-1.5 overflow-y-auto max-h-[80px] custom-scrollbar">
                                        {dayEvents.map(event => (
                                            <div
                                                key={event.id}
                                                className={clsx(
                                                    "event-item text-[10px] px-2 py-1 rounded truncate border flex items-center gap-1.5 transition-all select-none",
                                                    event.viral_music_enabled
                                                        ? "bg-synapse-purple text-white border-transparent"
                                                        : "bg-synapse-purple/10 text-synapse-purple border-synapse-purple/20"
                                                )}
                                                onClick={(e) => {
                                                    e.stopPropagation(); // Don't open new modal when clicking event
                                                    alert(`Evento: ${event.id}\nPerfil: ${event.profile_id}`);
                                                }}
                                            >
                                                <span>⏰ {format(new Date(event.scheduled_time), 'HH:mm')}</span>
                                                {event.viral_music_enabled && (
                                                    <MusicalNoteIcon className="w-3 h-3 text-white animate-pulse" title="Viral Boost Active" />
                                                )}
                                            </div>
                                        ))}
                                    </div>

                                    {/* Add Button */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            openModal(day);
                                        }}
                                        className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 p-1.5 bg-synapse-emerald hover:bg-synapse-emerald/90 text-black rounded-lg shadow-lg shadow-synapse-emerald/20 transition-all transform hover:scale-110"
                                        title="Agendar neste dia"
                                    >
                                        <PlusIcon className="w-4 h-4" />
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </StitchCard>

                {/* Scheduling Modal */}
                <SchedulingModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSubmit={handleScheduleSubmit}
                    initialDate={modalDate}
                    initialViralBoost={viralBoost}
                    profiles={profiles}
                />
            </main>
        </div>
    );
}
