import React, { useState, useEffect, useRef } from 'react';
import { useBatch } from './BatchContext';
import { XMarkIcon, SparklesIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { NeonButton } from '../NeonButton';
import clsx from 'clsx';
import { toast } from 'sonner';

export function BatchCaptionEditor() {
    const { files, editingFileId, setEditingFileId, updateFileMetadata } = useBatch();
    const file = files.find(f => f.id === editingFileId);

    // Local state for editing
    const [prompt, setPrompt] = useState('');
    const [generatedText, setGeneratedText] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [tone, setTone] = useState<string>('Viral'); // Default tone
    const [length, setLength] = useState<string>('short'); // short, medium
    const [hashtags, setHashtags] = useState(true);
    const [savedPrompts, setSavedPrompts] = useState<string[]>([]);

    // Load saved prompts from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('synapse_saved_prompts');
        if (saved) {
            setSavedPrompts(JSON.parse(saved));
        }
    }, []);

    const savePromptTemplate = () => {
        if (!prompt.trim()) return;
        const newPrompts = [...savedPrompts, prompt.trim()];
        const uniquePrompts = Array.from(new Set(newPrompts)); // de-dupe
        setSavedPrompts(uniquePrompts);
        localStorage.setItem('synapse_saved_prompts', JSON.stringify(uniquePrompts));
        toast.success("Prompt salvo como template! 💾");
    };

    const deletePromptTemplate = (promptToDelete: string) => {
        const newPrompts = savedPrompts.filter(p => p !== promptToDelete);
        setSavedPrompts(newPrompts);
        localStorage.setItem('synapse_saved_prompts', JSON.stringify(newPrompts));
        toast.success("Template removido.");
    };

    // Load initial data when file opens
    useEffect(() => {
        if (file) {
            setGeneratedText(file.metadata?.caption || '');
            setPrompt(file.metadata?.aiRequest?.prompt || '');
            setTone(file.metadata?.aiRequest?.tone || 'Viral');
        }
    }, [file]);

    if (!file) return null;

    const handleGenerate = async () => {
        // [SYN-44] Generate Caption + Hashtags (Unified)
        setIsGenerating(true);
        try {
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
                    output_type: 'caption'
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
        <div className="absolute inset-0 z-50 bg-[#0c0c0c]/95 backdrop-blur-xl flex animate-in fade-in duration-200">
            {/* Close Button */}
            <button
                onClick={() => setEditingFileId(null)}
                className="absolute top-6 right-6 p-2 rounded-full bg-black/50 hover:bg-white/10 text-gray-400 hover:text-white transition-colors z-[60]"
            >
                <XMarkIcon className="w-6 h-6" />
            </button>

            {/* Left: Preview */}
            <div className="w-1/3 h-full p-8 flex flex-col items-center justify-center border-r border-white/5 bg-black/20">
                <div className="relative aspect-[9/16] h-full max-h-[600px] rounded-2xl overflow-hidden shadow-2xl border border-white/10 group">
                    {/* Video Player */}
                    <video
                        src={file.preview}
                        className="w-full h-full object-cover"
                        controls
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

            {/* Right: Controls */}
            <div className="flex-1 h-full p-12 flex flex-col max-w-3xl mx-auto justify-center">
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <SparklesIcon className="w-6 h-6 text-synapse-purple" />
                        AI Caption Studio
                    </h2>
                    <p className="text-gray-400 mt-1">Otimize suas legendas para o algoritmo.</p>
                </div>

                {/* AI Input Area */}
                <div className="space-y-6">
                    {/* Prompt Input */}
                    <div className="space-y-2">
                        <div className="flex justify-between items-center">
                            <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Instrução para IA</label>

                            {/* Templates Dropdown */}
                            {savedPrompts.length > 0 && (
                                <select
                                    onChange={(e) => {
                                        if (e.target.value) setPrompt(e.target.value);
                                    }}
                                    className="bg-white/5 border border-white/10 rounded-lg text-[10px] text-gray-400 px-2 py-1 outline-none hover:bg-white/10"
                                >
                                    <option value="">📂 Carregar Template...</option>
                                    {savedPrompts.map((p, i) => (
                                        <option key={i} value={p}>{p.substring(0, 30)}...</option>
                                    ))}
                                </select>
                            )}
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
                                {prompt.trim().length > 0 && (
                                    <button
                                        onClick={savePromptTemplate}
                                        className="text-[10px] text-synapse-purple hover:text-white bg-synapse-purple/10 hover:bg-synapse-purple/50 px-2 py-1 rounded-md border border-synapse-purple/20 transition-colors"
                                    >
                                        💾 Salvar Prompt
                                    </button>
                                )}
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
                            <>
                                <ArrowPathIcon className="w-4 h-4 animate-spin" />
                                Criando Legenda Viral...
                            </>
                        ) : (
                            <>
                                <SparklesIcon className="w-4 h-4" />
                                Regenerar Legenda Mágica
                            </>
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

                    {/* Save Button */}
                    <div className="flex justify-end gap-3 pt-4">
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
        </div>
    );
}
