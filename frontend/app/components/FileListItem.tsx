"use client";

import { motion } from "framer-motion";

interface FileListItemProps {
    filename: string;
    status: "ready" | "processing" | "uploading" | "queued";
    resolution?: string;
    duration?: string;
    size?: string;
    progress?: number;
    index?: number;
}

const statusConfig = {
    ready: {
        label: "PRONTO",
        color: "success",
        icon: "verified",
        textClass: "text-success",
        bgClass: "bg-success/5 border-success/10",
        dotClass: "bg-success",
    },
    processing: {
        label: "PROCESSANDO...",
        color: "primary",
        icon: null,
        textClass: "text-primary",
        bgClass: "bg-primary/5 border-primary/10",
        dotClass: "bg-primary",
    },
    uploading: {
        label: "ENVIANDO...",
        color: "neon-cyan",
        icon: "sync",
        textClass: "text-neon-cyan",
        bgClass: "bg-neon-cyan/5 border-neon-cyan/10",
        dotClass: "bg-neon-cyan",
    },
    queued: {
        label: "NA FILA",
        color: "warning",
        icon: "schedule",
        textClass: "text-warning",
        bgClass: "bg-warning/5 border-warning/10",
        dotClass: "bg-warning",
    },
};

export default function FileListItem({
    filename,
    status,
    resolution = "1080p",
    duration,
    size,
    progress,
    index = 0,
}: FileListItemProps) {
    const config = statusConfig[status];

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="group relative flex items-center justify-between p-4 bg-card-surface border border-white/5 hover:border-primary/30 rounded-lg overflow-hidden transition-all"
        >
            {/* Left accent bar */}
            <div className={`absolute left-0 top-0 bottom-0 w-0.5 ${config.dotClass} opacity-0 group-hover:opacity-100 transition-opacity`} />

            <div className="flex items-center gap-4 relative z-10">
                {/* Thumbnail placeholder */}
                <div className="w-10 h-10 rounded bg-[#13111a] border border-white/10 flex items-center justify-center text-primary">
                    <span className="material-symbols-outlined text-lg">movie</span>
                </div>

                <div>
                    <p className="text-gray-200 font-medium text-sm font-mono tracking-tight">{filename}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[9px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded border border-white/5 uppercase">
                            MP4
                        </span>
                        <span className="text-[9px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded border border-white/5 uppercase">
                            {resolution}
                        </span>
                        {size && <span className="text-[9px] text-gray-500 font-mono">{size}</span>}
                        {duration && <span className="text-[9px] text-gray-500 font-mono">{duration}</span>}
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-4 relative z-10">
                {/* Status indicator */}
                {status === "processing" || status === "uploading" ? (
                    <div className="flex flex-col gap-1.5 w-40">
                        <div className={`flex items-center gap-2 ${config.textClass}`}>
                            {config.icon && (
                                <span className="material-symbols-outlined text-sm animate-spin">{config.icon}</span>
                            )}
                            {!config.icon && (
                                <span className="relative flex h-2 w-2">
                                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.dotClass} opacity-75`}></span>
                                    <span className={`relative inline-flex rounded-full h-2 w-2 ${config.dotClass} shadow-[0_0_8px_currentColor]`}></span>
                                </span>
                            )}
                            <span className="text-[10px] font-mono uppercase tracking-widest font-bold glow-text">
                                {config.label}
                            </span>
                            {progress !== undefined && (
                                <span className="text-white font-mono">{progress}%</span>
                            )}
                        </div>
                        <div className="h-1.5 w-full bg-card-darker rounded-full overflow-hidden border border-white/5 relative">
                            <div
                                className={`h-full bg-gradient-to-r from-transparent via-${config.color} to-transparent rounded-full animate-shimmer shadow-[0_0_10px_currentColor] w-[var(--progress-width)]`}
                                // eslint-disable-next-line
                                style={{ "--progress-width": progress ? `${progress}%` : "50%" } as React.CSSProperties}
                            />
                        </div>
                    </div>
                ) : (
                    <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${config.bgClass} border`}>
                        {config.icon && (
                            <span className={`material-symbols-outlined text-sm ${config.textClass} glow-text-green`}>{config.icon}</span>
                        )}
                        <span className={`w-1.5 h-1.5 rounded-full ${config.dotClass} ${status === "ready" ? "animate-pulse" : ""}`} />
                        <span className={`text-[10px] font-bold ${config.textClass} tracking-wider`}>{config.label}</span>
                    </div>
                )}

                {/* Action button */}
                <button className="text-gray-500 hover:text-white p-2 rounded-full hover:bg-white/5 transition-colors">
                    <span className="material-symbols-outlined text-lg">more_vert</span>
                </button>
            </div>
        </motion.div>
    );
}
