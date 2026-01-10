'use client';
import { useState, useEffect } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { CalendarIcon, ChevronLeftIcon, ChevronRightIcon, PlusIcon, MusicalNoteIcon } from '@heroicons/react/24/outline';
import { ScheduleEvent } from '../types';

export default function SchedulerPage() {
    const [currentDate, setCurrentDate] = useState(new Date());
    const [events, setEvents] = useState<ScheduleEvent[]>([]);
    const [viralBoost, setViralBoost] = useState(false);

    const handleQuickAdd = async () => {
        // Mock creation for verification
        const newEvent = {
            profile_id: "profile_123",
            video_path: "C:\\Videos\\viral_trend.mp4",
            scheduled_time: new Date().toISOString(),
            viral_music_enabled: viralBoost
        };

        try {
            const res = await fetch('http://localhost:8000/api/v1/scheduler/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newEvent)
            });
            if (res.ok) {
                const created = await res.json();
                setEvents([...events, created]);
                alert("Evento agendado com Viral Boost: " + viralBoost);
            }
        } catch (e) {
            console.error(e);
        }
    };

    // Fetch events from backend
    useEffect(() => {
        fetch('http://localhost:8000/api/v1/scheduler/list')
            .then(res => res.json())
            .then(data => setEvents(data))
            .catch(err => console.error("Erro ao carregar agenda:", err));
    }, []);

    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1));
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1));

    return (
        <div className="p-8 h-full flex flex-col">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-cmd-text flex items-center gap-2">
                        <CalendarIcon className="w-8 h-8 text-cmd-green" />
                        Smart Scheduler
                    </h1>
                    <p className="text-cmd-text-muted font-mono text-sm">// PLANEJAMENTO_TEMPORAL</p>
                </div>

                <div className="flex items-center gap-4 bg-cmd-card p-2 rounded-lg border border-cmd-border">
                    <button onClick={prevMonth} className="p-2 hover:bg-cmd-surface rounded-md text-cmd-text"><ChevronLeftIcon className="w-5 h-5" /></button>
                    <span className="font-mono text-cmd-purple font-bold w-32 text-center">
                        {format(currentDate, 'MMMM yyyy', { locale: ptBR }).toUpperCase()}
                    </span>
                    <button onClick={nextMonth} className="p-2 hover:bg-cmd-surface rounded-md text-cmd-text"><ChevronRightIcon className="w-5 h-5" /></button>
                </div>
            </div>

            {/* Config Panel */}
            <div className="flex items-center justify-between p-4 bg-cmd-card border border-cmd-border rounded-lg mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-cmd-purple/20 rounded-lg">
                        <MusicalNoteIcon className="w-5 h-5 text-cmd-purple" />
                    </div>
                    <div>
                        <span className="text-sm font-bold text-white block">Viral Audio Boost</span>
                        <span className="text-xs text-cmd-text-muted">Aplica top trend oculta para engajamento.</span>
                    </div>
                </div>

                <label className="relative inline-flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        checked={viralBoost}
                        onChange={(e) => setViralBoost(e.target.checked)}
                        className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cmd-purple"></div>
                </label>
            </div>

            <div className="flex-1 grid grid-cols-7 gap-4 bg-cmd-surface p-4 rounded-xl border border-cmd-border/50">
                {['DOM', 'SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB'].map(day => (
                    <div key={day} className="text-center font-mono text-xs text-cmd-text-muted py-2 border-b border-cmd-border mb-2">
                        {day}
                    </div>
                ))}

                {days.map((day) => {
                    const dayEvents = events.filter(e => isSameDay(new Date(e.scheduled_time), day));

                    return (
                        <div
                            key={day.toISOString()}
                            className={`
                                min-h-[100px] rounded-lg border border-dashed border-cmd-border/30 p-2 relative group transition-all
                                hover:border-cmd-purple hover:bg-cmd-purple/5
                            `}
                        >
                            <span className={`text-sm font-mono ${isSameDay(day, new Date()) ? 'text-cmd-green font-bold' : 'text-cmd-text-muted'}`}>
                                {format(day, 'd')}
                            </span>

                            <div className="mt-2 space-y-1">
                                {dayEvents.map(event => (
                                    <div key={event.id} className={`text-[10px] px-1 py-0.5 rounded truncate border flex items-center gap-1 ${event.viral_music_enabled ? 'bg-cmd-purple text-white border-cmd-purple' : 'bg-cmd-purple/20 text-cmd-purple border-cmd-purple/30'}`}>
                                        <span>⏰ {format(new Date(event.scheduled_time), 'HH:mm')}</span>
                                        {event.viral_music_enabled && <MusicalNoteIcon className="w-3 h-3 text-cmd-green animate-pulse" title="Viral Boost Active" />}
                                    </div>
                                ))}
                            </div>

                            {/* Add Button (Mock) */}
                            <button
                                onClick={handleQuickAdd}
                                className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 p-1 bg-cmd-green text-black rounded shadow-[0_0_10px_rgba(34,197,94,0.5)] transition-opacity"
                                title="Quick Add Current Date"
                            >
                                <PlusIcon className="w-4 h-4" />
                            </button>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
