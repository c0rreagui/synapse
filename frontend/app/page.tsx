"use client";

import { useState, useCallback, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { Toaster, toast } from "sonner";
import {
  UploadCloud,
  Zap,
  CheckCircle2,
  Cpu,
  Radio,
  Sparkles,
  CalendarClock
} from "lucide-react";

export default function Home() {
  const [uploading, setUploading] = useState(false);
  const [profile, setProfile] = useState("p1");
  const [scheduleTime, setScheduleTime] = useState("");
  const [isScheduleEnabled, setIsScheduleEnabled] = useState(false);

  // Estado para perfis dinâmicos
  const [availableProfiles, setAvailableProfiles] = useState<{ id: string, name: string, username?: string, avatar?: string }[]>([]);

  // Carrega perfis ao iniciar
  useEffect(() => {
    fetch("http://localhost:8000/api/v1/profiles")
      .then(res => res.json())
      .then(data => {
        setAvailableProfiles(data);
        if (data.length > 0 && !profile) {
          setProfile(data[0].id);
        }
      })
      .catch((err) => {
        console.error("Erro ao carregar perfis:", err);
        // Fallback local
        setAvailableProfiles([
          { id: "tiktok_profile_01", name: "Perfil 01 (Offline)" },
          { id: "tiktok_profile_02", name: "Perfil 02 (Offline)" }
        ]);
      });
  }, []);

  // Função para definir horários rápidos (Atalhos)
  const setQuickTime = (hour: number) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(hour, 0, 0, 0);

    // Formato manual para preservar o fuso horário local (YYYY-MM-DDTHH:MM)
    const year = tomorrow.getFullYear();
    const month = String(tomorrow.getMonth() + 1).padStart(2, '0');
    const day = String(tomorrow.getDate()).padStart(2, '0');
    const hours = String(tomorrow.getHours()).padStart(2, '0');
    const minutes = String(tomorrow.getMinutes()).padStart(2, '0');

    const localIsoString = `${year}-${month}-${day}T${hours}:${minutes}`;

    setScheduleTime(localIsoString);
    setIsScheduleEnabled(true);
    toast.success(`Agendado para amanhã às ${hour}:00`);
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    const file = acceptedFiles[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("profile_id", profile);

    // Só envia a data se o checkbox estiver marcado e tiver data
    if (isScheduleEnabled && scheduleTime) {
      formData.append("schedule_time", scheduleTime);
      toast.info(`⏳ Injetando no fluxo temporal: ${new Date(scheduleTime).toLocaleString()}`);
    } else {
      toast.info("⚡ Iniciando transmissão neural imediata...");
    }

    try {
      const response = await fetch("http://localhost:8000/api/v1/ingest/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        toast.success("✅ Dados assimilados pela Fábrica!");
      } else {
        toast.error("❌ Falha na conexão neural.");
      }
    } catch {
      toast.error("⚠️ Erro crítico no uplink.");
    } finally {
      setUploading(false);
    }
  }, [profile, scheduleTime, isScheduleEnabled]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "video/mp4": [".mp4", ".mov"] },
    maxFiles: 1,
  });

  return (
    <div className="min-h-screen bg-[#050507] text-white font-sans selection:bg-blue-500/30 relative overflow-hidden">
      {/* Background Grid Mesh */}
      <div className="absolute inset-0 bg-grid-white [mask-image:linear-gradient(0deg,transparent,black)] pointer-events-none" />
      <div className="absolute top-0 center-0 w-full h-96 bg-blue-900/10 blur-[120px] rounded-full pointer-events-none mix-blend-screen" />

      <Toaster position="bottom-right" theme="dark" closeButton />

      <main className="max-w-4xl mx-auto pt-16 px-6 relative z-10">

        {/* HEADER */}
        <header className="mb-12 text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-mono mb-4">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            SYSTEM ONLINE
          </div>

          <h1 className="text-5xl md:text-6xl font-black tracking-tighter bg-gradient-to-br from-white via-white to-blue-500 bg-clip-text text-transparent transform hover:scale-[1.01] transition-transform cursor-default">
            SYNAPSE
            <span className="text-blue-600">.</span>
            AUTO
          </h1>
          <p className="text-lg text-neutral-400 font-medium max-w-xl mx-auto leading-relaxed">
            Central de Comando de Conteúdo Neural
          </p>
        </header>

        {/* MAIN CONTROL PANEL */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">

          {/* SIDEBAR / CONTROLS (4 cols) */}
          <div className="md:col-span-4 space-y-6">


            {/* PROFILE SELECTOR */}
            <div className="p-5 rounded-2xl bg-neutral-900/40 border border-white/5 backdrop-blur-md shadow-xl hover:border-white/10 transition-colors">
              <div className="flex items-center gap-2 mb-4 text-sm font-semibold text-neutral-300">
                <Radio className="w-4 h-4 text-blue-500" />
                CANAL DE TRANSMISSÃO
              </div>

              <div className="flex flex-col gap-2 bg-neutral-900 p-1 rounded-lg border border-neutral-800">
                {availableProfiles.length === 0 && (
                  <div className="text-center text-xs text-neutral-500 py-4">Carregando canais...</div>
                )}
                {availableProfiles.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setProfile(p.id)}
                    className={`w-full flex items-center justify-between p-2 pl-2 pr-3 rounded-xl transition-all duration-300 border ${profile === p.id
                      ? "bg-blue-600/10 border-blue-500/50 text-white translate-x-1"
                      : "bg-neutral-800/30 border-transparent text-neutral-400 hover:bg-neutral-800 hover:text-white"
                      }`}
                  >
                    <div className="flex items-center gap-3">
                      {p.avatar ? (
                        <img src={p.avatar} alt={p.name} className="w-9 h-9 rounded-full border border-white/10 object-cover" />
                      ) : (
                        <div className="w-9 h-9 rounded-full bg-neutral-800 flex items-center justify-center text-xs font-bold border border-white/5">
                          {p.name.charAt(0)}
                        </div>
                      )}
                      <div className="text-left">
                        <div className={`text-sm font-medium leading-tight ${profile === p.id ? "text-blue-400" : "text-neutral-200"}`}>
                          {p.name}
                        </div>
                        {p.username && (
                          <div className="text-[10px] text-neutral-500 font-mono mt-0.5">
                            @{p.username}
                          </div>
                        )}
                      </div>
                    </div>

                    {profile === p.id && <CheckCircle2 className="w-4 h-4 text-blue-400" />}
                  </button>
                ))}
              </div>
            </div>

            {/* SCHEDULER PANEL */}
            <div className={`p-5 rounded-2xl border transition-all duration-300 ${isScheduleEnabled
              ? "bg-blue-900/10 border-blue-500/30"
              : "bg-neutral-900/40 border-white/5"
              } backdrop-blur-md`}>

              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-neutral-300">
                  <CalendarClock className={`w-4 h-4 ${isScheduleEnabled ? "text-blue-400" : "text-neutral-500"}`} />
                  TIME TRAVEL
                </div>
                <div
                  onClick={() => {
                    setIsScheduleEnabled(!isScheduleEnabled);
                    if (!isScheduleEnabled) toast("Protocolo de Tempo Ativado");
                  }}
                  className={`w-10 h-6 rounded-full p-1 cursor-pointer transition-colors duration-300 ${isScheduleEnabled ? "bg-blue-500" : "bg-neutral-700"
                    }`}
                >
                  <div className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform duration-300 ${isScheduleEnabled ? "translate-x-4" : "translate-x-0"
                    }`} />
                </div>
              </div>

              {/* EXPANDABLE AREA */}
              <div className={`space-y-4 overflow-hidden transition-all duration-500 ${isScheduleEnabled ? "max-h-64 opacity-100" : "max-h-0 opacity-50"
                }`}>
                <div className="grid grid-cols-2 gap-2">
                  <button onClick={() => setQuickTime(10)} className="p-2 text-xs bg-neutral-800 rounded-lg hover:bg-neutral-700 border border-white/5 transition-colors">
                    ⛅ Amanhã 10h
                  </button>
                  <button onClick={() => setQuickTime(14)} className="p-2 text-xs bg-neutral-800 rounded-lg hover:bg-neutral-700 border border-white/5 transition-colors">
                    ☀️ Amanhã 14h
                  </button>
                  <button onClick={() => setQuickTime(18)} className="p-2 text-xs bg-neutral-800 rounded-lg hover:bg-neutral-700 border border-white/5 transition-colors">
                    🌙 Amanhã 18h
                  </button>
                  <button onClick={() => setQuickTime(20)} className="p-2 text-xs bg-neutral-800 rounded-lg hover:bg-neutral-700 border border-white/5 transition-colors">
                    🌃 Amanhã 20h
                  </button>
                </div>

                <input
                  type="datetime-local"
                  aria-label="Selecionar data e hora do agendamento"
                  value={scheduleTime}
                  onChange={(e) => setScheduleTime(e.target.value)}
                  className="w-full bg-[#0a0a0c] border border-neutral-800 text-white text-xs rounded-lg p-3 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all [color-scheme:dark]"
                />
              </div>
            </div>

          </div>

          {/* DROPZONE AREA (8 cols) */}
          <div className="md:col-span-8">
            <div
              {...getRootProps()}
              className={`
                h-full min-h-[400px] rounded-3xl border-2 border-dashed transition-all duration-300 relative group
                flex flex-col items-center justify-center p-12 text-center overflow-hidden
                ${isDragActive
                  ? "border-blue-500 bg-blue-500/5 shadow-[0_0_50px_-12px_rgba(59,130,246,0.3)] scale-[1.01]"
                  : "border-neutral-800 bg-neutral-900/20 hover:border-neutral-700 hover:bg-neutral-900/40"
                }
              `}
            >
              <input {...getInputProps()} />

              {/* Animated Glow Effect */}
              <div className="absolute inset-0 bg-blue-500/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />

              <div className={`
                w-24 h-24 mb-6 rounded-2xl flex items-center justify-center
                bg-gradient-to-br from-[#1a1a1f] to-[#0d0d10] border border-white/5 shadow-2xl
                group-hover:scale-110 group-hover:border-blue-500/30 transition-all duration-300
              `}>
                {uploading ? (
                  <Zap className="w-10 h-10 text-yellow-400 animate-pulse" />
                ) : isDragActive ? (
                  <UploadCloud className="w-10 h-10 text-blue-400 animate-bounce" />
                ) : (
                  <Sparkles className="w-10 h-10 text-neutral-500 group-hover:text-blue-400 transition-colors" />
                )}
              </div>

              <h2 className="text-2xl font-bold text-white mb-2 relative z-10">
                {isDragActive ? "Liberar Carga de Dados" : "Iniciar Ingestão"}
              </h2>

              <p className="text-neutral-500 text-sm max-w-sm mx-auto leading-relaxed relative z-10">
                Arraste arquivos de vídeo para o portal ou clique para acessar o diretório local.
              </p>

              <div className="mt-8 flex items-center gap-4 text-xs font-mono text-neutral-600 border border-white/5 rounded-full px-4 py-2 bg-[#050507]/50 backdrop-blur-sm">
                <span className="flex items-center gap-1.5"><Cpu className="w-3 h-3" /> MP4/MOV READY</span>
                <span className="w-px h-3 bg-neutral-800" />
                <span className="flex items-center gap-1.5"><Zap className="w-3 h-3" /> ULTRA FAST</span>
              </div>

            </div>
          </div>

        </div>

        {/* FOOTER STATUS */}
        <footer className="mt-12 border-t border-white/5 pt-8 pb-8 flex justify-between items-center text-xs text-neutral-600 font-mono">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500/20 border border-emerald-500/50"></span>
            FACTORIES: OPERATIONAL
          </div>
          <div>
            VERSION 2.1.0-NEURAL
          </div>
        </footer>

      </main>
    </div>
  );
}

