import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import { XMarkIcon, DocumentIcon, ClockIcon, ExclamationTriangleIcon, CheckCircleIcon, CubeTransparentIcon, ArrowPathIcon, TrashIcon, EyeIcon, PlayIcon, CalendarIcon, PencilIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { format } from 'date-fns';
import { useWebSocketContext } from '../context/WebSocketContext';
import { toast } from 'sonner';

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
    const [scheduledEvents, setScheduledEvents] = useState<any[]>([]);

    // Map initialTab (e.g. 'queued') to index? Or use Tab.Group controlled?
    // Let's use controlled index.
    const tabs = ['scheduled', 'queued', 'processing', 'completed', 'failed'];
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
            // Fetch ingestion files
            const res = await fetch(`${API_BASE}/ingest/files`);
            if (res.ok) {
                const data = await res.json();
                setFiles(data);
            }
            // Fetch scheduled events
            const schedRes = await fetch(`${API_BASE}/scheduler/list`);
            if (schedRes.ok) {
                const schedData = await schedRes.json();
                setScheduledEvents(schedData || []);
            }
        } catch (e) {
            console.error("Failed to fetch files details", e);
        }
        setLoading(false);
    };

    const handleDelete = async (filename: string, status: string) => {
        try {
            const res = await fetch(`${API_BASE}/ingest/files/${encodeURIComponent(filename)}?status=${status}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                toast.success(`Removido: ${filename}`);
                fetchFiles(); // Refresh list
            } else {
                const error = await res.json();
                toast.error(error.detail || 'Erro ao remover');
            }
        } catch (e) {
            toast.error('Erro de conexão');
        }
    };

    const handleReprocess = async (filename: string) => {
        try {
            const res = await fetch(`${API_BASE}/ingest/files/${encodeURIComponent(filename)}/reprocess`, {
                method: 'POST'
            });
            if (res.ok) {
                toast.success(`Reenviado para fila: ${filename}`);
                fetchFiles(); // Refresh list
            } else {
                const error = await res.json();
                toast.error(error.detail || 'Erro ao reprocessar');
            }
        } catch (e) {
            toast.error('Erro de conexão');
        }
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
            case 'scheduled': return CalendarIcon;
            case 'queued': return ClockIcon;
            case 'processing': return CubeTransparentIcon;
            case 'completed': return CheckCircleIcon;
            case 'failed': return ExclamationTriangleIcon;
            default: return DocumentIcon;
        }
    };

    const getColor = (type: string) => {
        switch (type) {
            case 'scheduled': return 'text-synapse-purple bg-synapse-purple/10 border-synapse-purple/20';
            case 'queued': return 'text-synapse-amber bg-synapse-amber/10 border-synapse-amber/20';
            case 'processing': return 'text-synapse-cyan bg-synapse-cyan/10 border-synapse-cyan/20';
            case 'completed': return 'text-synapse-emerald bg-synapse-emerald/10 border-synapse-emerald/20';
            case 'failed': return 'text-red-500 bg-red-500/10 border-red-500/20';
            default: return 'text-gray-400 bg-gray-800 border-gray-700';
        }
    };

    const handleDeleteEvent = async (eventId: string) => {
        try {
            const res = await fetch(`${API_BASE}/scheduler/${eventId}`, { method: 'DELETE' });
            if (res.ok) {
                toast.success('Evento removido');
                fetchFiles();
            } else {
                toast.error('Erro ao remover evento');
            }
        } catch (e) {
            toast.error('Erro de conexão');
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
                                    <span>Detalhes do Pipeline</span>
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
                                            {tab} ({tab === 'scheduled' ? scheduledEvents.length : (files[tab]?.length || 0)})
                                        </Tab>
                                    ))}
                                </Tab.List>
                                <Tab.Panels className="flex-1 overflow-y-auto p-6 bg-grid-pattern">
                                    {tabs.map((tab) => {
                                        const Icon = getIcon(tab);
                                        const colorClass = getColor(tab);

                                        // Renderização especial para tab 'scheduled'
                                        if (tab === 'scheduled') {
                                            return (
                                                <Tab.Panel key={tab} className="space-y-3 focus:outline-none">
                                                    {loading ? (
                                                        <div className="text-center py-10 text-gray-500 animate-pulse">Carregando dados...</div>
                                                    ) : scheduledEvents.length === 0 ? (
                                                        <div className="flex flex-col items-center justify-center py-12 text-gray-500 border border-dashed border-white/10 rounded-xl">
                                                            <CalendarIcon className="w-12 h-12 mb-3 opacity-20" />
                                                            <p>Nenhum evento agendado</p>
                                                        </div>
                                                    ) : (
                                                        scheduledEvents.map((event: any, idx: number) => (
                                                            <div key={idx} className="flex items-center justify-between p-4 rounded-lg bg-black/40 border border-white/5 hover:border-white/10 transition-colors group">
                                                                <div className="flex items-center gap-4">
                                                                    <div className={clsx("w-10 h-10 rounded-lg flex items-center justify-center", colorClass)}>
                                                                        <CalendarIcon className="w-5 h-5" />
                                                                    </div>
                                                                    <div>
                                                                        <h4 className="text-white font-mono text-sm break-all">{event.video_path || event.id}</h4>
                                                                        <p className="text-xs text-gray-500 flex items-center gap-2 mt-1">
                                                                            <span className="text-synapse-purple">{event.profile_id}</span>
                                                                            <span className="w-1 h-1 rounded-full bg-gray-700" />
                                                                            <span>{format(new Date(event.scheduled_time), 'PP pp')}</span>
                                                                            {event.status && (
                                                                                <>
                                                                                    <span className="w-1 h-1 rounded-full bg-gray-700" />
                                                                                    <span className="text-synapse-amber uppercase text-[10px]">{event.status}</span>
                                                                                </>
                                                                            )}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <button
                                                                        onClick={() => handleDeleteEvent(event.id)}
                                                                        className="p-2 rounded-lg bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white transition-all"
                                                                        title="Remover"
                                                                    >
                                                                        <TrashIcon className="w-4 h-4" />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        ))
                                                    )}
                                                </Tab.Panel>
                                            );
                                        }

                                        // Renderização normal para outros tabs
                                        const currentFiles = files[tab] || [];
                                        return (
                                            <Tab.Panel key={tab} className="space-y-3 focus:outline-none">
                                                {loading ? (
                                                    <div className="text-center py-10 text-gray-500 animate-pulse">Carregando dados...</div>
                                                ) : currentFiles.length === 0 ? (
                                                    <div className="flex flex-col items-center justify-center py-12 text-gray-500 border border-dashed border-white/10 rounded-xl">
                                                        <Icon className="w-12 h-12 mb-3 opacity-20" />
                                                        <p>Nenhum arquivo em {tab === 'queued' ? 'fila' : tab === 'processing' ? 'processamento' : tab === 'completed' ? 'concluído' : 'falha'}</p>
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
                                                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                {/* Botões de Ação */}
                                                                {tab === 'failed' && (
                                                                    <button
                                                                        onClick={() => handleReprocess(file.name)}
                                                                        className="p-2 rounded-lg bg-synapse-amber/10 text-synapse-amber border border-synapse-amber/20 hover:bg-synapse-amber hover:text-black transition-all"
                                                                        title="Reprocessar"
                                                                    >
                                                                        <ArrowPathIcon className="w-4 h-4" />
                                                                    </button>
                                                                )}
                                                                {tab === 'queued' && (
                                                                    <button
                                                                        onClick={() => toast.info(`Processando ${file.name} agora...`)}
                                                                        className="p-2 rounded-lg bg-synapse-emerald/10 text-synapse-emerald border border-synapse-emerald/20 hover:bg-synapse-emerald hover:text-black transition-all"
                                                                        title="Processar Agora"
                                                                    >
                                                                        <PlayIcon className="w-4 h-4" />
                                                                    </button>
                                                                )}
                                                                <button
                                                                    onClick={() => toast.info(`Caminho: ${file.path}`)}
                                                                    className="p-2 rounded-lg bg-synapse-cyan/10 text-synapse-cyan border border-synapse-cyan/20 hover:bg-synapse-cyan hover:text-black transition-all"
                                                                    title="Ver Detalhes"
                                                                >
                                                                    <EyeIcon className="w-4 h-4" />
                                                                </button>
                                                                {(tab === 'queued' || tab === 'failed') && (
                                                                    <button
                                                                        onClick={() => handleDelete(file.name, tab)}
                                                                        className="p-2 rounded-lg bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white transition-all"
                                                                        title="Remover"
                                                                    >
                                                                        <TrashIcon className="w-4 h-4" />
                                                                    </button>
                                                                )}
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
