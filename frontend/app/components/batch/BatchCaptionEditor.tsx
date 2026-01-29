import React, { useState, useEffect, useRef } from 'react';
import { useBatch } from './BatchContext';
import { X, Sparkles, Loader2, ChevronUpIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { NeonButton } from '../NeonButton';
import { PromptTemplateSelector } from './PromptTemplateSelector';
import clsx from 'clsx';
import { toast } from 'sonner';

export function BatchCaptionEditor() {
    const { files, editingFileId, setEditingFileId, updateFileMetadata, selectedProfiles, profiles } = useBatch();
    const file = files.find(f => f.id === editingFileId);

    // Local state for editing
    const [prompt, setPrompt] = useState('');
    const [generatedText, setGeneratedText] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [tone, setTone] = useState<string>('Viral'); // Default tone
    const [length, setLength] = useState<string>('short'); // short, medium
    const [hashtags, setHashtags] = useState(true);
    const [model, setModel] = useState<string>('llama-3.3-70b-versatile');
    const [isModelOpen, setIsModelOpen] = useState(false);

    // Vision Link
    const [analyzeVideo, setAnalyzeVideo] = useState(true);

    const modelDropdownRef = useRef<HTMLDivElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);

    // Close model dropdown on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (modelDropdownRef.current && !modelDropdownRef.current.contains(event.target as Node)) {
                setIsModelOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const models = [
        { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 (70B) - Smart' },
        { id: 'meta-llama/llama-4-scout-17b-16e-instruct', name: 'Llama 4 Scout (17B) - Preview ⚡' },
        { id: 'qwen/qwen3-32b', name: 'Qwen 3 (32B) - Asian Expert' },
        { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 (8B) - Fast' },
        { id: 'openai/gpt-oss-120b', name: 'GPT OSS (120B)' },
    ];

    // Load initial data when file opens
    useEffect(() => {
        if (file) {
            setGeneratedText(file.metadata?.caption || '');
            setPrompt(file.metadata?.aiRequest?.prompt || '');
            setTone(file.metadata?.aiRequest?.tone || 'Viral');
        }
    }, [file]);

    if (!file) return null;

    // --- Vision Logic: Burst Mode ---
    const captureBurstFrames = async (video: HTMLVideoElement): Promise<string[]> => {
        const frames: string[] = [];
        const canvas = document.createElement('canvas');

        // Safety Check: Ensure video has loaded metadata
        if (video.readyState < 1) { // 1 = HAVE_METADATA
            console.log("Vision: Waiting for video metadata...");
            try {
                await new Promise<void>((resolve, reject) => {
                    // Success listener
                    const onLoaded = () => {
                        cleanup();
                        resolve();
                    };

                    // Timeout logic (10s max wait)
                    const timeoutId = setTimeout(() => {
                        cleanup();
                        reject(new Error("Timeout waiting for video metadata"));
                    }, 10000);

                    // Cleanup helper
                    const cleanup = () => {
                        video.removeEventListener('loadedmetadata', onLoaded);
                        clearTimeout(timeoutId);
                    };

                    video.addEventListener('loadedmetadata', onLoaded);
                });
            } catch (e) {
                console.warn("Vision: Could not load metadata in time. Proceeding cautiously.");
            }
        }

        const duration = Number.isFinite(video.duration) ? video.duration : 0;
        if (duration <= 0) {
            console.warn("Vision: Metadata check failed after timeout. Skipping visual analysis.");
            return []; // Fail gracefully, don't crash
        }

        // 3 Windows: Start (0-5s), Middle (Center +/- 2.5s), End (Last 5s)
        const windows = [
            { start: 0, end: Math.min(5, duration) },
            { start: Math.max(0, (duration / 2) - 2.5), end: Math.min(duration, (duration / 2) + 2.5) },
            { start: Math.max(0, duration - 5), end: duration }
        ];

        // Capture 6 frames per window = 18 frames total
        const framesPerWindow = 6;

        for (const win of windows) {
            const step = (win.end - win.start) / (framesPerWindow + 1);
            for (let i = 1; i <= framesPerWindow; i++) {
                const time = win.start + (step * i);

                // Seek
                video.currentTime = time;
                await new Promise(r => setTimeout(r, 200)); // Wait for seek

                // Draw (Downscaled for API performance)
                canvas.width = 480; // Standard vision scale
                canvas.height = (480 / video.videoWidth) * video.videoHeight;
                canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height);

                // Compress JPEG
                frames.push(canvas.toDataURL('image/jpeg', 0.7));
            }
        }
        return frames;
    };

    const handleGenerate = async () => {
        setIsGenerating(true);
        try {
            // 1. Vision Analysis (if enabled)
            let visualFrames: string[] = [];
            if (analyzeVideo && videoRef.current) {
                try {
                    visualFrames = await captureBurstFrames(videoRef.current);
                    toast.info(`Analisando ${visualFrames.length} frames do vídeo... 👁️`);
                } catch (e) {
                    console.error("Frame capture failed", e);
                    toast.warning("Falha ao capturar frames. Usando apenas texto.");
                }
            }

            // 2. Identify Niche Context
            // Resolve IDs to Profiles 
            const activeProfiles = profiles.filter(p => selectedProfiles.includes(p.id));
            const nicheContext = activeProfiles.length > 0
                ? activeProfiles.map(p => p.niche || p.label).join(", ")
                : "General Content Creator";

            // 3. API Call
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${API_URL}/api/v1/oracle/generate_caption`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    instruction: prompt,
                    tone: tone,
                    length: length,
                    video_context: file.file.name,
                    include_hashtags: hashtags,
                    output_type: 'caption',
                    model: model,
                    visual_frames: visualFrames, // Send frames!
                    niche_context: nicheContext, // [SYN-50] Niche Awareness
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Failed to generate");
            }

            const data = await res.json();
            setGeneratedText(data.caption);
            toast.success("Legenda Mágica criada! ✨");

        } catch (error: any) {
            console.error(error);
            toast.error(`Erro: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = () => {
        updateFileMetadata(file.id, {
            caption: generatedText,
            aiRequest: {
                prompt,
                tone,
                hashtags
            }
        });
        setEditingFileId(null);
    };

    return (
        <div className="absolute inset-0 z-[100] bg-[#0c0c0c]/95 backdrop-blur-xl flex animate-in fade-in duration-200">
            {/* Close Button */}
            <button
                onClick={() => setEditingFileId(null)}
                className="absolute top-6 right-6 p-2 rounded-full bg-black/50 hover:bg-white/10 text-gray-400 hover:text-white transition-colors z-[60]"
            >
                <X className="w-6 h-6" />
            </button>

            {/* Left: Preview */}
            <div className="w-1/3 h-full p-8 flex flex-col items-center justify-center border-r border-white/5 bg-black/20">
                <div className="relative aspect-[9/16] h-full max-h-[600px] rounded-2xl overflow-hidden shadow-2xl border border-white/10 group">
                    {/* Video Player - With Ref for Capture */}
                    <video
                        ref={videoRef}
                        src={file.preview}
                        className="w-full h-full object-cover"
                        controls
                        crossOrigin="anonymous" // Important for canvas
                        autoPlay
                        loop
                        muted
                    />

                    {/* Caption Overlay Preview */}
                    <div className="absolute bottom-12 left-4 right-4 text-center pointer-events-none">
                        <p className="text-white text-sm font-bold drop-shadow-md bg-black/50 p-2 rounded-lg inline-block backdrop-blur-sm">
                            {generatedText || "Sua legenda aparecerá aqui..."}
                        </p>
                    </div>
                </div>
                <p className="mt-4 text-xs text-gray-500 font-mono text-center">
                    Preview: {file.file.name}
                </p>
            </div>

            {/* Right: Controls (Scrollable + Sticky Footer Layout) */}
            <div className="flex-1 h-full flex flex-col bg-[#0c0c0c]/50 relative overflow-hidden">

                {/* Scrollable Content Area */}
                <div className="flex-1 overflow-y-auto px-12 py-8 custom-scrollbar pb-32">
                    <div className="max-w-3xl mx-auto space-y-8">

                        {/* Header & Vision Toggle */}
                        <div className="flex justify-between items-start">
                            <div>
                                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                    <Sparkles className="w-6 h-6 text-synapse-purple" />
                                    AI Caption Studio
                                </h2>
                                <p className="text-gray-400 mt-1">Otimize suas legendas para o algoritmo.</p>
                            </div>

                            {/* Vision Toggle */}
                            <button
                                onClick={() => setAnalyzeVideo(!analyzeVideo)}
                                className={clsx(
                                    "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold border transition-all",
                                    analyzeVideo
                                        ? "bg-synapse-purple/20 border-synapse-purple text-white shadow-[0_0_15px_rgba(139,92,246,0.3)]"
                                        : "bg-white/5 border-white/10 text-gray-500 hover:bg-white/10"
                                )}
                            >
                                <span className={analyzeVideo ? "animate-pulse" : ""}>👁️</span>
                                {analyzeVideo ? "Vision Ativado" : "Vision Desativado"}
                            </button>
                        </div>

                        {/* AI Input Area */}
                        <div className="space-y-6">
                            {/* Prompt Input */}
                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Instrução para IA</label>

                                    {/* Premium Template Selector */}
                                    <PromptTemplateSelector
                                        onSelect={(content) => setPrompt(content)}
                                        currentPrompt={prompt}
                                    />
                                </div>
                                <div className="relative">
                                    <textarea
                                        value={prompt}
                                        onChange={(e) => setPrompt(e.target.value)}
                                        placeholder="Opcional: Dê uma direção específica (ou deixe vazio para usar apenas os parâmetros)..."
                                        className="w-full h-24 bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white focus:ring-1 focus:ring-synapse-purple focus:border-synapse-purple outline-none resize-none transition-all placeholder:text-gray-600"
                                    />
                                    <div className="absolute bottom-3 right-3 flex gap-2">
                                        <button className="text-[10px] text-gray-500 hover:text-white bg-black/40 px-2 py-1 rounded-md border border-white/5">
                                            + Emojis
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Controls (Pills) */}
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Parâmetros</label>
                                <div className="flex flex-wrap gap-3">
                                    {['Viral', 'Polêmico', 'Engraçado', 'Profissional'].map(t => (
                                        <button
                                            key={t}
                                            onClick={() => setTone(t)}
                                            className={clsx(
                                                "px-4 py-2 rounded-full text-xs font-medium transition-all border",
                                                tone === t
                                                    ? "bg-synapse-purple/20 border-synapse-purple text-white shadow-[0_0_10px_rgba(139,92,246,0.2)]"
                                                    : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20"
                                            )}
                                        >
                                            {t}
                                        </button>
                                    ))}

                                    {/* Model Selector */}
                                    <div className="relative" ref={modelDropdownRef}>
                                        <button
                                            onClick={() => setIsModelOpen(!isModelOpen)}
                                            className={clsx(
                                                "px-4 py-2 rounded-full text-xs font-medium transition-all border flex items-center gap-2",
                                                isModelOpen
                                                    ? "bg-white/10 border-white/30 text-white"
                                                    : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20"
                                            )}
                                        >
                                            <span className="text-gray-500">Model:</span>
                                            <span className="text-white">{models.find(m => m.id === model)?.name}</span>
                                            <ChevronUpIcon className={clsx("w-3 h-3 transition-transform", isModelOpen ? "rotate-180" : "")} />
                                        </button>

                                        {/* Dropdown */}
                                        <AnimatePresence>
                                            {isModelOpen && (
                                                <motion.div
                                                    initial={{ opacity: 0, y: 4, scale: 0.95 }}
                                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                                    exit={{ opacity: 0, y: 4, scale: 0.95 }}
                                                    className="absolute bottom-full left-0 mb-2 w-56 bg-[#1a1a1a] border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
                                                >
                                                    <div className="p-1">
                                                        {models.map(m => (
                                                            <button
                                                                key={m.id}
                                                                onClick={() => {
                                                                    setModel(m.id);
                                                                    setIsModelOpen(false);
                                                                }}
                                                                className={clsx(
                                                                    "w-full text-left px-3 py-2 text-xs rounded-lg transition-colors flex items-center justify-between group",
                                                                    model === m.id ? "bg-synapse-purple/10 text-synapse-purple font-bold" : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                                                                )}
                                                            >
                                                                <span>{m.name}</span>
                                                                {model === m.id && <div className="w-1.5 h-1.5 rounded-full bg-synapse-purple shadow-[0_0_5px_rgba(139,92,246,0.5)]" />}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>

                                    <button
                                        onClick={() => setHashtags(!hashtags)}
                                        className={clsx(
                                            "px-4 py-2 rounded-full text-xs font-medium transition-all border",
                                            hashtags
                                                ? "bg-cyan-500/20 border-cyan-500 text-cyan-400"
                                                : "bg-white/5 border-white/10 text-gray-400"
                                        )}
                                    >
                                        # Hashtags
                                    </button>
                                </div>
                            </div>

                            {/* Generate Button */}
                            <NeonButton
                                onClick={handleGenerate}
                                disabled={isGenerating}
                                variant="primary"
                                className="w-full py-3 flex items-center justify-center gap-2 text-sm font-bold uppercase tracking-wider shadow-lg shadow-synapse-purple/20 hover:shadow-synapse-purple/40"
                            >
                                {isGenerating ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        {analyzeVideo ? "👀 Analisando Frames & Criando..." : "Criando Legenda Viral..."}
                                    </span>
                                ) : (
                                    <span className="flex items-center justify-center gap-2">
                                        <Sparkles className="w-4 h-4" />
                                        Regenerar Legenda Mágica
                                    </span>
                                )}
                            </NeonButton>

                            <div className="w-full h-px bg-white/5 my-4" />

                            {/* Result Area */}
                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Resultado Final</label>
                                    <span className="text-[10px] text-gray-600">{generatedText.length} chars</span>
                                </div>
                                <textarea
                                    value={generatedText}
                                    onChange={(e) => setGeneratedText(e.target.value)}
                                    className="w-full h-32 bg-black/40 border border-white/10 rounded-xl p-4 text-sm text-white focus:border-white/30 outline-none resize-none font-sans leading-relaxed"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer Actions (Sticky) */}
                <div className="p-6 border-t border-white/5 bg-[#0c0c0c] z-[70] flex justify-end gap-3 absolute bottom-0 w-full left-0 right-0 shadow-[0_-20px_40px_rgba(0,0,0,0.5)]">
                    <button
                        onClick={() => setEditingFileId(null)}
                        className="px-6 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-8 py-2 bg-white text-black font-bold rounded-full hover:bg-gray-200 transition-colors shadow-lg shadow-white/10"
                    >
                        Salvar Alterações
                    </button>
                </div>
            </div>
        </div>
    );
}
