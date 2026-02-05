import React, { useRef } from 'react';
import { useBatch } from './BatchContext';
import { PromptTemplateSelector } from './PromptTemplateSelector';
import { useDropzone } from 'react-dropzone';
import { Music, Sparkles, X, Play, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import clsx from 'clsx';

export function BatchMain() {
    const {
        files, setFiles,
        viralBoost, setViralBoost,
        mixViralSounds, setMixViralSounds,
        aiCaptions,
        setEditingFileId,
        privacyLevel, setPrivacyLevel,
        // [SYN-UX] New Context
        selectedFileIds, setSelectedFileIds,
        viewFilter, setViewFilter,
        updateFileMetadata,
        isGeneratingAll, setIsGeneratingAll,
        generateProgress, setGenerateProgress
    } = useBatch();

    // [SYN-UX] AI Parameters State
    const [showAiSettings, setShowAiSettings] = React.useState(false);
    const [prompt, setPrompt] = React.useState("");
    const [selectedTones, setSelectedTones] = React.useState<string[]>(["Viral"]);
    const [model, setModel] = React.useState("llama-3.3-70b-versatile");
    const [length, setLength] = React.useState("short");

    // [SYN-UX] Filter Logic
    const filteredFiles = files.filter(f => {
        if (viewFilter === 'pending') {
            return !f.metadata?.caption; // Only show those missing captions
        }
        return true;
    });

    // [SYN-UX] Selection Helpers
    const toggleSelection = (id: string, multi: boolean, range: boolean) => {
        if (range && selectedFileIds.length > 0) {
            // Simple range logic: finds index of last selected and current
            const lastId = selectedFileIds[selectedFileIds.length - 1];
            const currentIndex = files.findIndex(f => f.id === id);
            const lastIndex = files.findIndex(f => f.id === lastId);

            const start = Math.min(currentIndex, lastIndex);
            const end = Math.max(currentIndex, lastIndex);

            const rangeIds = files.slice(start, end + 1).map(f => f.id);
            // Union with existing
            setSelectedFileIds(prev => Array.from(new Set([...prev, ...rangeIds])));
        } else if (multi) {
            // Toggle
            setSelectedFileIds(prev =>
                prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
            );
        } else {
            // Exclusive
            setSelectedFileIds([id]);
        }
    };

    // [SYN-UX] Keyboard Shortcuts
    React.useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ignore if input/textarea is focused
            if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;

            if (e.key === 'a' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                setSelectedFileIds(files.map(f => f.id));
            } else if (e.key === 'Escape') {
                setSelectedFileIds([]);
            } else if (e.key === 'Delete' || e.key === 'Backspace') {
                if (selectedFileIds.length > 0) {
                    // Bulk Delete
                    setFiles(prev => prev.filter(f => !selectedFileIds.includes(f.id)));
                    setSelectedFileIds([]);
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [files, selectedFileIds]);

    // [SYN-UX] Automation Logic
    const captureFullVideoFrames = async (videoUrl: string): Promise<string[]> => {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            video.src = videoUrl;
            video.muted = true;
            video.crossOrigin = "anonymous"; // Safety

            const frames: string[] = [];

            video.onloadedmetadata = async () => {
                const duration = video.duration || 0;
                if (duration === 0) {
                    resolve([]);
                    return;
                }

                // Strategy: Capture 1 frame every 1.5 seconds
                let currentTime = 0;
                const interval = 1.5;

                const processFrame = async () => {
                    if (currentTime > duration) {
                        resolve(frames);
                        return;
                    }

                    video.currentTime = currentTime;
                    // We need to wait for 'seeked' but inside a loop it's tricky with events.
                    // simpler: await a poll check or just use a one-off event listener wrapper?
                    // Actually, the cleanest way is a recursive chain driven by 'seeked'.
                };

                const onSeeked = () => {
                    const canvas = document.createElement('canvas');
                    // Downscale for Vision API (standard is often ~512px)
                    const scale = 480 / video.videoWidth;
                    canvas.width = 480;
                    canvas.height = video.videoHeight * scale;

                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        frames.push(canvas.toDataURL('image/jpeg', 0.5)); // 50% quality
                    }

                    currentTime += interval;
                    if (currentTime <= duration) {
                        video.currentTime = currentTime;
                    } else {
                        resolve(frames);
                    }
                };

                video.onseeked = onSeeked;
                // Start
                video.currentTime = 0;
            };

            video.onerror = () => resolve([]);
        });
    };

    const generateAllPending = async () => {
        // Filter target files: Selected OR All Pending
        const targets = selectedFileIds.length > 0
            ? files.filter(f => selectedFileIds.includes(f.id) && !f.metadata?.caption)
            : files.filter(f => !f.metadata?.caption);

        if (targets.length === 0) {
            toast.info("Nenhum vídeo pendente para gerar.");
            return;
        }

        setIsGeneratingAll(true);
        setGenerateProgress({ current: 0, total: targets.length, statusMessage: "Iniciando..." });

        for (let i = 0; i < targets.length; i++) {
            const file = targets[i];
            const currentStep = i + 1;

            try {
                // 1. Vision Capture (Full Video)
                setGenerateProgress({
                    current: currentStep,
                    total: targets.length,
                    statusMessage: `👁️ Analisando vídeo: ${file.filename}`
                });

                const visualFrames = await captureFullVideoFrames(file.preview);

                // 2. Define API URL
                const API_URL = (typeof window !== 'undefined' && window.location.hostname === 'localhost')
                    ? 'http://127.0.0.1:8000'
                    : (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000');

                // 2. Audio Transcription (Hearing)
                let transcript = "";
                if (file.file) {
                    try {
                        setGenerateProgress({
                            current: currentStep,
                            total: targets.length,
                            statusMessage: `👂 Ouvindo áudio: ${file.filename}`
                        });

                        const formData = new FormData();
                        formData.append("file", file.file);

                        const tRes = await fetch(`${API_URL}/api/v1/oracle/transcribe`, {
                            method: "POST",
                            body: formData
                        });

                        if (tRes.ok) {
                            const tData = await tRes.json();
                            transcript = tData.text || "";
                        }
                    } catch (e) {
                        console.warn(`[Audio] Transcription failed for ${file.filename}`, e);
                    }
                }

                setGenerateProgress({
                    current: currentStep,
                    total: targets.length,
                    statusMessage: `🧠 Gerando legenda: ${file.filename}`
                });

                // 3. API Call (Vision + Hearing + Mind)     
                const res = await fetch(`${API_URL}/api/v1/oracle/generate_caption`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        instruction: prompt || "Analise o vídeo completo quadro a quadro. Identifique a narrativa visual, o texto na tela, as reações e o contexto exato para criar uma legenda perfeita.",
                        tone: selectedTones,
                        length: length,
                        video_context: file.filename,
                        include_hashtags: true,
                        output_type: 'caption',
                        model: model, // User selected model
                        visual_frames: visualFrames,
                        niche_context: "Auto-Detected (Full Video Scan)",
                        transcript: transcript // [SYN-AUDIO] Pass transcript
                    })
                });

                if (res.ok) {
                    const data = await res.json();
                    updateFileMetadata(file.id, {
                        caption: data.caption,
                        aiRequest: {
                            prompt: prompt || "Auto-Generated (Full Vision)",
                            tone: selectedTones,
                            model: model,
                            length: length
                        }
                    });
                } else {
                    console.error("API Error", res.status);
                    // Don't toast per file on error to avoid spam, just log
                }

            } catch (e) {
                console.error(`Failed to generate for ${file.filename}`, e);
            }
        }

        setIsGeneratingAll(false);
        setGenerateProgress(null);
        toast.success("Geração Inteligente concluída! 🧠✨");
    };

    const onDrop = (acceptedFiles: File[]) => {
        const newFiles = acceptedFiles.map(file => ({
            file,
            filename: file.name,
            preview: URL.createObjectURL(file), // Basic preview
            duration: 0, // Placeholder
            status: 'pending' as const,
            progress: 0,
            id: Math.random().toString(36).substr(2, 9)
        }));
        setFiles(prev => [...prev, ...newFiles]);
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'video/*': ['.mp4', '.mov', '.avi'] },
        multiple: true
    });

    const removeFile = (id: string) => {
        setFiles(prev => prev.filter(f => f.id !== id));
    };

    return (
        <div className="flex-1 h-full bg-[#0a0a0a]/50 flex flex-col relative">
            {/* [SYN-UX] Global Progress Bar */}
            {isGeneratingAll && generateProgress && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-gray-800 z-50">
                    <div
                        className="h-full bg-gradient-to-r from-synapse-purple to-cyan-400 transition-all duration-300"
                        style={{ width: `${(generateProgress.current / generateProgress.total) * 100}%` }}
                    />
                    <div className="absolute top-2 right-4 bg-black/80 backdrop-blur px-3 py-1 rounded-full border border-white/10 text-[10px] text-white font-mono shadow-xl flex items-center gap-2">
                        {generateProgress.statusMessage && (
                            <span className="text-gray-400 border-r border-white/10 pr-2 mr-1">
                                {generateProgress.statusMessage}
                            </span>
                        )}
                        <span>{generateProgress.current}/{generateProgress.total}</span>
                    </div>
                </div>
            )}

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-8">

                {/* 1. Intelligence Section (Opus Style "Feature Block") */}
                <div className="mb-8 p-1 rounded-2xl bg-gradient-to-r from-synapse-purple/20 to-cyan-500/20 p-[1px]">
                    <div className="bg-[#0f0a15] rounded-2xl p-5 backdrop-blur-xl">
                        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-4">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-synapse-purple to-cyan-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
                                    <Sparkles className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-sm font-bold text-white">Synapse Estúdio</h3>
                                    <p className="text-[11px] text-gray-400">Automação de conteúdo e otimização viral</p>
                                </div>
                            </div>

                            <div className="flex flex-wrap items-center gap-4">
                                {/* [SYN-UX] Generate All Button Group */}
                                <div className="flex bg-synapse-purple/20 border border-synapse-purple/50 rounded-lg shadow-[0_0_15px_rgba(139,92,246,0.2)]">
                                    <button
                                        onClick={generateAllPending}
                                        disabled={isGeneratingAll}
                                        className="flex items-center gap-2 px-4 py-1.5 text-white text-xs font-bold hover:bg-synapse-purple/30 transition-all border-r border-synapse-purple/30"
                                    >
                                        {isGeneratingAll ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                                        {isGeneratingAll ? "GERANDO..." : "GERAR MAGIA I.A."}
                                    </button>
                                    <button
                                        onClick={() => setShowAiSettings(!showAiSettings)}
                                        className="px-2 hover:bg-synapse-purple/30 transition-all flex items-center justify-center"
                                        title="Configurações de IA"
                                    >
                                        <div className={clsx("w-4 h-4 transition-transform duration-300", showAiSettings ? "rotate-90" : "rotate-0")}>
                                            ⚙️
                                        </div>
                                    </button>
                                </div>

                                <div className="w-px h-4 bg-white/10" />

                                {/* [SYN-UX] Filter Toggle */}
                                <div className="flex bg-white/5 p-1 rounded-lg border border-white/5">
                                    <button
                                        onClick={() => setViewFilter('all')}
                                        className={clsx(
                                            "px-3 py-1 rounded-md text-[10px] font-bold transition-all",
                                            viewFilter === 'all' ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300"
                                        )}
                                    >
                                        TODOS ({files.length})
                                    </button>
                                    <button
                                        onClick={() => setViewFilter('pending')}
                                        className={clsx(
                                            "px-3 py-1 rounded-md text-[10px] font-bold transition-all flex items-center gap-2",
                                            viewFilter === 'pending' ? "bg-amber-500/20 text-amber-400 border border-amber-500/20" : "text-gray-500 hover:text-gray-300"
                                        )}
                                    >
                                        PENDENTES ({files.filter(f => !f.metadata?.caption).length})
                                        {files.some(f => !f.metadata?.caption) && <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />}
                                    </button>
                                </div>

                                <div className="flex items-center gap-4">
                                    {/* Privacy Toggle */}
                                    <div className="flex items-center gap-2 cursor-pointer group" onClick={() => setPrivacyLevel(privacyLevel === 'public' ? 'private' : 'public')}>
                                        <span className="text-[11px] font-mono text-gray-400 group-hover:text-white transition-colors">
                                            {privacyLevel === 'public' ? 'PÚBLICO' : 'PRIVADO'}
                                        </span>
                                        <div className={clsx(
                                            "w-10 h-6 rounded-full p-1 transition-colors",
                                            privacyLevel === 'public' ? "bg-cyan-500" : "bg-red-500/50"
                                        )}>
                                            <div className={clsx(
                                                "w-4 h-4 rounded-full bg-white shadow-sm transition-transform",
                                                privacyLevel === 'public' ? "translate-x-4" : "translate-x-0"
                                            )} />
                                        </div>
                                    </div>

                                    <div className="w-px h-4 bg-white/10" />

                                    {/* Viral Boost */}
                                    <label className="flex items-center gap-2 cursor-pointer group">
                                        <span className="text-[11px] font-mono text-gray-400 group-hover:text-white transition-colors">VIRAL BOOST</span>
                                        <div className={clsx(
                                            "w-10 h-6 rounded-full p-1 transition-colors",
                                            viralBoost ? "bg-purple-600 shadow-[0_0_10px_rgba(147,51,234,0.5)]" : "bg-gray-700"
                                        )} onClick={() => setViralBoost(!viralBoost)}>
                                            <div className={clsx(
                                                "w-4 h-4 rounded-full bg-white shadow-sm transition-transform",
                                                viralBoost ? "translate-x-4" : "translate-x-0"
                                            )} />
                                        </div>
                                    </label>
                                </div>
                            </div>


                            {/* [SYN-UX] AI Parameters Panel */}
                            {showAiSettings && (
                                <div className="mt-4 pt-4 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-6 animate-in slide-in-from-top-2 duration-300">
                                    <div>
                                        <div className="flex items-center justify-between mb-2">
                                            <label className="text-[10px] uppercase font-bold text-gray-500">Prompt Personalizado (Opcional)</label>
                                            <PromptTemplateSelector currentPrompt={prompt} onSelect={setPrompt} />
                                        </div>
                                        <textarea
                                            value={prompt}
                                            onChange={(e) => setPrompt(e.target.value)}
                                            placeholder="Ex: Crie legendas engraçadas focando na reação dele..."
                                            className="w-full bg-black/30 border border-white/10 rounded-lg p-2 text-xs text-white placeholder-gray-600 focus:border-synapse-purple/50 focus:outline-none resize-none h-20"
                                        />
                                    </div>
                                    <div className="space-y-4">
                                        {/* Tones */}
                                        <div>
                                            <label className="text-[10px] uppercase font-bold text-gray-500 mb-2 block">Tom de Voz</label>
                                            <div className="flex flex-wrap gap-2">
                                                {["Viral", "Polêmico", "Engraçado", "Profissional", "Inspirador"].map(tone => (
                                                    <button
                                                        key={tone}
                                                        onClick={() => setSelectedTones(prev =>
                                                            prev.includes(tone) ? prev.filter(t => t !== tone) : [...prev, tone]
                                                        )}
                                                        className={clsx(
                                                            "px-3 py-1 rounded-full text-[10px] font-bold border transition-all",
                                                            selectedTones.includes(tone)
                                                                ? "bg-white text-black border-white"
                                                                : "bg-transparent text-gray-400 border-white/10 hover:border-white/30"
                                                        )}
                                                    >
                                                        {tone}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            {/* Model */}
                                            <div>
                                                <label className="text-[10px] uppercase font-bold text-gray-500 mb-2 block">Modelo IA</label>
                                                <select
                                                    value={model}
                                                    onChange={(e) => setModel(e.target.value)}
                                                    className="w-full bg-black/30 border border-white/10 rounded-lg p-1.5 text-xs text-white focus:border-synapse-purple/50 outline-none cursor-pointer"
                                                >
                                                    <option value="llama-3.3-70b-versatile">Llama 3.3 (70B) - Smart</option>
                                                    <option value="llama-3.2-11b-vision-preview">Llama 3.2 Vision (Fast)</option>
                                                    <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                                                </select>
                                            </div>
                                            {/* Length */}
                                            <div>
                                                <label className="text-[10px] uppercase font-bold text-gray-500 mb-2 block">Tamanho</label>
                                                <div className="flex bg-black/30 rounded-lg p-1 border border-white/10">
                                                    {[
                                                        { id: 'short', label: 'Curto ⚡' },
                                                        { id: 'medium', label: 'Story 📖' }
                                                    ].map(opt => (
                                                        <button
                                                            key={opt.id}
                                                            onClick={() => setLength(opt.id)}
                                                            className={clsx(
                                                                "flex-1 py-0.5 rounded text-[10px] font-bold transition-all",
                                                                length === opt.id ? "bg-white/10 text-white" : "text-gray-500 hover:text-gray-300"
                                                            )}
                                                        >
                                                            {opt.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Collapsible Options (Legacy/Compact) */}
                            {viralBoost && (
                                <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-white/5 animate-in slide-in-from-top-2 duration-300">
                                    {/* Mix Options */}
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                                                <Music className="w-4 h-4 text-cyan-400" />
                                            </div>
                                            <div>
                                                <p className="text-xs font-medium text-white">Mixar Trends</p>
                                                <p className="text-[10px] text-gray-500">Música única por vídeo</p>
                                            </div>
                                        </div>
                                        <input
                                            type="checkbox"
                                            checked={mixViralSounds}
                                            onChange={(e) => setMixViralSounds(e.target.checked)}
                                            className="accent-cyan-400 w-4 h-4 rounded-md cursor-pointer"
                                        />
                                    </div>

                                    {/* Smart Captions (Read Only / Indicator) */}
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between opacity-80">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                                <span className="text-xs font-black text-purple-400">AI</span>
                                            </div>
                                            <div>
                                                <p className="text-xs font-medium text-white">Smart Captions</p>
                                                <p className="text-[10px] text-gray-500">Gerado automaticamente</p>
                                            </div>
                                        </div>
                                        <div className="text-[10px] text-purple-400 font-mono font-bold px-2 py-1 rounded bg-purple-500/10 border border-purple-500/20">
                                            AUTO
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 2. Upload/Drop Area */}
                    {
                        files.length === 0 ? (
                            <div
                                {...getRootProps()}
                                className={clsx(
                                    "border-2 border-dashed rounded-3xl h-64 flex flex-col items-center justify-center cursor-pointer transition-all",
                                    isDragActive
                                        ? "border-synapse-purple bg-synapse-purple/10 scale-[0.99]"
                                        : "border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20"
                                )}
                            >
                                <input {...getInputProps()} />
                                <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center mb-4 shadow-xl">
                                    <span className="text-2xl">☁️</span>
                                </div>
                                <p className="text-sm font-medium text-white mb-2">Arraste seus vídeos aqui</p>
                                <p className="text-xs text-gray-500">MP4, MOV ou AVI</p>
                            </div>
                        ) : (
                            /* 3. Grid Gallery (Opus Style) */
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pb-20">
                                {/* Add More Button */}
                                <div
                                    {...getRootProps()}
                                    className="aspect-[9/16] rounded-xl border border-dashed border-white/20 bg-white/5 hover:bg-white/10 flex flex-col items-center justify-center cursor-pointer transition-colors group"
                                >
                                    <input {...getInputProps()} />
                                    <div className="w-8 h-8 rounded-full border border-white/30 flex items-center justify-center text-white mb-2 group-hover:scale-110 transition-transform">
                                        +
                                    </div>
                                    <span className="text-xs text-gray-400">Adicionar</span>
                                </div>

                                {filteredFiles.map((file, idx) => {
                                    const isSelected = selectedFileIds.includes(file.id);
                                    const hasCaption = !!file.metadata?.caption;

                                    return (
                                        <div
                                            key={file.id}
                                            onClick={(e) => {
                                                // If holding Ctrl/Shift, do selection logic
                                                if (e.ctrlKey || e.metaKey || e.shiftKey) {
                                                    e.stopPropagation();
                                                    toggleSelection(file.id, e.ctrlKey || e.metaKey, e.shiftKey);
                                                } else {
                                                    // Regular click = Edit
                                                    setEditingFileId(file.id);
                                                }
                                            }}
                                            className={clsx(
                                                "relative aspect-[9/16] bg-black rounded-xl overflow-hidden group border shadow-lg cursor-pointer transition-all",
                                                isSelected
                                                    ? "border-synapse-purple ring-2 ring-synapse-purple/50 scale-[0.98]"
                                                    : "border-white/10 hover:border-synapse-purple/50"
                                            )}
                                        >
                                            {/* Preview */}
                                            {file.preview ? (
                                                <video src={file.preview} className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity" />
                                            ) : (
                                                <div className="w-full h-full bg-gray-900" />
                                            )}

                                            {/* Overlay Info */}
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-3 flex flex-col justify-end">
                                                <p className="text-xs font-medium text-white line-clamp-2 leading-tight mb-1">{file.filename}</p>
                                                <p className="text-[10px] text-gray-500">
                                                    {file.file ? (file.file.size / 1024 / 1024).toFixed(1) + ' MB' : 'Remoto'}
                                                </p>
                                            </div>

                                            {/* Top Bar (Selection & Status) */}
                                            <div className="absolute top-2 left-2 flex flex-col gap-2 z-10 items-start">
                                                {/* Selection Checkbox & Index */}
                                                <div
                                                    onClick={(e) => { e.stopPropagation(); toggleSelection(file.id, true, false); }}
                                                    className={clsx(
                                                        "h-6 px-2 rounded-lg border backdrop-blur flex items-center justify-center text-[10px] font-bold transition-colors hover:bg-white/20 min-w-[24px]",
                                                        isSelected
                                                            ? "bg-synapse-purple border-synapse-purple text-white shadow-lg shadow-purple-500/40"
                                                            : "bg-black/50 border-white/10 text-white"
                                                    )}
                                                >
                                                    {isSelected ? <span className="text-white scale-125">✓</span> : (files.indexOf(file) + 1)}
                                                </div>

                                                {/* Status Badge */}
                                                <div className={clsx(
                                                    "px-2 py-1 rounded-md text-[9px] font-bold border backdrop-blur-md uppercase tracking-wider shadow-sm",
                                                    hasCaption
                                                        ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400"
                                                        : "bg-amber-500/20 border-amber-500/30 text-amber-400"
                                                )}>
                                                    {hasCaption ? "OK" : "PENDENTE"}
                                                </div>
                                            </div>

                                            {/* Remove Button */}
                                            <button
                                                onClick={(e) => { e.stopPropagation(); removeFile(file.id); }}
                                                className="absolute top-2 right-2 w-6 h-6 rounded-lg bg-red-500/20 hover:bg-red-500 text-red-500 hover:text-white flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                </div>
            </div>
        </div>
    );
}
