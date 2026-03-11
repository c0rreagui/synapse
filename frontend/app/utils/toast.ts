import { toast as sonnerToast, ExternalToast } from 'sonner';
import { notificationStore } from '../store/notificationStore';

const extractDescription = (data?: ExternalToast): string | undefined => {
    if (!data) return undefined;
    if (typeof data.description === 'string') return data.description;
    return undefined;
};

const toastHandler = Object.assign((message: string | React.ReactNode, data?: ExternalToast) => {
    sonnerToast(message, data);
    notificationStore.addNotification({ type: 'info', title: String(message), message: extractDescription(data) });
}, sonnerToast, {
    success: (message: string | React.ReactNode, data?: ExternalToast) => {
        sonnerToast.success(message, data);
        notificationStore.addNotification({ type: 'success', title: String(message), message: extractDescription(data) });
    },
    error: (message: string | React.ReactNode, data?: ExternalToast) => {
        sonnerToast.error(message, data);
        notificationStore.addNotification({ type: 'error', title: String(message), message: extractDescription(data) });
    },
    info: (message: string | React.ReactNode, data?: ExternalToast) => {
        sonnerToast.info(message, data);
        notificationStore.addNotification({ type: 'info', title: String(message), message: extractDescription(data) });
    },
    warning: (message: string | React.ReactNode, data?: ExternalToast) => {
        sonnerToast.warning(message, data);
        notificationStore.addNotification({ type: 'warning', title: String(message), message: extractDescription(data) });
    }
});

export const toast = toastHandler;
