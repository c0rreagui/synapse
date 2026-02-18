import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getApiUrl } from '@/app/utils/apiClient';
import { TikTokProfile, ScheduleEvent } from '../types';

const API_BASE = getApiUrl() + '/api/v1';

export interface IngestionStatus {
    queued: number;
    processing: number;
    completed: number;
    failed: number;
}

export interface PendingVideo {
    id: string;
    filename: string;
    profile: string;
    uploaded_at: string;
    status: string;
    metadata: {
        caption?: string;
        original_filename?: string;
        profile_id?: string;
    };
}

async function fetchJson<T>(url: string): Promise<T> {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch ${url}`);
    return res.json();
}

export function useIngestionStatus() {
    return useQuery({
        queryKey: ['ingestion-status'],
        queryFn: () => fetchJson<IngestionStatus>(`${API_BASE}/ingest/status`),
        refetchInterval: 5000,
        retry: false, // Se backend cair, falha rápido
    });
}

export function usePendingVideos() {
    return useQuery({
        queryKey: ['pending-videos'],
        queryFn: () => fetchJson<PendingVideo[]>(`${API_BASE}/queue/pending`),
        refetchInterval: 5000,
    });
}

export function useProfiles() {
    return useQuery({
        queryKey: ['profiles-list'],
        queryFn: () => fetchJson<TikTokProfile[]>(`${API_BASE}/profiles/list`),
        staleTime: 1000 * 60 * 5, // 5 minutos de cache (perfis mudam pouco)
    });
}

export function useScheduledEvents() {
    return useQuery({
        queryKey: ['scheduled-events'],
        queryFn: () => fetchJson<ScheduleEvent[]>(`${API_BASE}/scheduler/list`),
        refetchInterval: 5000,
    });
}

export function useDashboardRefresh() {
    const queryClient = useQueryClient();
    return () => {
        queryClient.invalidateQueries({ queryKey: ['ingestion-status'] });
        queryClient.invalidateQueries({ queryKey: ['pending-videos'] });
        queryClient.invalidateQueries({ queryKey: ['profiles-list'] });
        queryClient.invalidateQueries({ queryKey: ['scheduled-events'] });
    };
}
