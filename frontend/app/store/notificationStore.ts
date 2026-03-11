import { useSyncExternalStore } from 'react';

export interface NotificationItem {
    id: string;
    type: 'success' | 'error' | 'info' | 'warning';
    title: string;
    message?: string;
    date: Date;
    read: boolean;
}

let notifications: NotificationItem[] = [];
let listeners: Array<() => void> = [];

const emitChange = () => {
    for (let listener of listeners) {
        listener();
    }
};

export const notificationStore = {
    addNotification(notification: Omit<NotificationItem, 'id' | 'date' | 'read'>) {
        const newNotif: NotificationItem = {
            ...notification,
            id: Math.random().toString(36).substring(2, 9),
            date: new Date(),
            read: false
        };
        notifications = [newNotif, ...notifications].slice(0, 100); // Keep last 100
        emitChange();
    },
    markAsRead(id: string) {
        notifications = notifications.map(n => n.id === id ? { ...n, read: true } : n);
        emitChange();
    },
    markAllAsRead() {
        notifications = notifications.map(n => ({ ...n, read: true }));
        emitChange();
    },
    clearAll() {
        notifications = [];
        emitChange();
    },
    subscribe(listener: () => void) {
        listeners = [...listeners, listener];
        return () => {
            listeners = listeners.filter(l => l !== listener);
        };
    },
    getSnapshot() {
        return notifications;
    }
};

export function useNotifications() {
    return useSyncExternalStore(notificationStore.subscribe, notificationStore.getSnapshot, notificationStore.getSnapshot);
}
