import { CpuChipIcon, CircleStackIcon, ServerIcon } from '@heroicons/react/24/outline';

interface SystemStats {
    cpu_percent: number;
    ram_percent: number;
    disk_usage: number;
}

interface Props {
    system?: SystemStats;
}

export default function SystemMonitor({ system }: Props) {
    const stats = system || { cpu_percent: 0, ram_percent: 0, disk_usage: 0 };

    const getColor = (val: number) => {
        if (val > 80) return 'text-red-500 bg-red-500';
        if (val > 50) return 'text-yellow-500 bg-yellow-500';
        return 'text-green-500 bg-green-500';
    };

    const MetricBar = ({ label, value, icon: Icon }: { label: string, value: number, icon: any }) => {
        const colorClass = getColor(value);
        const glowClass = value > 80 ? 'animate-pulse' : '';

        return (
            <div className="bg-black border border-green-900/50 rounded p-3 relative overflow-hidden group">
                {/* Background Fill Effect */}
                <div
                    className={`absolute bottom-0 left-0 w-full opacity-10 transition-all duration-1000 ${colorClass.split(' ')[1]}`}
                    style={{ height: `${value}%` }}
                />

                <div className="flex items-center justify-between mb-2 relative z-10">
                    <div className="flex items-center gap-2 text-gray-400 group-hover:text-white transition-colors">
                        <Icon className="w-4 h-4" />
                        <span className="text-xs font-bold tracking-wider">{label}</span>
                    </div>
                    <span className={`text-sm font-mono font-bold ${colorClass.split(' ')[0]} ${glowClass}`}>
                        {value.toFixed(1)}%
                    </span>
                </div>

                {/* Progress Bar */}
                <div className="h-1.5 w-full bg-gray-900 rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-500 ${colorClass.split(' ')[1]}`}
                        style={{ width: `${value}%` }}
                    />
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-3 font-mono">
            <h3 className="text-xs font-bold text-green-500 mb-2 border-b border-green-900/30 pb-2 flex items-center gap-2">
                <ServerIcon className="w-3 h-3" />
                HARDWARE_TELEMETRY
            </h3>
            <MetricBar label="CPU_CORE" value={stats.cpu_percent} icon={CpuChipIcon} />
            <MetricBar label="RAM_MODULE" value={stats.ram_percent} icon={CircleStackIcon} />
            <MetricBar label="DISK_ARRAY" value={stats.disk_usage} icon={ServerIcon} />
        </div>
    );
}
