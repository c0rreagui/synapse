interface StatCardProps {
    label: string;
    value: string;
    unit?: string;
    icon: string;
    color: "primary" | "success" | "secondary" | "warning";
    trend?: string;
    trendType?: "up" | "down" | "neutral";
}

const colorMap = {
    primary: {
        icon: "text-primary",
        bg: "bg-primary/10",
        border: "border-primary/20",
        trend: "text-primary bg-primary/5 border-primary/10",
    },
    success: {
        icon: "text-success",
        bg: "bg-success/10",
        border: "border-success/20",
        trend: "text-success bg-success/5 border-success/10",
    },
    secondary: {
        icon: "text-secondary",
        bg: "bg-secondary/10",
        border: "border-secondary/20",
        trend: "text-secondary bg-secondary/5 border-secondary/10",
    },
    warning: {
        icon: "text-warning",
        bg: "bg-warning/10",
        border: "border-warning/20",
        trend: "text-warning bg-warning/5 border-warning/10",
    },
};

export default function StatCard({
    label,
    value,
    unit,
    icon,
    color,
    trend,
    trendType = "up",
}: StatCardProps) {
    const colors = colorMap[color];

    return (
        <div className="glass-panel rounded-2xl p-6 group">
            {/* Background Icon */}
            <div className={`absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-all transform group-hover:scale-110 duration-500`}>
                <span className={`material-symbols-outlined text-8xl ${colors.icon}`}>{icon}</span>
            </div>

            <div className="relative z-10 flex flex-col h-full justify-between gap-4">
                {/* Header */}
                <div className="flex items-center gap-3 text-[#94a3b8]">
                    <div className={`p-2 rounded-lg ${colors.bg} border ${colors.border} shadow-inner`}>
                        <span className={`material-symbols-outlined ${colors.icon} text-xl`}>{icon}</span>
                    </div>
                    <span className="text-xs font-mono font-medium uppercase tracking-wider text-white/60">{label}</span>
                </div>

                {/* Value */}
                <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-white tracking-tighter tabular-nums drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
                        {value}
                    </span>
                    {unit && <span className="text-xs font-mono text-[#94a3b8]">{unit}</span>}
                </div>

                {/* Trend */}
                {trend && (
                    <div className={`flex items-center gap-2 text-[10px] font-mono font-medium ${colors.trend} self-start px-2 py-1 rounded border`}>
                        <span className="material-symbols-outlined text-sm">
                            {trendType === "up" ? "trending_up" : trendType === "down" ? "trending_down" : "trending_flat"}
                        </span>
                        {trend}
                    </div>
                )}
            </div>

            {/* Data Flow Animation */}
            <div className="data-flow-line opacity-50"></div>
        </div>
    );
}
