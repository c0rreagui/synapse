'use client';

import { useEffect } from 'react';
import { StitchCard } from './components/StitchCard';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log the error to an analytics service
        console.error('Global Error Boundary caught:', error);
    }, [error]);

    return (
        <div className="min-h-screen bg-[#050507] flex items-center justify-center p-4">
            <StitchCard className="max-w-md w-full p-8 text-center border-red-500/30 bg-red-900/10">
                <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                    <span className="text-3xl">💥</span>
                </div>
                <h2 className="text-xl font-bold text-white mb-2">Algo deu errado</h2>
                <p className="text-gray-400 text-sm mb-6">
                    Um erro crítico ocorreu na interface. Detalhes técnicos foram registrados no console.
                </p>
                <div className="bg-black/40 p-4 rounded text-left mb-6 overflow-auto max-h-32 border border-white/5">
                    <code className="text-[10px] text-red-300 font-mono">
                        {error.toString()}
                    </code>
                </div>
                <button
                    onClick={() => reset()}
                    className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-bold transition-colors w-full"
                >
                    Tentar Novamente
                </button>
            </StitchCard>
        </div>
    );
}
