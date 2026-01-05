"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar } from "./components";

interface QueuedFile {
  id: number;
  filename: string;
  status: "enviando" | "processando" | "concluido" | "erro";
  size: string;
}

export default function IngestionPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState("p1");
  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  // Scheduling State
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduleTime, setScheduleTime] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const showToast = useCallback((message: string, type: "success" | "error") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  const uploadToFactory = useCallback(async (file: File, queueId: number) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('profile_id', selectedProfile);

    // Add schedule time if enabled
    if (isScheduled && scheduleTime) {
      formData.append('schedule_time', scheduleTime);
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/ingest/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        await response.json(); // Consuming the promise but ignoring the return value
        setQueue((prev) =>
          prev.map((f) =>
            f.id === queueId ? { ...f, status: "processando" } : f
          )
        );
        showToast(`✅ "${file.name}" enviado com sucesso!`, "success");

        setTimeout(() => {
          setQueue((prev) =>
            prev.map((f) => (f.id === queueId ? { ...f, status: "concluido" } : f))
          );
        }, 3000);
      } else {
        setQueue((prev) =>
          prev.map((f) => (f.id === queueId ? { ...f, status: "erro" } : f))
        );
        showToast(`❌ Erro ao enviar arquivo`, "error");
      }
    } catch (_) { // usage of _ to ignore unused var
      setQueue((prev) =>
        prev.map((f) => (f.id === queueId ? { ...f, status: "erro" } : f))
      );
      showToast(`❌ Erro de conexão`, "error");
    }
  }, [selectedProfile, isScheduled, scheduleTime, showToast]);

  const processFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);

    fileArray.forEach((file) => {
      if (!file.name.toLowerCase().endsWith('.mp4') &&
        !file.name.toLowerCase().endsWith('.mov') &&
        !file.name.toLowerCase().endsWith('.webm')) {
        showToast(`⚠️ Apenas vídeos são aceitos`, "error");
        return;
      }

      const queueId = Date.now() + Math.random();
      const newFile: QueuedFile = {
        id: queueId,
        filename: file.name,
        status: "enviando",
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      };

      setQueue((prev) => [newFile, ...prev]);
      uploadToFactory(file, queueId);
    });
  }, [uploadToFactory, showToast]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [processFiles]); // Correct dependency

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      processFiles(e.target.files);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const getStatusIcon = (status: QueuedFile["status"]) => {
    switch (status) {
      case "enviando": return "⏳";
      case "processando": return "🔄";
      case "concluido": return "✅";
      case "erro": return "❌";
    }
  };

  const getStatusText = (status: QueuedFile["status"]) => {
    switch (status) {
      case "enviando": return "Enviando...";
      case "processando": return "Processando";
      case "concluido": return "Concluído";
      case "erro": return "Erro";
    }
  };

  const getStatusColor = (status: QueuedFile["status"]) => {
    switch (status) {
      case "enviando": return "text-yellow-500 bg-yellow-500/10";
      case "processando": return "text-blue-500 bg-blue-500/10";
      case "concluido": return "text-green-500 bg-green-500/10";
      case "erro": return "text-red-500 bg-red-500/10";
    }
  };

  return (
    <main className="min-h-screen flex bg-background">
      <Sidebar />

      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header Simples */}
        <header className="h-16 flex items-center px-8 border-b border-white/10">
          <h1 className="text-2xl font-bold text-white">Fábrica de Conteúdo</h1>
        </header>

        {/* Conteúdo Principal */}
        <div className="flex-1 overflow-y-auto p-8">
          <div className="max-w-3xl mx-auto space-y-8">

            {/* Seletor de Perfil */}
            <div className="space-y-2">
              <label htmlFor="profile-selector" className="text-sm font-medium text-gray-400">
                Para qual conta vai esse vídeo?
              </label>
              <select
                id="profile-selector"
                value={selectedProfile}
                onChange={(e) => setSelectedProfile(e.target.value)}
                className="w-full md:w-64 px-4 py-3 bg-[#1a1a1f] border border-white/10 rounded-xl text-white text-base focus:outline-none focus:border-primary/50 cursor-pointer"
                title="Selecione o perfil"
              >
                <option value="p1">📱 Perfil 01 (Principal)</option>
                <option value="p2">📱 Perfil 02 (Secundário)</option>
              </select>
            </div>

            {/* Agendamento (Time Travel) */}
            <div className="p-4 bg-[#1a1a1f]/50 border border-white/5 rounded-xl space-y-3">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="scheduleToggle"
                  checked={isScheduled}
                  onChange={(e) => setIsScheduled(e.target.checked)}
                  className="w-5 h-5 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
                />
                <label htmlFor="scheduleToggle" className="text-white font-medium cursor-pointer select-none">
                  🗓️ Agendar Postagem? (Time Travel)
                </label>
              </div>

              {isScheduled && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="pt-2"
                >
                  <label htmlFor="schedule-time" className="block text-xs text-gray-500 mb-1">Data e Hora da Publicação</label>
                  <input
                    id="schedule-time"
                    type="datetime-local"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                    className="w-full md:w-64 px-4 py-2 bg-gray-900 border border-white/10 rounded-lg text-white focus:border-primary/50 focus:outline-none"
                    title="Data e hora do agendamento"
                  />
                </motion.div>
              )}
            </div>

            {/* Área de Upload - DESTAQUE PRINCIPAL */}
            <div
              onClick={handleClick}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`
                                relative rounded-2xl border-2 border-dashed p-12 
                                flex flex-col items-center justify-center min-h-[280px]
                                cursor-pointer transition-all duration-200
                                ${isDragging
                  ? "border-primary bg-primary/10 scale-[1.02]"
                  : "border-white/20 hover:border-primary/50 hover:bg-white/5"
                }
                            `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                multiple
                onChange={handleFileSelect}
                className="hidden"
                aria-label="Upload de vídeos"
                title="Upload de vídeos"
              />

              <div className={`text-6xl mb-4 transition-transform ${isDragging ? "scale-110" : ""}`}>
                {isDragging ? "📥" : "🎬"}
              </div>

              <h2 className="text-xl font-bold text-white mb-2">
                {isDragging ? "Solte o vídeo aqui!" : "Arraste seu Vídeo Aqui"}
              </h2>

              <p className="text-gray-400 text-sm">
                ou <span className="text-primary underline">clique para selecionar</span>
              </p>

              <div className="flex items-center gap-4 mt-6 text-xs text-gray-500">
                <span>MP4, MOV, WebM</span>
                <span>•</span>
                <span>Até 500MB</span>
              </div>
            </div>

            {/* Lista de Vídeos na Fila */}
            {queue.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  📋 Vídeos na Fila
                  <span className="text-sm font-normal text-gray-500">
                    ({queue.length} {queue.length === 1 ? "arquivo" : "arquivos"})
                  </span>
                </h3>

                <div className="space-y-2">
                  <AnimatePresence>
                    {queue.map((file) => (
                      <motion.div
                        key={file.id}
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex items-center justify-between p-4 bg-[#1a1a1f] rounded-xl border border-white/5"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="text-2xl">{getStatusIcon(file.status)}</span>
                          <div className="min-w-0">
                            <p className="text-white font-medium truncate">
                              {file.filename}
                            </p>
                            <p className="text-xs text-gray-500">{file.size}</p>
                          </div>
                        </div>

                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(file.status)}`}>
                          {getStatusText(file.status)}
                        </span>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            )}

            {/* Estado Vazio */}
            {queue.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>Nenhum vídeo na fila ainda.</p>
                <p className="text-sm mt-1">Arraste um vídeo acima para começar.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className={`
                            fixed bottom-6 left-1/2 -translate-x-1/2 
                            px-6 py-3 rounded-xl shadow-lg z-50
                            ${toast.type === "success" ? "bg-green-600" : "bg-red-600"}
                        `}
          >
            <span className="text-white font-medium">{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
