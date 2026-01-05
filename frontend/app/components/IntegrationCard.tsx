"use client";

import Toggle from "./Toggle";

interface IntegrationCardProps {
    name: string;
    icon: string;
    iconColor: string;
    iconBgColor: string;
    connected: boolean;
    onToggle: (checked: boolean) => void;
    latency?: string;
    quota?: string;
    lastSync?: string;
    status?: "connected" | "awaiting" | "inactive";
}

export default function IntegrationCard({
    name,
    icon,
    iconColor,
    iconBgColor,
    connected,
    onToggle,
    latency,
    quota,
    lastSync,
    status = "connected",
}: IntegrationCardProps) {
    const statusConfig = {
        connected: {
            label: "Connected",
            dotClass: "bg-success shadow-glow-success",
            textClass: "text-gray-400",
        },
        awaiting: {
            label: "Awaiting Token",
            dotClass: "bg-idle",
            textClass: "text-gray-400",
        },
        inactive: {
            label: "Inactive",
            dotClass: "bg-gray-500",
            textClass: "text-gray-500",
        },
    };

    const config = statusConfig[status];

    return (
        <div className={`glass-card rounded-xl p-5 relative overflow-hidden group ${status === "inactive" ? "opacity-80 hover:opacity-100" : ""}`}>
            {/* Glow effect */}
            <div className={`absolute top-0 right-0 w-20 h-20 ${iconBgColor} blur-[40px] rounded-full -mr-10 -mt-10`}></div>

            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className={`size-10 rounded-lg ${iconBgColor} flex items-center justify-center border border-white/10`}>
                        <span className={`material-symbols-outlined ${iconColor} text-[24px]`}>{icon}</span>
                    </div>
                    <div>
                        <h3 className="font-bold text-white text-base">{name}</h3>
                        <div className="flex items-center gap-1.5 mt-0.5">
                            <span className={`size-1.5 rounded-full ${config.dotClass}`}></span>
                            <span className={`text-xs ${config.textClass}`}>{config.label}</span>
                        </div>
                    </div>
                </div>
                <Toggle id={`toggle-${name.toLowerCase()}`} checked={connected} onChange={onToggle} disabled={status === "inactive"} />
            </div>

            {/* Stats */}
            {(latency || quota) && (
                <div className="grid grid-cols-2 gap-2 mt-4">
                    {latency && (
                        <div className="bg-black/40 rounded p-2 border border-white/5">
                            <p className="text-[10px] text-gray-500 font-mono uppercase">API Latency</p>
                            <p className="text-sm font-mono text-white">{latency}</p>
                        </div>
                    )}
                    {quota && (
                        <div className="bg-black/40 rounded p-2 border border-white/5">
                            <p className="text-[10px] text-gray-500 font-mono uppercase">Daily Quota</p>
                            <p className="text-sm font-mono text-white">{quota}</p>
                        </div>
                    )}
                </div>
            )}

            {lastSync && (
                <div className="bg-black/40 rounded p-2 border border-white/5 mt-4 flex items-center justify-between">
                    <span className="text-[10px] text-gray-500 font-mono uppercase">Last Sync</span>
                    <span className="text-xs font-mono text-gray-300">{lastSync}</span>
                </div>
            )}

            {status === "inactive" && (
                <button className="mt-2 w-full py-1.5 rounded border border-dashed border-gray-700 text-xs text-gray-500 hover:text-white hover:border-gray-500 transition-colors">
                    Configure API Keys
                </button>
            )}
        </div>
    );
}
