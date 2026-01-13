"use client";

import { useState, useEffect } from 'react';
import { ClockIcon, CalendarIcon, CheckIcon, XMarkIcon, ArrowPathIcon, SparklesIcon, FireIcon } from '@heroicons/react/24/outline';
import GlassCard from '../components/GlassCard';
import Toast from '../components/Toast';
import Badge from '../components/Badge';
import Spinner from '../components/Spinner';
import EmptyState from '../components/EmptyState';
import ConfirmDialog from '../components/ConfirmDialog';

interface PendingVideo {
    id: string;
    filename: string;
    profile: string;
    uploaded_at: string;
    status: string;
    metadata: {
        caption?: string;
        original_filename?: string;
        profile_id?: string;
        oracle_status?: 'pending' | 'completed' | 'failed';
        oracle_analysis?: {
            suggested_caption: string;
            hashtags: string[];
            viral_score: number;
            viral_reason: string;
        };
    };
}

export default function QueuePage() {
    const [pendingVideos, setPendingVideos] = useState<PendingVideo[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedVideo, setSelectedVideo] = useState<PendingVideo | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [postType, setPostType] = useState<'immediate' | 'scheduled'>('immediate');
    const [selectedDate, setSelectedDate] = useState('');
    const [selectedTime, setSelectedTime] = useState('12:00');
    const [submitting, setSubmitting] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
    const [confirmReject, setConfirmReject] = useState<string | null>(null);

    const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
        setToast({ message, type });
    };

    useEffect(() => {
        fetchPendingVideos();
    }, []);

    const fetchPendingVideos = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/queue/pending');
            const data = await response.json();
            setPendingVideos(data);
        } catch (error) {
            console.error('Error fetching pending videos:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = (video: PendingVideo) => {
        setSelectedVideo(video);
        setShowModal(true);
        // Set default date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        setSelectedDate(tomorrow.toISOString().split('T')[0]);
    };

    const handleReject = async (videoId: string) => {
        setConfirmReject(videoId);
    };

    const confirmRejectVideo = async () => {
        if (!confirmReject) return;
        try {
            await fetch(`http://localhost:8000/api/v1/queue/${confirmReject}`, {
                method: 'DELETE'
            });
            fetchPendingVideos();
            showToast('Vídeo rejeitado', 'info');
        } catch (error) {
            console.error('Error rejecting video:', error);
            showToast('Erro ao rejeitar vídeo', 'error');
        } finally {
            setConfirmReject(null);
        }
    };

    const handleConfirm = async () => {
        if (!selectedVideo) return;

        setSubmitting(true);

        try {
            const scheduleTime = postType === 'scheduled'
                ? `${selectedDate}T${selectedTime}:00`
                : null;

            const response = await fetch('http://localhost:8000/api/v1/queue/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: selectedVideo.id,
                    action: postType,
                    schedule_time: scheduleTime
                })
            });

            if (response.ok) {
                setShowModal(false);
                setSelectedVideo(null);
                fetchPendingVideos(); // Refresh list
                alert(postType === 'immediate'
                    ? 'Vídeo aprovado! Bot iniciando execução...'
                    : `Vídeo agendado para ${selectedDate} às ${selectedTime}`);
            } else {
                throw new Error('Falha na aprovação');
            }
        } catch (error) {
            console.error('Error approving video:', error);
            alert('Erro ao aprovar vídeo');
        } finally {
            setSubmitting(false);
        }
    };

    // Generate time options (5-min intervals)
    const timeOptions = [];
    for (let h = 0; h < 24; h++) {
        for (let m = 0; m < 60; m += 5) {
            const hour = h.toString().padStart(2, '0');
            const minute = m.toString().padStart(2, '0');
            timeOptions.push(`${hour}:${minute}`);
        }
    }

    return (
        <div className="p-6 space-y-6">
            {/* Toast Notification */}
            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}

            {/* Confirm Reject Dialog */}
            <ConfirmDialog
                isOpen={!!confirmReject}
                title="Rejeitar Vídeo"
                message="Tem certeza que deseja rejeitar este vídeo? Esta ação não pode ser desfeita."
                confirmLabel="Rejeitar"
                cancelLabel="Cancelar"
                variant="danger"
                onConfirm={confirmRejectVideo}
                onCancel={() => setConfirmReject(null)}
            />

            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-white">Fila de Aprovação</h1>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button
                        onClick={fetchPendingVideos}
                        title="Atualizar lista"
                        aria-label="Atualizar lista"
                        style={{ padding: '10px', borderRadius: '8px', backgroundColor: 'transparent', border: '1px solid #30363d', cursor: 'pointer' }}
                    >
                        <ArrowPathIcon style={{ width: '20px', height: '20px', color: '#8b949e' }} />
                    </button>
                    <Badge variant={pendingVideos.length > 0 ? 'warning' : 'success'} size="md">
                        {pendingVideos.length} Pendente{pendingVideos.length !== 1 ? 's' : ''}
                    </Badge>
                </div>
            </div>

            {loading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}>
                    <Spinner size="lg" />
                </div>
            ) : pendingVideos.length === 0 ? (
                <GlassCard>
                    <EmptyState
                        title="Nenhum vídeo pendente"
                        description="Todos os vídeos foram processados. Faça upload de novos vídeos para começar."
                        icon={<CheckIcon style={{ width: '48px', height: '48px', color: '#3fb950' }} />}
                        action={{ label: 'Ir para Upload', onClick: () => window.location.href = '/' }}
                    />
                </GlassCard>
            ) : (
                <div className="grid gap-4">
                    {pendingVideos.map((video) => (
                        <GlassCard key={video.id}>
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <h3 className="text-lg font-semibold text-white">
                                        {video.metadata.original_filename || video.filename}
                                    </h3>
                                    <p className="text-sm text-gray-400 mt-1">
                                        Perfil: {video.metadata.profile_id || video.profile}
                                    </p>
                                    {video.metadata.caption && (
                                        <p className="text-sm text-gray-300 mt-2 line-clamp-2">
                                            {video.metadata.caption}
                                        </p>
                                    )}

                                    {/* 🔮 ORACLE INSIGHTS BLOCK */}
                                    {video.metadata.oracle_status === 'pending' && (
                                        <div className="mt-3 flex items-center gap-2 text-xs text-synapse-cyan animate-pulse">
                                            <SparklesIcon className="w-4 h-4" />
                                            <span>Oracle AI analisando viralidade...</span>
                                        </div>
                                    )}

                                    {video.metadata.oracle_analysis && (
                                        <div className="mt-3 p-3 rounded-lg bg-synapse-cyan/5 border border-synapse-cyan/20">
                                            <div className="flex items-center gap-2 mb-2">
                                                <SparklesIcon className="w-4 h-4 text-synapse-cyan" />
                                                <span className="text-xs font-bold text-synapse-cyan uppercase tracking-wider">Oracle Insight</span>
                                                <div className="ml-auto flex items-center gap-1 text-xs text-orange-400 font-bold border border-orange-400/30 px-2 py-0.5 rounded-full">
                                                    <FireIcon className="w-3 h-3" />
                                                    {video.metadata.oracle_analysis.viral_score}/100
                                                </div>
                                            </div>

                                            {/* AI Caption */}
                                            <div className="text-sm text-white italic mb-2">
                                                "{video.metadata.oracle_analysis.suggested_caption}"
                                            </div>

                                            {/* Tags */}
                                            <div className="flex flex-wrap gap-1">
                                                {video.metadata.oracle_analysis.hashtags.slice(0, 5).map(tag => (
                                                    <span key={tag} className="text-[10px] text-gray-400 bg-white/5 px-1.5 py-0.5 rounded">
                                                        {tag}
                                                    </span>
                                                ))}
                                                {video.metadata.oracle_analysis.hashtags.length > 5 && (
                                                    <span className="text-[10px] text-gray-500 px-1.5 py-0.5">
                                                        +{video.metadata.oracle_analysis.hashtags.length - 5}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                                <div className="flex gap-3 ml-6">
                                    <button
                                        onClick={() => handleApprove(video)}
                                        className="px-6 py-3 bg-gradient-to-r from-synapse-cyan to-synapse-purple text-white font-semibold rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2"
                                    >
                                        <CheckIcon className="w-5 h-5" />
                                        Aprovar
                                    </button>
                                    <button
                                        onClick={() => handleReject(video.id)}
                                        className="px-6 py-3 bg-red-500/20 border border-red-500 text-red-400 font-semibold rounded-lg hover:bg-red-500/30 transition-colors flex items-center gap-2"
                                    >
                                        <XMarkIcon className="w-5 h-5" />
                                        Rejeitar
                                    </button>
                                </div>
                            </div>
                        </GlassCard>
                    ))}
                </div>
            )
            }

            {/* Approval Modal */}
            {
                showModal && selectedVideo && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="glass-panel max-w-lg w-full p-6 space-y-6">
                            <div>
                                <h2 className="text-2xl font-bold text-white">Aprovar Vídeo</h2>
                                <p className="text-gray-400 text-sm mt-1">
                                    {selectedVideo.metadata.original_filename}
                                </p>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-white font-semibold mb-3">
                                        Tipo de Postagem
                                    </label>
                                    <div className="flex gap-4">
                                        <button
                                            onClick={() => setPostType('immediate')}
                                            className={`flex-1 py-3 px-4 rounded-lg border-2 transition-all ${postType === 'immediate'
                                                ? 'border-synapse-cyan bg-synapse-cyan/20 text-synapse-cyan'
                                                : 'border-gray-600 text-gray-400 hover:border-gray-500'
                                                }`}
                                        >
                                            <span className="font-semibold">Post Imediato</span>
                                        </button>
                                        <button
                                            onClick={() => setPostType('scheduled')}
                                            className={`flex-1 py-3 px-4 rounded-lg border-2 transition-all ${postType === 'scheduled'
                                                ? 'border-synapse-purple bg-synapse-purple/20 text-synapse-purple'
                                                : 'border-gray-600 text-gray-400 hover:border-gray-500'
                                                }`}
                                        >
                                            <span className="font-semibold">Agendar</span>
                                        </button>
                                    </div>
                                </div>

                                {postType === 'scheduled' && (
                                    <div className="space-y-4 p-4 bg-white/5 rounded-lg border border-white/10">
                                        <div>
                                            <label className="block text-white font-semibold mb-2 flex items-center gap-2">
                                                <CalendarIcon className="w-5 h-5 text-synapse-purple" />
                                                Data
                                            </label>
                                            <input
                                                type="date"
                                                title="Selecionar data de agendamento"
                                                aria-label="Data de agendamento"
                                                value={selectedDate}
                                                onChange={(e) => setSelectedDate(e.target.value)}
                                                min={new Date().toISOString().split('T')[0]}
                                                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:border-synapse-purple focus:outline-none"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-white font-semibold mb-2 flex items-center gap-2">
                                                <ClockIcon className="w-5 h-5 text-synapse-cyan" />
                                                Horário (múltiplos de 5 minutos)
                                            </label>
                                            <select
                                                title="Selecionar horário de agendamento"
                                                aria-label="Horário de agendamento"
                                                value={selectedTime}
                                                onChange={(e) => setSelectedTime(e.target.value)}
                                                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:border-synapse-cyan focus:outline-none"
                                            >
                                                {timeOptions.map((time) => (
                                                    <option key={time} value={time} className="bg-gray-900">
                                                        {time}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={() => {
                                        setShowModal(false);
                                        setSelectedVideo(null);
                                    }}
                                    disabled={submitting}
                                    className="flex-1 px-6 py-3 bg-gray-700 text-white font-semibold rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
                                >
                                    Cancelar
                                </button>
                                <button
                                    onClick={handleConfirm}
                                    disabled={submitting || (postType === 'scheduled' && !selectedDate)}
                                    className="flex-1 px-6 py-3 bg-gradient-to-r from-synapse-cyan to-synapse-purple text-white font-semibold rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {submitting ? (
                                        <>Processando...</>
                                    ) : (
                                        <>
                                            <CheckIcon className="w-5 h-5" />
                                            Confirmar & Executar
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    );
}
