import { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import { XMarkIcon, DocumentIcon, ClockIcon, ExclamationTriangleIcon, CheckCircleIcon, CubeTransparentIcon, ArrowPathIcon, TrashIcon, EyeIcon, PlayIcon, CalendarIcon, PencilIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
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
    onViewDetails?: (file: FileItem) => void;
}

import { apiClient } from '../lib/api';
import ConfirmDialog from './ConfirmDialog';

const API_BASE = '/api/v1';

export default function MetricsModal({ isOpen, onClose, initialTab = 'processing', onViewDetails }: MetricsModalProps) {
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
    const tabs = ['queued', 'processing', 'completed', 'failed'];
    const [selectedIndex, setSelectedIndex] = useState(tabs.indexOf(initialTab) !== -1 ? tabs.indexOf(initialTab) : 0);

    useEffect(() => {
        if (isOpen) {
            fetchFiles();
            const idx = tabs.indexOf(initialTab);
            if (idx !== -1) setSelectedIndex(idx);
        }
    }, [isOpen, initialTab]);

    const [deletingConfirm, setDeletingConfirm] = useState<{ id: string, type: string } | null>(null);

    const fetchFiles = async () => {
        setLoading(true);
        try {
            // Fetch ingestion files
            const filesData = await apiClient.get<Record<string, FileItem[]>>(`${API_BASE}/ingest/files`);
            setFiles(filesData);

            // Fetch scheduled events
            const schedData = await apiClient.get<any[]>(`${API_BASE}/scheduler/list`);
            setScheduledEvents(schedData || []);
        } catch (e) {
            console.error("Failed to fetch files details", e);
        }
        setLoading(false);
    };

    const handleDeleteClick = (filename: string, status: string) => {
        setDeletingConfirm({ id: filename, type: status });
    };

    const confirmDelete = async () => {
        if (!deletingConfirm) return;

        try {
            if (deletingConfirm.type === 'event') {
                await apiClient.delete(`${API_BASE}/scheduler/${deletingConfirm.id}`);
                toast.success('Evento removido');
            } else {
                await apiClient.delete(`${API_BASE}/ingest/files/${encodeURIComponent(deletingConfirm.id)}?status=${deletingConfirm.type}`);
                toast.success(`Removido: ${deletingConfirm.id}`);
            }
            fetchFiles(); // Refresh list
        } catch (e: any) {
            toast.error(e.message || 'Erro ao remover');
        } finally {
            setDeletingConfirm(null);
        }
    };

    const handleReprocess = async (filename: string) => {
        try {
            await apiClient.post(`${API_BASE}/ingest/files/${encodeURIComponent(filename)}/reprocess`, {});
            toast.success(`Reenviado para fila: ${filename}`);
            fetchFiles(); // Refresh list
        } catch (e: any) {
            toast.error(e.message || 'Erro ao reprocessar');
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

    const handleDeleteEventClick = (eventId: string) => {
        setDeletingConfirm({ id: eventId, type: 'event' });
    };

    const handleExportCSV = () => {
        const rows = ['Tipo,Nome/ID,Perfil,Tamanho,Status,Data'];

        scheduledEvents.forEach(event => {
            rows.push(`Agendado,${event.video_path || event.id},${event.profile_id},N/A,${event.status},${new Date(event.scheduled_time).toLocaleString('pt-BR')}`);
        });

        Object.entries(files).forEach(([status, items]) => {
            items.forEach((item: any) => {
                rows.push(`${status},${item.name},N/A,${formatSize(item.size)},${status},${new Date(item.modified).toLocaleString('pt-BR')}`);
            });
        });

        const csvContent = rows.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `synapse_telemetry_${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        toast.success('Telemetria exportada (CSV) com sucesso!');
    };

    return (
        <Transition show={isOpen} as={Fragment}>
            <Dialog onClose={onClose} className="relative z-50">
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-200"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-150"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
                </Transition.Child>

                <div className="fixed inset-0 flex items-center justify-center p-4">
                    <Transition.Child
                        as={Fragment}
                        enter="ease-[cubic-bezier(0.34,1.56,0.64,1)] duration-300"
                        enterFrom="opacity-0 scale-[0.92]"
                        enterTo="opacity-100 scale-100"
                        leave="ease-in duration-150"
                        leaveFrom="opacity-100 scale-100"
                        leaveTo="opacity-0 scale-[0.95]"
                    >
                        <Dialog.Panel className="relative w-full max-w-3xl rounded-[20px] overflow-hidden flex flex-col max-h-[80vh] bg-gradient-to-b from-[rgba(22,15,35,0.92)] to-[rgba(11,8,18,0.97)] backdrop-blur-[40px] saturate-[180%] border border-white/[0.08] shadow-[0_32px_64px_-12px_rgba(0,0,0,0.85),0_0_80px_rgba(139,92,246,0.05),inset_0_1px_0_rgba(255,255,255,0.07)]">
                            {/* Borda prismática */}
                            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent pointer-events-none z-10" />
                            {/* Header */}
                            <div className="flex items-center justify-between p-5 border-b border-white/[0.05]">
                                <Dialog.Title className="text-xl font-bold text-white flex items-center gap-2">
                                    <DocumentIcon className="w-6 h-6 text-synapse-primary" />
                                    <span>Detalhes do Pipeline</span>
                                </Dialog.Title>
                                <div className="flex items-center gap-4">
                                    <button onClick={handleExportCSV} className="text-gray-400 hover:text-synapse-cyan transition-colors group flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-white/10 hover:border-synapse-cyan/50" title="Exportar Telemetria (CSV)">
                                        <ArrowDownTrayIcon className="w-4 h-4" />
                                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider group-hover:text-synapse-cyan">Exportar CSV</span>
                                    </button>
                                    <div className="w-[1px] h-6 bg-white/10 hidden sm:block"></div>
                                    <button onClick={onClose} className="w-8 h-8 rounded-xl flex items-center justify-center bg-white/[0.04] hover:bg-white/[0.10] border border-white/[0.06] text-gray-400 hover:text-white transition-all duration-200">
                                        <XMarkIcon className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            <Tab.Group selectedIndex={selectedIndex} onChange={setSelectedIndex}>
                                <Tab.List className="flex space-x-1 bg-black/20 p-1 border-b border-white/5">
                                    {tabs.map((tab) => {
                                        const tabNames: Record<string, string> = {
                                            scheduled: 'Agendados',
                                            queued: 'Na Fila',
                                            processing: 'Processando',
                                            completed: 'Concluídos',
                                            failed: 'Falhas'
                                        };
                                        return (
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
                                                {tabNames[tab]} ({tab === 'scheduled' ? scheduledEvents.length : (files[tab]?.length || 0)})
                                            </Tab>
                                        )
                                    })}
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
                                                                        onClick={() => handleDeleteEventClick(event.id)}
                                                                        className="p-2 rounded-lg transition-all border bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500 hover:text-white"
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
                                                                    onClick={() => onViewDetails ? onViewDetails(file) : toast.info(`Caminho: ${file.path}`)}
                                                                    className="p-2 rounded-lg bg-synapse-cyan/10 text-synapse-cyan border border-synapse-cyan/20 hover:bg-synapse-cyan hover:text-black transition-all"
                                                                    title="Ver Detalhes"
                                                                >
                                                                    <EyeIcon className="w-4 h-4" />
                                                                </button>
                                                                {(tab === 'queued' || tab === 'failed') && (
                                                                    <button
                                                                        onClick={() => handleDeleteClick(file.name, tab)}
                                                                        className="p-2 rounded-lg transition-all border bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500 hover:text-white"
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
                <ConfirmDialog
                    isOpen={!!deletingConfirm}
                    title="Remover Item"
                    message={deletingConfirm?.type === 'event' ? "Tem certeza que deseja remover este evento?" : "Tem certeza que deseja remover este arquivo de métricas?"}
                    onConfirm={confirmDelete}
                    onCancel={() => setDeletingConfirm(null)}
                    variant="danger"
                    confirmLabel="Remover"
                    cancelLabel="Cancelar"
                />
            </Dialog>
        </Transition>
    );
}
