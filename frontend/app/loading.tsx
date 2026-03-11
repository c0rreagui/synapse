export default function Loading() {
    return (
        <div className="min-h-screen bg-[#050507] p-8 flex flex-col pt-24 items-center animate-pulse">
            <div className="w-full max-w-7xl mx-auto space-y-6">
                {/* Header Skeleton */}
                <div className="flex items-center justify-between mb-12">
                    <div className="space-y-3">
                        <div className="h-8 w-64 bg-white/5 rounded-lg" />
                        <div className="h-4 w-96 bg-white/5 rounded-lg" />
                    </div>
                    <div className="flex gap-4">
                        <div className="h-10 w-24 bg-white/5 rounded-lg" />
                        <div className="h-10 w-32 bg-white/5 rounded-lg" />
                    </div>
                </div>

                {/* Grid Skeleton */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                        <div key={i} className="h-48 bg-white/[0.02] border border-white/5 rounded-xl p-6 flex flex-col justify-between">
                            <div className="flex justify-between items-start">
                                <div className="h-12 w-12 bg-white/5 rounded-lg" />
                                <div className="h-6 w-20 bg-white/5 rounded-full" />
                            </div>
                            <div className="space-y-2 mt-auto">
                                <div className="h-4 w-3/4 bg-white/5 rounded" />
                                <div className="h-3 w-1/2 bg-white/5 rounded" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="mt-16 flex flex-col items-center opacity-50">
                <div className="h-10 w-10 rounded-full border-t-2 border-l-2 border-synapse-purple animate-spin" />
                <span className="mt-4 text-xs font-mono text-synapse-purple uppercase tracking-widest">Sincronizando Módulos...</span>
            </div>
        </div>
    );
}
