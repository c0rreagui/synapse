import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import { XMarkIcon, DocumentIcon, ClockIcon, ExclamationTriangleIcon, CheckCircleIcon, CubeTransparentIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format } from 'date-fns';
import { useWebSocketContext } from '../context/WebSocketContext';

interface FileItem {
    name: string;
    size: number;
    modified: string;
    path: string;
}

interface MetricsModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialTab?: string;
}

const API_BASE = 'http://localhost:8000/api/v1';

export default function MetricsModal({ isOpen, onClose, initialTab = 'processing' }: MetricsModalProps) {
    const [files, setFiles] = useState<Record<string, FileItem[]>>({
        queued: [],
        processing: [],
        completed: [],
        failed: []
    });
    const [loading, setLoading] = useState(false);

    // Map initialTab (e.g. 'queued') to index? Or use Tab.Group controlled?
    // Let's use controlled index.
    const tabs = ['queued', 'processing', 'completed', 'failed'];
    const [selectedIndex, setSelectedIndex] = useState(tabs.indexOf(initialTab));

    useEffect(() => {
        if (isOpen) {
            fetchFiles();
            const idx = tabs.indexOf(initialTab);
            if (idx !== -1) setSelectedIndex(idx);
        }
    }, [isOpen, initialTab]);

    const fetchFiles = async () => {
        console.log("DEBUG: API_BASE is", API_BASE);
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/ingest/files`);
            if (res.ok) {
                const data = await res.json();
                setFiles(data);
            }
        } catch (e) {
            console.error("Failed to fetch files details", e);
        }
        setLoading(false);
    };

    const formatSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'queued': return ClockIcon;
            case 'processing': return CubeTransparentIcon;
            case 'completed': return CheckCircleIcon;
            case 'failed': return ExclamationTriangleIcon;
            default: return DocumentIcon;
        }
    };

    const getColor = (type: string) => {
        switch (type) {
            case 'queued': return 'text-synapse-amber bg-synapse-amber/10 border-synapse-amber/20';
            case 'processing': return 'text-synapse-cyan bg-synapse-cyan/10 border-synapse-cyan/20';
            case 'completed': return 'text-synapse-emerald bg-synapse-emerald/10 border-synapse-emerald/20';
            case 'failed': return 'text-red-500 bg-red-500/10 border-red-500/20';
            default: return 'text-gray-400 bg-gray-800 border-gray-700';
        }
    };

    return (
        <Transition show={isOpen} as={Fragment}>
            <Dialog onClose={onClose} className="relative z-50">
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" />
                </Transition.Child>

                <div className="fixed inset-0 flex items-center justify-center p-4">
                    <Transition.Child
                        as={Fragment}
                        enter="ease-out duration-300"
                        enterFrom="opacity-0 scale-95"
                        enterTo="opacity-100 scale-100"
                        leave="ease-in duration-200"
                        leaveFrom="opacity-100 scale-100"
                        leaveTo="opacity-0 scale-95"
                    >
                        <Dialog.Panel className="w-full max-w-3xl rounded-xl bg-[#0f0a15] border border-white/10 shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
                            {/* Header */}
                            <div className="flex items-center justify-between p-6 border-b border-white/5 bg-white/5">
                                <Dialog.Title className="text-xl font-bold text-white flex items-center gap-2">
                                    <DocumentIcon className="w-6 h-6 text-synapse-primary" />
                                    <span>Pipeline Details</span>
                                </Dialog.Title>
                                <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                                    <XMarkIcon className="w-6 h-6" />
                                </button>
                            </div>

                            <Tab.Group selectedIndex={selectedIndex} onChange={setSelectedIndex}>
                                <Tab.List className="flex space-x-1 bg-black/20 p-1 border-b border-white/5">
                                    {tabs.map((tab) => (
                                        <Tab
                                            key={tab}
                                            className={({ selected }) =>
                                                clsx(
                                                    'w-full rounded-lg py-2.5 text-sm font-medium leading-5 uppercase tracking-wider',
                                                    'focus:outline-none focus:ring-0 transition-all',
                                                    selected
                                                        ? 'bg-white/10 text-white shadow'
                                                        : 'text-gray-500 hover:bg-white/[0.05] hover:text-gray-300'
                                                )
                                            }
                                        >
                                            {tab} ({files[tab]?.length || 0})
                                        </Tab>
                                    ))}
                                </Tab.List>
                                <Tab.Panels className="flex-1 overflow-y-auto p-6 bg-grid-pattern">
                                    {tabs.map((tab) => {
                                        const currentFiles = files[tab] || [];
                                        const Icon = getIcon(tab);
                                        const colorClass = getColor(tab);

                                        return (
                                            <Tab.Panel key={tab} className="space-y-3 focus:outline-none">
                                                {loading ? (
                                                    <div className="text-center py-10 text-gray-500 animate-pulse">Loading data...</div>
                                                ) : currentFiles.length === 0 ? (
                                                    <div className="flex flex-col items-center justify-center py-12 text-gray-500 border border-dashed border-white/10 rounded-xl">
                                                        <Icon className="w-12 h-12 mb-3 opacity-20" />
                                                        <p>No files in {tab} state</p>
                                                    </div>
                                                ) : (
                                                    currentFiles.map((file, idx) => (
                                                        <div key={idx} className="flex items-center justify-between p-4 rounded-lg bg-black/40 border border-white/5 hover:border-white/10 transition-colors group">
                                                            <div className="flex items-center gap-4">
                                                                <div className={clsx("w-10 h-10 rounded-lg flex items-center justify-center", colorClass)}>
                                                                    <Icon className="w-5 h-5" />
                                                                </div>
                                                                <div>
                                                                    <h4 className="text-white font-mono text-sm break-all">{file.name}</h4>
                                                                    <p className="text-xs text-gray-500 flex items-center gap-2 mt-1">
                                                                        <span>{formatSize(file.size)}</span>
                                                                        <span className="w-1 h-1 rounded-full bg-gray-700" />
                                                                        <span>{format(new Date(file.modified), 'PP pp')}</span>
                                                                    </p>
                                                                </div>
                                                            </div>
                                                            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                                                                {/* Actions later? */}
                                                            </div>
                                                        </div>
                                                    ))
                                                )}
                                            </Tab.Panel>
                                        );
                                    })}
                                </Tab.Panels>
                            </Tab.Group>
                        </Dialog.Panel>
                    </Transition.Child>
                </div>
            </Dialog>
        </Transition>
    );
}
