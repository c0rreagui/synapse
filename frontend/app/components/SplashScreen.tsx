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
    status: 'pending' | 'loading' | 'done' | 'error';
}

export default function SplashScreen({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [isReady, setIsReady] = useState(false);
    const [progress, setProgress] = useState(0);
    const [steps, setSteps] = useState<InitStep[]>([
        { id: 'api', label: 'Conectando ao Backend', status: 'pending' },
        { id: 'routes', label: 'Pré-carregando Módulos', status: 'pending' },
        { id: 'profiles', label: 'Carregando Perfis', status: 'pending' },
        { id: 'final', label: 'Inicializando Oracle', status: 'pending' },
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

        const initialize = async () => {
            try {
                // Step 1: Check API Health
                updateStep('api', 'loading');
                setProgress(10);

                try {
                    const healthRes = await fetch('http://localhost:8000/health', {
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
                    await fetch('http://localhost:8000/api/v1/profiles', {
                        signal: AbortSignal.timeout(5000)
                    });
                } catch { /* ignore */ }
                updateStep('profiles', 'done');
                setProgress(80);

                // Step 4: Final Oracle Check
                updateStep('final', 'loading');
                try {
                    await fetch('http://localhost:8000/api/v1/oracle/status', {
                        signal: AbortSignal.timeout(3000)
                    });
                } catch { /* ignore */ }
                updateStep('final', 'done');
                setProgress(100);

                // Mark as initialized
                sessionStorage.setItem('synapse_initialized', 'true');

                // Small delay before showing app
                await new Promise(r => setTimeout(r, 500));
                setIsReady(true);

            } catch (error) {
                console.error('Splash init error:', error);
                // Still show app even if initialization fails
                setIsReady(true);
            }
        };

        initialize();
    }, [router]);

    // Show children when ready
    if (isReady) {
        return <>{children}</>;
    }

    return (
        <div className="fixed inset-0 bg-[#050507] z-[9999] flex flex-col items-center justify-center overflow-hidden">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />

            {/* Floating Orbs */}
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

            {/* Logo & Title */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative z-10 text-center mb-12"
            >
                {/* Spinning Ring */}
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-0 w-32 h-32 mx-auto -top-4 border-2 border-purple-500/30 rounded-full border-t-purple-500"
                />

                {/* Logo Icon */}
                <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center shadow-2xl shadow-purple-500/30">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 text-white">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                    </svg>
                </div>

                <h1 className="text-4xl font-bold text-white tracking-wider font-mono">
                    SYNAPSE
                </h1>
                <p className="text-purple-400 font-mono text-sm mt-2 tracking-widest">
                    // CONTENT_AUTO_v1.2.0
                </p>
            </motion.div>

            {/* Progress Bar */}
            <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: '100%' }}
                className="relative z-10 w-80 mb-8"
            >
                <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.3 }}
                        className="h-full bg-gradient-to-r from-purple-500 to-cyan-500 rounded-full"
                    />
                </div>
                <div className="flex justify-between mt-2">
                    <span className="text-xs text-gray-500 font-mono">INICIALIZANDO</span>
                    <span className="text-xs text-purple-400 font-mono">{progress}%</span>
                </div>
            </motion.div>

            {/* Steps */}
            <div className="relative z-10 space-y-3 w-80">
                <AnimatePresence>
                    {steps.map((step, index) => (
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className={`flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-mono transition-all ${step.status === 'done'
                                    ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                                    : step.status === 'loading'
                                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                                        : step.status === 'error'
                                            ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                            : 'bg-white/5 text-gray-500 border border-white/5'
                                }`}
                        >
                            {/* Status Icon */}
                            <div className="w-5 h-5 flex items-center justify-center">
                                {step.status === 'done' && (
                                    <motion.span
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        className="text-green-400"
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
                                    <span className="text-gray-600">○</span>
                                )}
                                {step.status === 'error' && (
                                    <span className="text-red-400">✗</span>
                                )}
                            </div>
                            <span>{step.label}</span>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Terminal Log Effect */}
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
        </div>
    );
}
