import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDownIcon, PlusIcon, PencilIcon, TrashIcon, CheckIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { PromptTemplate, templateService } from '../../../services/templateService';
import { toast } from 'sonner';
import clsx from 'clsx';
import { NeonButton } from '../NeonButton';

interface PromptTemplateSelectorProps {
    onSelect: (content: string) => void;
    currentPrompt?: string;
}

export function PromptTemplateSelector({ onSelect, currentPrompt }: PromptTemplateSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [templates, setTemplates] = useState<PromptTemplate[]>([]);
    const [search, setSearch] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [editingTemplate, setEditingTemplate] = useState<PromptTemplate | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Form inputs
    const [formName, setFormName] = useState('');
    const [formContent, setFormContent] = useState('');

    useEffect(() => {
        loadTemplates();

        // Click outside to close
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const loadTemplates = async () => {
        setIsLoading(true);
        try {
            const data = await templateService.list();
            setTemplates(data);
        } catch (error) {
            toast.error("Erro ao carregar templates");
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreate = async () => {
        if (!formName.trim() || !formContent.trim()) return toast.warning("Nome e conteúdo obrigatórios");
        try {
            await templateService.create({ name: formName, content: formContent, category: "General" });
            toast.success("Template criado!");
            setIsCreating(false);
            setFormName('');
            setFormContent('');
            loadTemplates();
        } catch (error) {
            toast.error("Erro ao criar template");
        }
    };

    const handleUpdate = async () => {
        if (!editingTemplate || !formName.trim() || !formContent.trim()) return;
        try {
            await templateService.update(editingTemplate.id, { name: formName, content: formContent });
            toast.success("Template atualizado!");
            setEditingTemplate(null);
            loadTemplates();
        } catch (error) {
            toast.error("Erro ao atualizar");
        }
    };

    const handleDelete = async (id: number, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!confirm("Tem certeza que deseja excluir?")) return;
        try {
            await templateService.delete(id);
            toast.success("Template removido");
            loadTemplates();
        } catch (error) {
            toast.error("Erro ao remover");
        }
    };

    const startEditing = (t: PromptTemplate, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingTemplate(t);
        setFormName(t.name);
        setFormContent(t.content);
        setIsCreating(false);
    };

    const startCreating = () => {
        setIsCreating(true);
        setEditingTemplate(null);
        setFormName('');
        // If there's text in the main prompt area, preload it
        if (currentPrompt) setFormContent(currentPrompt);
        else setFormContent('');
    };

    const filtered = templates.filter(t => t.name.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 bg-white/5 border border-white/10 hover:bg-white/10 px-3 py-1.5 rounded-lg text-xs text-gray-300 transition-all font-medium"
            >
                <span>📂 Templates</span>
                <ChevronDownIcon className={clsx("w-3 h-3 transition-transform", isOpen && "rotate-180")} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        className="absolute top-full right-0 mt-2 w-80 bg-[#1a1a1a] border border-white/10 rounded-xl shadow-2xl z-[100] backdrop-blur-xl overflow-hidden flex flex-col"
                    >
                        {/* Header / Search */}
                        {!isCreating && !editingTemplate && (
                            <div className="p-3 border-b border-white/5 space-y-2">
                                <div className="relative">
                                    <MagnifyingGlassIcon className="absolute left-2.5 top-2.5 w-4 h-4 text-gray-500" />
                                    <input
                                        type="text"
                                        placeholder="Buscar..."
                                        value={search}
                                        onChange={e => setSearch(e.target.value)}
                                        className="w-full bg-black/30 border border-white/5 rounded-lg pl-9 pr-3 py-2 text-xs text-white focus:border-synapse-purple/50 outline-none"
                                        autoFocus
                                    />
                                </div>
                                <button
                                    onClick={startCreating}
                                    className="w-full flex items-center justify-center gap-2 bg-synapse-purple/10 hover:bg-synapse-purple/20 text-synapse-purple text-xs py-2 rounded-lg transition-colors border border-synapse-purple/20"
                                >
                                    <PlusIcon className="w-3 h-3" />
                                    Novo Template
                                </button>
                            </div>
                        )}

                        {/* List */}
                        {!isCreating && !editingTemplate && (
                            <div className="max-h-60 overflow-y-auto p-1 custom-scrollbar">
                                {isLoading ? (
                                    <p className="text-center text-xs text-gray-500 py-4">Carregando...</p>
                                ) : filtered.length === 0 ? (
                                    <p className="text-center text-xs text-gray-500 py-4">Nenhum template encontrado.</p>
                                ) : (
                                    filtered.map(t => (
                                        <div
                                            key={t.id}
                                            onClick={() => { onSelect(t.content); setIsOpen(false); }}
                                            className="group flex items-center justify-between p-2 hover:bg-white/5 rounded-lg cursor-pointer transition-colors"
                                        >
                                            <div className="flex-1 min-w-0 pr-2">
                                                <p className="text-xs font-bold text-gray-300 group-hover:text-white truncate">{t.name}</p>
                                                <p className="text-[10px] text-gray-500 truncate">{t.content}</p>
                                            </div>
                                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={(e) => startEditing(t, e)}
                                                    className="p-1.5 hover:bg-blue-500/20 text-blue-400 rounded-md transition-colors"
                                                    title="Editar"
                                                >
                                                    <PencilIcon className="w-3 h-3" />
                                                </button>
                                                <button
                                                    onClick={(e) => handleDelete(t.id, e)}
                                                    className="p-1.5 hover:bg-red-500/20 text-red-400 rounded-md transition-colors"
                                                    title="Excluir"
                                                >
                                                    <TrashIcon className="w-3 h-3" />
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}

                        {/* Create / Edit Form */}
                        {(isCreating || editingTemplate) && (
                            <div className="p-4 space-y-3">
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="text-xs font-bold text-white uppercase">{isCreating ? 'Novo Template' : 'Editar Template'}</h4>
                                    <button onClick={() => { setIsCreating(false); setEditingTemplate(null); }} className="text-gray-500 hover:text-white text-xs">Cancelar</button>
                                </div>
                                <input
                                    type="text"
                                    placeholder="Nome do Template (ex: Viral Curto)"
                                    value={formName}
                                    onChange={e => setFormName(e.target.value)}
                                    className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:border-synapse-purple/50 outline-none"
                                />
                                <textarea
                                    placeholder="Instrução do prompt..."
                                    value={formContent}
                                    onChange={e => setFormContent(e.target.value)}
                                    className="w-full h-24 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:border-synapse-purple/50 outline-none resize-none"
                                />
                                <NeonButton
                                    onClick={isCreating ? handleCreate : handleUpdate}
                                    className="w-full justify-center text-xs py-2"
                                >
                                    {isCreating ? 'Salvar Novo' : 'Salvar Alterações'}
                                </NeonButton>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
