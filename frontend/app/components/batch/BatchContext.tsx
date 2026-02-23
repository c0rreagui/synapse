import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { TikTokProfile as Profile } from '@/app/types';
import { toast } from 'sonner';
import { getApiUrl } from '../../utils/apiClient';
import { format } from 'date-fns';

// Types
export interface FileUpload {
    file?: File; // Optional for remote files
    filename: string; // Unified name
    preview: string;
    duration: number;
    status: 'pending' | 'uploading' | 'done' | 'error';
    isRemote?: boolean; // New flag for pre-existing files
    progress: number;
    id: string;
    metadata?: {
        caption?: string;
        aiRequest?: {
            prompt?: string;
            tone?: string;
            hashtags?: boolean;
        }
    };
}

export type ScheduleStrategy = 'INTERVAL' | 'ORACLE' | 'QUEUE' | 'CUSTOM' | 'AUTO_SCHEDULE';

interface BatchContextType {
    // State
    files: FileUpload[];
    setFiles: React.Dispatch<React.SetStateAction<FileUpload[]>>;
    selectedProfiles: string[];
    setSelectedProfiles: React.Dispatch<React.SetStateAction<string[]>>;
    profiles: Profile[];

    // Strategy & Time
    startDate: string;
    setStartDate: (date: string) => void;
    startTime: string;
    setStartTime: (time: string) => void;
    strategy: ScheduleStrategy;
    setStrategy: (s: ScheduleStrategy) => void;
    intervalMinutes: number;
    setIntervalMinutes: (n: number) => void;
    customTimes: string[];
    setCustomTimes: React.Dispatch<React.SetStateAction<string[]>>;

    // Intelligence
    viralBoost: boolean;
    setViralBoost: (b: boolean) => void;
    mixViralSounds: boolean;
    setMixViralSounds: (b: boolean) => void;
    aiCaptions: boolean;
    bypassConflicts: boolean;
    setBypassConflicts: (b: boolean) => void;

    privacyLevel: string;
    setPrivacyLevel: (p: string) => void;

    // Actions
    handleUpload: () => Promise<void>;
    isValidating: boolean;
    isUploading: boolean;
    validationResult: any;

    // Editor State
    editingFileId: string | null;
    setEditingFileId: (id: string | null) => void;
    updateFileMetadata: (id: string, metadata: any) => void;

    // [SYN-UX] Selection & Filtering
    selectedFileIds: string[];
    setSelectedFileIds: React.Dispatch<React.SetStateAction<string[]>>;
    viewFilter: 'all' | 'pending';
    setViewFilter: React.Dispatch<React.SetStateAction<'all' | 'pending'>>;

    // [SYN-UX] Automation
    isGeneratingAll: boolean;
    setIsGeneratingAll: React.Dispatch<React.SetStateAction<boolean>>;
    generateProgress: { current: number; total: number; statusMessage?: string } | null;
    setGenerateProgress: React.Dispatch<React.SetStateAction<{ current: number; total: number; statusMessage?: string } | null>>;

    // [SYN-67] Auto-Schedule (Studio Native)
    postsPerDay: number;
    setPostsPerDay: (n: number) => void;
    scheduleHours: number[];           // Ex: [12, 18] - horarios exatos
    setScheduleHours: (hours: number[]) => void;
    handleAutoSchedule: () => Promise<void>;
}

export const BatchContext = createContext<BatchContextType | undefined>(undefined);

export interface InitialFilePreload {
    filename: string;
    url?: string;
    caption?: string;
    profileId?: string;
    isRemote: true;
}

interface BatchProviderProps {
    children: ReactNode;
    existingProfiles: Profile[];
    initialFiles?: File[];
    initialPreload?: InitialFilePreload[]; // New Prop
    initialDate?: Date; // [SYN-FIX] Accept initial date for calendar context
    onClose: () => void;
    onSuccess: () => void;
}

