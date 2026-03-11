'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useNotifications, notificationStore } from '../store/notificationStore';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { CheckCircleIcon, ExclamationCircleIcon, InformationCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'; // Adjust icons if necessary

export function NotificationCenter() {
    const [isOpen, setIsOpen] = useState(false);
    const notifications = useNotifications();
    const dropdownRef = useRef<HTMLDivElement>(null);

    const unreadCount = notifications.filter(n => !n.read).length;

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const getIcon = (type: string) => {
        switch (type) {
            case 'success': return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
            case 'error': return <ExclamationCircleIcon className="w-5 h-5 text-red-400" />;
            case 'warning': return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400" />;
            case 'info':
            default: return <InformationCircleIcon className="w-5 h-5 text-blue-400" />;
        }
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative w-10 h-10 rounded-full border border-white/10 flex items-center justify-center bg-white/5 hover:bg-white/10 transition-colors"
            >
                <span className="material-symbols-outlined text-slate-300">notifications</span>
                {unreadCount > 0 && (
                    <span className="absolute top-0 right-0 w-4 h-4 bg-red-500 rounded-full text-[9px] font-bold flex items-center justify-center border-2 border-[#0A0A0A]">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="absolute right-0 mt-2 w-80 bg-slate-900 border border-white/10 shadow-2xl rounded-xl overflow-hidden z-50 flex flex-col max-h-[400px]"
                    >
                        <div className="p-4 border-b border-white/10 flex justify-between items-center bg-black/20">
                            <h3 className="font-display font-bold text-sm text-white">Centro de Notificações</h3>
                            {notifications.length > 0 && (
                                <button
                                    onClick={() => notificationStore.markAllAsRead()}
                                    className="text-[10px] text-cyan-400 hover:text-cyan-300 uppercase tracking-widest font-mono"
                                >
                                    Marcar lidas
                                </button>
                            )}
                        </div>

                        <div className="overflow-y-auto flex-1 scrollbar-hide">
                            {notifications.length === 0 ? (
                                <div className="p-8 text-center text-slate-500 font-mono text-xs flex flex-col items-center justify-center gap-2">
                                    <span className="material-symbols-outlined text-3xl opacity-50">notifications_off</span>
                                    Nenhuma notificação na escuta.
                                </div>
                            ) : (
                                <div className="flex flex-col">
                                    {notifications.map(notif => (
                                        <div
                                            key={notif.id}
                                            className={`p-4 border-b border-white/5 flex gap-3 hover:bg-white/5 transition-colors cursor-pointer ${notif.read ? 'opacity-60' : 'bg-blue-500/5'}`}
                                            onClick={() => !notif.read && notificationStore.markAsRead(notif.id)}
                                        >
                                            <div className="mt-0.5 flex-shrink-0">
                                                {getIcon(notif.type)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className={`text-sm font-medium ${notif.read ? 'text-slate-300' : 'text-white'}`}>
                                                    {notif.title}
                                                </p>
                                                {notif.message && (
                                                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                                                        {notif.message}
                                                    </p>
                                                )}
                                                <p className="text-[10px] font-mono text-slate-500 mt-2">
                                                    {formatDistanceToNow(notif.date, { addSuffix: true, locale: ptBR })}
                                                </p>
                                            </div>
                                            {!notif.read && (
                                                <div className="w-2 h-2 rounded-full bg-cyan-500 mt-1.5 flex-shrink-0 shadow-[0_0_8px_rgba(0,240,255,0.8)]"></div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        {notifications.length > 0 && (
                            <div className="p-2 border-t border-white/10 bg-black/20">
                                <button
                                    onClick={() => notificationStore.clearAll()}
                                    className="w-full py-2 text-[10px] text-slate-400 hover:text-white uppercase font-mono tracking-widest transition-colors flex items-center justify-center gap-2"
                                >
                                    <span className="material-symbols-outlined text-[14px]">delete</span>
                                    Limpar Histórico
                                </button>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
