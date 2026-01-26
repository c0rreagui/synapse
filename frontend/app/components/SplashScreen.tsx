'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';

// Rotas para prefetch
const ROUTES_TO_PREFETCH = [
    '/',
    '/profiles',
    '/oracle',
    '/factory',
    '/scheduler',
    '/analytics',
    '/logs'
];

interface InitStep {
    id: string;
    label: string;
    description: string;
    icon: string;
    status: 'pending' | 'loading' | 'done' | 'error';
}

export default function SplashScreen({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [isReady, setIsReady] = useState(false);
    const [progress, setProgress] = useState(0);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [steps, setSteps] = useState<InitStep[]>([
        { id: 'api', label: 'Conectando ao Backend', description: 'Estabelecendo conexão neural', icon: '🔌', status: 'pending' },
        { id: 'routes', label: 'Pré-carregando Módulos', description: 'Preparando interfaces', icon: '📦', status: 'pending' },
        { id: 'profiles', label: 'Carregando Perfis', description: 'Sincronizando identidades', icon: '👤', status: 'pending' },
        { id: 'final', label: 'Inicializando Oracle', description: 'Ativando inteligência', icon: '🔮', status: 'pending' },
    ]);

    const updateStep = (id: string, status: 'loading' | 'done' | 'error') => {
        setSteps(prev => prev.map(s => s.id === id ? { ...s, status } : s));
    };

    useEffect(() => {
        // Se já está pronto (ex: reload), não mostra splash
        if (sessionStorage.getItem('synapse_initialized')) {
            setIsReady(true);
            return;
        }

        // Timer para mostrar tempo decorrido
        const timer = setInterval(() => {
            setElapsedTime(prev => prev + 100);
        }, 100);

        const initialize = async () => {
            try {
                // Step 1: Check API Health
                updateStep('api', 'loading');
                setProgress(10);

                try {
                    const healthRes = await fetch('http://127.0.0.1:8000/health', {
                        signal: AbortSignal.timeout(5000)
                    });
                    if (healthRes.ok) {
                        updateStep('api', 'done');
                    } else {
                        throw new Error('API not healthy');
                    }
                } catch {
                    // API might be slow, continue anyway
                    updateStep('api', 'done');
                }
                setProgress(25);

                // Step 2: Prefetch Routes
                updateStep('routes', 'loading');
                for (let i = 0; i < ROUTES_TO_PREFETCH.length; i++) {
                    router.prefetch(ROUTES_TO_PREFETCH[i]);
                    setProgress(25 + Math.floor((i / ROUTES_TO_PREFETCH.length) * 30));
                    await new Promise(r => setTimeout(r, 100)); // Small delay for visual effect
                }
                updateStep('routes', 'done');
                setProgress(55);

                // Step 3: Load Profiles
                updateStep('profiles', 'loading');
                try {
                    await fetch('http://127.0.0.1:8000/api/v1/profiles', {
                        signal: AbortSignal.timeout(5000)
                    });
                } catch { /* ignore */ }
                updateStep('profiles', 'done');
                setProgress(80);

                // Step 4: Final Oracle Check
                updateStep('final', 'loading');
                try {
                    await fetch('http://127.0.0.1:8000/api/v1/oracle/status', {
                        signal: AbortSignal.timeout(3000)
                    });
                } catch { /* ignore */ }
                updateStep('final', 'done');
                setProgress(100);

                // Mark as initialized
                sessionStorage.setItem('synapse_initialized', 'true');

                // Small delay before showing app
                await new Promise(r => setTimeout(r, 500));
                clearInterval(timer);
                setIsReady(true);

            } catch (error) {
                console.error('Splash init error:', error);

                // If API failed, show error state instead of proceeding
                const isApiError = steps.find(s => s.id === 'api')?.status !== 'done';

                if (isApiError) {
                    updateStep('api', 'error');
                    // Stop everything
                    clearInterval(timer);
                    return; // Stays on Splash with Error
                }

                // Non-critical errors (e.g. profile fetch), proceed logic
                clearInterval(timer);
                setIsReady(true);
            }
        };

        initialize();

        return () => clearInterval(timer);
    }, [router]);

    // Show children when ready
    if (isReady) {
        return <>{children}</>;
    }

    // Check if we have a critical error
    const criticalError = steps.find(s => s.status === 'error');

    return (
        <div className="fixed inset-0 bg-[#050507] z-[9999] flex flex-col items-center justify-center overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />

            {/* ERROR STATE */}
            {criticalError && (
                <div className="relative z-50 flex flex-col items-center animate-in fade-in zoom-in duration-300">
                    <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center border border-red-500/30 mb-6 shadow-[0_0_30px_rgba(239,68,68,0.2)]">
                        <span className="text-4xl">⚠️</span>
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2 tracking-wide">SYSTEM OFFLINE</h2>
                    <p className="text-gray-400 mb-8 max-w-md text-center">
                        Não foi possível conectar ao Núcleo Neural (Backend). Verifique se o servidor está rodando em 127.0.0.1:8000.
                    </p>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-8 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg font-bold transition-all shadow-lg shadow-red-600/20"
                    >
                        TENTAR NOVAMENTE
                    </button>
                </div>
            )}


            {/* Floating Orbs (Only if no error) */}
            {!criticalError && (
                <>
                    <motion.div
                        animate={{
                            scale: [1, 1.2, 1],
                            opacity: [0.3, 0.6, 0.3],
                        }}
                        transition={{ duration: 3, repeat: Infinity }}
                        className="absolute w-96 h-96 bg-purple-600/20 rounded-full blur-3xl"
                    />
                    <motion.div
                        animate={{
                            scale: [1.2, 1, 1.2],
                            opacity: [0.2, 0.4, 0.2],
                        }}
                        transition={{ duration: 4, repeat: Infinity }}
                        className="absolute w-64 h-64 bg-cyan-500/20 rounded-full blur-3xl translate-x-32 translate-y-16"
                    />
                </>
            )}

            {/* Logo & Title (Hidden on Error) */}
            {!criticalError && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="relative z-10 text-center mb-16"
                >
                    {/* Premium Logo Container */}
                    <div className="relative w-40 h-40 mx-auto mb-8">
                        {/* Outer Glow */}
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/30 via-cyan-500/30 to-emerald-500/30 rounded-full blur-2xl animate-pulse" />

                        {/* Orbital Ring 1 - Slow */}
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-2 border border-purple-500/20 rounded-full"
                        >
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-purple-500 rounded-full shadow-[0_0_10px_rgba(139,92,246,0.8)]" />
                        </motion.div>

                        {/* Orbital Ring 2 - Medium */}
                        <motion.div
                            animate={{ rotate: -360 }}
                            transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-6 border border-cyan-500/30 rounded-full"
                        >
                            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-1.5 h-1.5 bg-cyan-400 rounded-full shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
                        </motion.div>

                        {/* Orbital Ring 3 - Fast */}
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-10 border border-emerald-500/40 rounded-full"
                        >
                            <div className="absolute right-0 top-1/2 translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-emerald-400 rounded-full shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
                        </motion.div>

                        {/* Core - Glowing Center */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <motion.div
                                animate={{
                                    boxShadow: [
                                        "0 0 30px rgba(139,92,246,0.4), 0 0 60px rgba(139,92,246,0.2)",
                                        "0 0 50px rgba(139,92,246,0.6), 0 0 100px rgba(139,92,246,0.3)",
                                        "0 0 30px rgba(139,92,246,0.4), 0 0 60px rgba(139,92,246,0.2)"
                                    ]
                                }}
                                transition={{ duration: 2, repeat: Infinity }}
                                className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 via-violet-600 to-indigo-700 flex items-center justify-center"
                            >
                                {/* Neural Icon - Stylized S */}
                                <span className="text-3xl font-black text-white tracking-tighter" style={{ fontFamily: 'system-ui' }}>S</span>
                            </motion.div>
                        </div>

                        {/* Pulse Effect */}
                        <motion.div
                            animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className="absolute inset-0 border-2 border-purple-500/50 rounded-full"
                        />
                    </div>

                    <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-white tracking-[0.2em] uppercase">
                        SYNAPSE
                    </h1>
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                        className="text-gray-500 font-mono text-xs mt-3 tracking-[0.3em] uppercase"
                    >
                        Content Automation System
                    </motion.p>
                </motion.div>
            )}

            {/* Progress Bar (Hidden on Error) */}
            {!criticalError && (
                <motion.div
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: '100%' }}
                    className="relative z-10 w-96 mb-8"
                >
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden shadow-inner">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.3 }}
                            className="h-full bg-gradient-to-r from-purple-500 via-cyan-400 to-emerald-500 rounded-full shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                        />
                    </div>
                    <div className="flex justify-between mt-2">
                        <span className="text-xs text-gray-500 font-mono">INICIALIZANDO</span>
                        <div className="flex items-center gap-3">
                            <span className="text-[10px] text-gray-600 font-mono">{(elapsedTime / 1000).toFixed(1)}s</span>
                            <span className="text-xs text-purple-400 font-mono font-bold">{progress}%</span>
                        </div>
                    </div>
                </motion.div>
            )}

            {/* Steps */}
            {!criticalError && (
                <div className="relative z-10 space-y-2 w-96">
                    <AnimatePresence>
                        {steps.map((step, index) => (
                            <motion.div
                                key={step.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className={`flex items-center gap-4 px-4 py-3 rounded-xl text-sm font-mono transition-all ${step.status === 'done'
                                    ? 'bg-gradient-to-r from-emerald-500/10 to-transparent text-emerald-400 border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]'
                                    : step.status === 'loading'
                                        ? 'bg-gradient-to-r from-purple-500/10 to-transparent text-purple-400 border border-purple-500/30 shadow-[0_0_15px_rgba(139,92,246,0.15)]'
                                        : step.status === 'error'
                                            ? 'bg-gradient-to-r from-red-500/10 to-transparent text-red-400 border border-red-500/30'
                                            : 'bg-white/5 text-gray-500 border border-white/5'
                                    }`}
                            >
                                {/* Step Icon */}
                                <span className="text-lg">{step.icon}</span>

                                {/* Content */}
                                <div className="flex-1">
                                    <span className="font-medium">{step.label}</span>
                                    <p className={`text-[10px] mt-0.5 ${step.status === 'done' ? 'text-emerald-500/50' : step.status === 'loading' ? 'text-purple-400/50' : 'text-gray-600'}`}>
                                        {step.description}
                                    </p>
                                </div>

                                {/* Status Indicator */}
                                <div className="w-5 h-5 flex items-center justify-center">
                                    {step.status === 'done' && (
                                        <motion.span
                                            initial={{ scale: 0 }}
                                            animate={{ scale: 1 }}
                                            className="text-emerald-400 text-lg"
                                        >
                                            ✓
                                        </motion.span>
                                    )}
                                    {step.status === 'loading' && (
                                        <motion.div
                                            animate={{ rotate: 360 }}
                                            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                            className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full"
                                        />
                                    )}
                                    {step.status === 'pending' && (
                                        <span className="text-gray-700">○</span>
                                    )}
                                    {step.status === 'error' && (
                                        <span className="text-red-400">✗</span>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Terminal Log Effect */}
            {!criticalError && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.5 }}
                    transition={{ delay: 1 }}
                    className="absolute bottom-8 left-8 text-[10px] font-mono text-gray-600 space-y-1"
                >
                    <p>&gt; loading neural modules...</p>
                    <p>&gt; establishing oracle connection...</p>
                    <motion.p
                        animate={{ opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 1, repeat: Infinity }}
                    >
                        &gt; _
                    </motion.p>
                </motion.div>
            )}
        </div>
    );
}