export function BatchProvider({ children, existingProfiles, initialFiles = [], initialPreload = [], initialDate, onClose, onSuccess }: BatchProviderProps) {
    // --- State ---
    const [files, setFiles] = useState<FileUpload[]>([]);

    // Load initial files on mount
    useEffect(() => {
        let newFiles: FileUpload[] = [];

        // 1. Handle Local Files (Drag n Drop)
        if (initialFiles.length > 0) {
            newFiles = [...newFiles, ...initialFiles.map(file => ({
                file,
                filename: file.name,
                preview: URL.createObjectURL(file),
                duration: 0,
                status: 'pending' as const,
                progress: 0,
                id: Math.random().toString(36).substr(2, 9)
            }))];
        }

        // 2. Handle Remote Files (Approval Queue / Edit Mode)
        if (initialPreload.length > 0) {
            newFiles = [...newFiles, ...initialPreload.map(preload => ({
                filename: preload.filename,
                preview: preload.url || '', // Should ideally be a thumbnail URL
                duration: 0,
                status: 'done' as const, // Already on server
                progress: 100,
                id: Math.random().toString(36).substr(2, 9),
                isRemote: true,
                metadata: {
                    caption: preload.caption
                }
            }))];

            // Auto-select profile if provided in preload AND exists in known profiles
            if (initialPreload[0]?.profileId) {
                const targetId = initialPreload[0].profileId;
                const isValidProfile = existingProfiles.some(p => p.id === targetId);

                if (isValidProfile) {
                    setSelectedProfiles([targetId]);
                } else {
                    // [SYN-FIX] If ID is phantom (e.g. ptiktok_...), do NOT select it. 
                    // Fallback to first available real profile or empty.
                    console.warn(`[BatchContext] Ignored phantom profile ID: ${targetId}`);
                    if (existingProfiles.length > 0) {
                        setSelectedProfiles([existingProfiles[0].id]);
                    }
                }
            }
            // Auto-open editor if single file
            if (initialPreload.length === 1) {
                // We need to wait for state to settle, but we can set editingFileId in next tick
                setTimeout(() => setEditingFileId(newFiles[0].id), 100);
            }
        }

        if (newFiles.length > 0) {
            setFiles(newFiles);
        }
    }, [initialFiles, initialPreload, existingProfiles]);
    const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);

    // Time Defaults
    const now = new Date();
    now.setMinutes(now.getMinutes() + 30);
    const defaultDate = now.toISOString().split('T')[0];
    const defaultTime = now.toTimeString().slice(0, 5); // HH:MM

    // [SYN-FIX] Use initialDate if provided (e.g. from Calendar click)
    const initDateStr = initialDate ? format(initialDate, 'yyyy-MM-dd') : defaultDate;
    // Keep default time logic (now + 30) unless we want to enforce time too. 
    // Usually calendar click is just for the Day.

    const [startDate, setStartDate] = useState(initDateStr);
    const [startTime, setStartTime] = useState(defaultTime);
    const [strategy, setStrategy] = useState<ScheduleStrategy>('INTERVAL');
    const [intervalMinutes, setIntervalMinutes] = useState(60);
    const [customTimes, setCustomTimes] = useState<string[]>([]); // [SYN-CUSTOM]

    // Features
    const [viralBoost, setViralBoost] = useState(false);
    const [mixViralSounds, setMixViralSounds] = useState(false);
    const [isValidating, setIsValidating] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [bypassConflicts, setBypassConflicts] = useState(false);
    const [privacyLevel, setPrivacyLevel] = useState('public'); // 'public' | 'private'
    const [validationResult, setValidationResult] = useState<any>(null);
    const [editingFileId, setEditingFileId] = useState<string | null>(null);

    // [SYN-UX] Selection & Filtering
    const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
    const [viewFilter, setViewFilter] = useState<'all' | 'pending'>('all');

    // [SYN-UX] Automation
    const [isGeneratingAll, setIsGeneratingAll] = useState(false);
    const [generateProgress, setGenerateProgress] = useState<{ current: number; total: number; statusMessage?: string } | null>(null);

    // [SYN-67] Auto-Schedule
    const [postsPerDay, setPostsPerDay] = useState(1);
    const [scheduleHours, setScheduleHours] = useState<number[]>([18]);

    // --- Logic ---

    const updateFileMetadata = (id: string, metadata: any) => {
        setFiles(prev => prev.map(f => {
            if (f.id === id) {
                return { ...f, metadata: { ...f.metadata, ...metadata } };
            }
            return f;
        }));
    };

    const validateBatch = async () => {
        // Handle both local (File object) and remote (filename only)
        const filePaths = files.map(f => f.isRemote ? f.filename : `C:\\Videos\\${f.filename}`);
        const startDateTime = new Date(`${startDate}T${startTime}`);

        // [SYN-FIX] Send Local ISO string (no 'Z') to ensure Backend treats it as Local Time (Sao Paulo)
        // toISOString() converts to UTC (e.g. 15:00 -> 18:00Z), which creates offset confusion.
        // We want 15:00 Input -> 15:00 Saved.
        const startIsoLocal = format(startDateTime, "yyyy-MM-dd'T'HH:mm:ss");

        const payload = {
            files: filePaths,
            profile_ids: selectedProfiles,
            strategy: strategy,
            start_time: startIsoLocal,
            interval_minutes: intervalMinutes,
            custom_times: customTimes, // [SYN-CUSTOM]
            dry_run: true
        };

        const API_URL = getApiUrl();
        const res = await fetch(`${API_URL}/api/v1/scheduler/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        return res.json();
    };

    const handleUpload = async () => {
        if (files.length === 0 || selectedProfiles.length === 0) return;

        // 1. Upload Phase
        setIsUploading(true);
        const uploadedPaths: string[] = [];

        try {
            // Upload each file sequentially (or parallelLimit if needed)
            for (let i = 0; i < files.length; i++) {
                const fileObj = files[i];

                // Skip if already done (future proofing) or Remote
                if (fileObj.status === 'done' || fileObj.isRemote) {
                    uploadedPaths.push(fileObj.filename); // stored name
                    continue;
                }

                // Update status to uploading
                setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'uploading', progress: 0 } : f));

                const formData = new FormData();
                if (fileObj.file) {
                    formData.append("file", fileObj.file);
                } else {
                    // Should not happen if logic is correct
                    continue;
                }
                // Use first profile for "owner" tag, though batch is multi-profile. 
                formData.append("profile_id", selectedProfiles[0] || "batch_upload");
                // [SYN-FIX] Pass privacy_level to Ingestion
                formData.append("privacy_level", privacyLevel || "public_to_everyone");

                try {
                    const API_URL = getApiUrl();
                    const uploadRes = await fetch(`${API_URL}/api/v1/ingest/upload`, {
                        method: 'POST',
                        body: formData
                    });

                    if (!uploadRes.ok) throw new Error(`Failed to upload ${fileObj.filename}`);

                    const data = await uploadRes.json();
                    const serverFilename = data.filename; // Real filename from server
                    uploadedPaths.push(serverFilename);

                    // Update status to done
                    setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'done', progress: 100 } : f));

                } catch (e) {
                    console.error(e);
                    setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'error' } : f));
                    toast.error(`Falha ao enviar ${fileObj.filename}`);
                    setIsUploading(false); // Stop chain
                    return;
                }
            }
        } catch (e) {
            toast.error("Erro fatal no upload");
            setIsUploading(false);
            return;
        }

        // --- QUEUE ONLY MODE ---
        // If strategy is QUEUE, we stop here. Use the uploads as "done".
        if (strategy === 'QUEUE') {
            toast.success(`🚀 ${files.length} vídeos enviados para a fila!`);
            onSuccess();
            onClose();
            setFiles([]);
            setSelectedProfiles([]);
            setIsUploading(false);
            return;
        }

        setIsValidating(true);
        try {
            // 2. Validation Phase (using REAL paths now)
            // Note: serverFilename usually is just the basename in 'inputs' or 'pending'.
            // The scheduler expects absolute paths? Or relative?
            // The backend 'upload' puts files in 'inputs'. 
            // The legacy 'C:\Videos' verification implies the backend might expect absolute paths.
            // Let's assume the backend 'scheduler/batch' can handle filenames if they are in a known location,
            // OR we need to construct the path. 
            // Based on 'run_backend.py' searching 'inputs', let's guess the path structure or fix backend.
            // For now, let's send what the upload returned, but usually it returns just filename.
            // Let's prepend the likely backend path if needed, but safer to let backend resolve.
            // However, the previous mock was `C:\Videos\name`.

            // Let's check `scheduler.py` or similar if I could.
            // But strict "upload then validation" flow:

            // [SYN-FIX] Send Local ISO string (no 'Z')
            const startDateTime = new Date(`${startDate}T${startTime}`);
            const startIsoLocal = format(startDateTime, "yyyy-MM-dd'T'HH:mm:ss");

            const payloadStub = {
                files: uploadedPaths, // Validated filenames on server
                profile_ids: selectedProfiles,
                strategy,
                start_time: startIsoLocal,
                interval_minutes: intervalMinutes,
                custom_times: customTimes, // [SYN-CUSTOM]
                dry_run: true
            };

            const API_URL = getApiUrl();
            const valRes = await fetch(`${API_URL}/api/v1/scheduler/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payloadStub)
            });
            const validation = await valRes.json();

            // ... (Validation Logic from before) ...
            if (validation.detail) {
                toast.error(`Erro no sistema: ${validation.detail}`);
                setIsValidating(false);
                setIsUploading(false);
                return;
            }

            const issues: any[] = [];
            const validationData = validation.validation || {};
            Object.values(validationData).forEach((v: any) => {
                if (v.issues) v.issues.forEach((issue: any) => { if (issue.severity === 'error') issues.push(issue); });
            });
            setValidationResult({ canProceed: validation.can_proceed, issues });

            if (validation.can_proceed === false) {
                const errCount = validation.summary?.errors || 0;
                if (errCount > 0 && !bypassConflicts) {
                    toast.error(`❌ ${errCount} conflitos detectados. Ative 'Ignorar Conflitos' para prosseguir.`);
                    setIsValidating(false);
                    setIsUploading(false);
                    return;
                }
            }

            // 3. Final Execution Phase
            // [SYN-FIX] Build file metadata map for captions
            const fileMetadata: Record<string, any> = {};
            uploadedPaths.forEach((path, idx) => {
                fileMetadata[path] = {
                    caption: files[idx]?.metadata?.caption // Extract manual caption if present
                };
            });

            const finalPayload = {
                ...payloadStub,
                dry_run: false,
                force: bypassConflicts,
                viral_music_enabled: viralBoost,
                mix_viral_sounds: viralBoost && mixViralSounds,
                smart_captions: true,
                privacy_level: privacyLevel,
                file_metadata: fileMetadata
            };

            const res = await fetch(`${API_URL}/api/v1/scheduler/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(finalPayload)
            });

            if (!res.ok) throw new Error("Batch scheduling failed");

            toast.success(`🚀 ${files.length} vídeos agendados!`);
            onSuccess();
            onClose();
            setFiles([]);
            setSelectedProfiles([]);
            setValidationResult(null);

        } catch (error) {
            console.error("Batch error", error);
            toast.error("Falha ao agendar batch");
        } finally {
            setIsValidating(false);
            setIsUploading(false);
        }
    };

    // [SYN-67] Auto-Schedule Handler
    const handleAutoSchedule = async () => {
        if (files.length === 0 || selectedProfiles.length === 0) return;
        if (selectedProfiles.length > 1) {
            toast.error('Auto-Agendar suporta apenas 1 perfil por vez.');
            return;
        }

        setIsUploading(true);
        const fileMetaList: Array<{ path: string; caption: string; hashtags: string[] }> = [];

        try {
            for (let i = 0; i < files.length; i++) {
                const fileObj = files[i];
                if (fileObj.status === 'done' || fileObj.isRemote) {
                    fileMetaList.push({ path: fileObj.filename, caption: fileObj.metadata?.caption || '', hashtags: [] });
                    continue;
                }
                setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'uploading', progress: 0 } : f));
                const formData = new FormData();
                if (!fileObj.file) continue;
                formData.append('file', fileObj.file);
                formData.append('profile_id', selectedProfiles[0]);
                formData.append('privacy_level', privacyLevel || 'public_to_everyone');
                const API_URL = getApiUrl();
                const uploadRes = await fetch(`${API_URL}/api/v1/ingest/upload`, { method: 'POST', body: formData });
                if (!uploadRes.ok) throw new Error(`Falha ao enviar ${fileObj.filename}`);
                const data = await uploadRes.json();
                fileMetaList.push({ path: data.filename, caption: fileObj.metadata?.caption || '', hashtags: [] });
                setFiles(prev => prev.map(f => f.id === fileObj.id ? { ...f, status: 'done', progress: 100 } : f));
            }

            const API_URL = getApiUrl();
            const res = await fetch(`${API_URL}/api/v1/auto-scheduler/queue`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile_slug: selectedProfiles[0],
                    videos: fileMetaList.map(m => ({ path: m.path, caption: m.caption, hashtags: m.hashtags, privacy_level: privacyLevel || 'public_to_everyone' })),
                    posts_per_day: postsPerDay,
                    schedule_hours: scheduleHours.slice(0, postsPerDay),
                    auto_schedule_first_batch: true
                })
            });

            if (!res.ok) throw new Error('Falha ao criar fila de agendamento');
            const result = await res.json();
            toast.success(`${result.total_queued} videos adicionados a fila! Primeiros 10 sendo agendados...`);
            onSuccess();
            onClose();
            setFiles([]);
            setSelectedProfiles([]);
        } catch (e: any) {
            console.error('AutoSchedule error', e);
            toast.error(e.message || 'Falha no auto-agendamento');
        } finally {
            setIsUploading(false);
        }
    };

    const value = {
        files, setFiles,
        selectedProfiles, setSelectedProfiles,
        profiles: existingProfiles,
        startDate, setStartDate,
        startTime, setStartTime,
        strategy, setStrategy,
        intervalMinutes, setIntervalMinutes,
        customTimes, setCustomTimes, // [SYN-CUSTOM]
        viralBoost, setViralBoost,
        mixViralSounds, setMixViralSounds,
        aiCaptions: true,
        bypassConflicts, setBypassConflicts,
        privacyLevel, setPrivacyLevel,
        handleUpload,
        isValidating,
        isUploading,
        validationResult,
        editingFileId, setEditingFileId,
        updateFileMetadata,
        selectedFileIds, setSelectedFileIds,
        viewFilter, setViewFilter,
        isGeneratingAll, setIsGeneratingAll,
        generateProgress, setGenerateProgress,
        postsPerDay, setPostsPerDay,
        scheduleHours, setScheduleHours,
        handleAutoSchedule,
    };

    return (
        <BatchContext.Provider value={value}>
            {children}
        </BatchContext.Provider>
    );
}

export function useBatch() {
    const context = useContext(BatchContext);
    if (context === undefined) {
        throw new Error('useBatch must be used within a BatchProvider');
    }
    return context;
}
