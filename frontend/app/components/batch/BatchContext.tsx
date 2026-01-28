import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { TikTokProfile as Profile } from '@/app/types';
import { toast } from 'sonner';

// Types
export interface FileUpload {
    file: File;
    preview: string;
    duration: number;
    status: 'pending' | 'uploading' | 'done' | 'error';
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

export type ScheduleStrategy = 'INTERVAL' | 'ORACLE';

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

    // Intelligence
    viralBoost: boolean;
    setViralBoost: (b: boolean) => void;
    mixViralSounds: boolean;
    setMixViralSounds: (b: boolean) => void;
    aiCaptions: boolean;

    // Actions
    handleUpload: () => Promise<void>;
    isValidating: boolean;
    isUploading: boolean;
    validationResult: any;

    // Editor State
    editingFileId: string | null;
    setEditingFileId: (id: string | null) => void;
    updateFileMetadata: (id: string, metadata: any) => void;
}

export const BatchContext = createContext<BatchContextType | undefined>(undefined);

interface BatchProviderProps {
    children: ReactNode;
    existingProfiles: Profile[];
    initialFiles?: File[];
    onClose: () => void;
    onSuccess: () => void;
}

export function BatchProvider({ children, existingProfiles, initialFiles = [], onClose, onSuccess }: BatchProviderProps) {
    // --- State ---
    const [files, setFiles] = useState<FileUpload[]>([]);

    // Load initial files on mount
    useEffect(() => {
        if (initialFiles.length > 0) {
            const newFiles = initialFiles.map(file => ({
                file,
                preview: URL.createObjectURL(file),
                duration: 0,
                status: 'pending' as const,
                progress: 0,
                id: Math.random().toString(36).substr(2, 9)
            }));
            setFiles(newFiles);
        }
    }, [initialFiles]);
    const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);

    // Time Defaults
    const now = new Date();
    now.setMinutes(now.getMinutes() + 30);
    const defaultDate = now.toISOString().split('T')[0];
    const defaultTime = now.toTimeString().slice(0, 5); // HH:MM

    const [startDate, setStartDate] = useState(defaultDate);
    const [startTime, setStartTime] = useState(defaultTime);
    const [strategy, setStrategy] = useState<ScheduleStrategy>('INTERVAL');
    const [intervalMinutes, setIntervalMinutes] = useState(60);

    // Features
    const [viralBoost, setViralBoost] = useState(false);
    const [mixViralSounds, setMixViralSounds] = useState(false);
    const [isValidating, setIsValidating] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [validationResult, setValidationResult] = useState<any>(null);
    const [editingFileId, setEditingFileId] = useState<string | null>(null);

    // --- Logic ---

    const updateFileMetadata = (id: string, metadata: any) => {
        setFiles(prev => prev.map(f => {
            if (f.id === id) {
                return { ...f, metadata: { ...f.metadata, ...metadata } };
            }
            return f;
        }));
    };

    // 🧠 Validar batch com dry_run
    const validateBatch = async () => {
        const filePaths = files.map(f => `C:\\Videos\\${f.file.name}`); // Simulating path for now as per legacy logic
        const startDateTime = new Date(`${startDate}T${startTime}`);

        const payload = {
            files: filePaths,
            profile_ids: selectedProfiles,
            strategy: strategy,
            start_time: startDateTime.toISOString(),
            interval_minutes: intervalMinutes,
            dry_run: true
        };

        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${API_URL}/api/v1/scheduler/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        return res.json();
    };

    const handleUpload = async () => {
        if (files.length === 0 || selectedProfiles.length === 0) return;

        setIsValidating(true);
        try {
            // 1. Validation Phase
            const validation = await validateBatch();

            // [SYN-FIX] Check for backend execution error (e.g. 500)
            if (validation.detail) {
                toast.error(`Erro no sistema: ${validation.detail}`);
                setIsValidating(false);
                return;
            }

            // Store issues for UI
            const issues: any[] = [];
            const validationData = validation.validation || {};
            Object.values(validationData).forEach((v: any) => {
                if (v.issues) {
                    v.issues.forEach((issue: any) => {
                        if (issue.severity === 'error') {
                            issues.push(issue);
                        }
                    });
                }
            });

            setValidationResult({
                canProceed: validation.can_proceed,
                issues
            });

            // If explicitly blocked by logic and we have errors
            if (validation.can_proceed === false) {
                const errCount = validation.summary?.errors || 0;
                if (errCount > 0) {
                    toast.error(`❌ ${errCount} conflitos detectados`);
                    setIsValidating(false);
                    return;
                }
                // If can_proceed is false but 0 errors, it might be a logic glitch, but we proceed cautiously
                // or might be warnings only if backend logic changed. 
                // However, per backend, can_proceed=errors==0.
            }

            // 2. Execution Phase
            setIsUploading(true);
            const filePaths = files.map(f => `C:\\Videos\\${f.file.name}`);
            const startDateTime = new Date(`${startDate}T${startTime}`);

            const payload = {
                files: filePaths,
                profile_ids: selectedProfiles,
                strategy: strategy,
                start_time: startDateTime.toISOString(),
                interval_minutes: intervalMinutes,
                viral_music_enabled: viralBoost,
                mix_viral_sounds: viralBoost && mixViralSounds,
                smart_captions: true // Always true for batch
            };

            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_URL}/api/v1/scheduler/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Batch scheduling failed");

            toast.success(`🚀 ${files.length} vídeos agendados!`);
            onSuccess();
            onClose();

            // Reset
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

    const value = {
        files, setFiles,
        selectedProfiles, setSelectedProfiles,
        profiles: existingProfiles,
        startDate, setStartDate,
        startTime, setStartTime,
        strategy, setStrategy,
        intervalMinutes, setIntervalMinutes,
        viralBoost, setViralBoost,
        mixViralSounds, setMixViralSounds,
        aiCaptions: true,
        handleUpload,
        isValidating,
        isUploading,
        validationResult,
        editingFileId, setEditingFileId,
        updateFileMetadata
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
