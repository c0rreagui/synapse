'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useMood } from '../context/MoodContext';
import { useEffect, useState } from 'react';

export default function AmbientBackground() {
    const { mood } = useMood();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) return null;

    // Configuration for each mood state
    const variants: Record<string, import('framer-motion').TargetAndTransition> = {
        IDLE: {
            background: 'radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.15) 0%, rgba(0, 0, 0, 0) 50%)',
            scale: [1, 1.1, 1],
            opacity: 0.8,
            transition: { duration: 8, repeat: Infinity, ease: "easeInOut" }
        },
        PROCESSING: {
            background: 'radial-gradient(circle at 50% 50%, rgba(147, 51, 234, 0.3) 0%, rgba(0, 0, 0, 0) 60%)',
            scale: [1, 1.2, 1],
            opacity: 1,
            transition: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
        },
        SUCCESS: {
            background: 'radial-gradient(circle at 50% 50%, rgba(34, 197, 94, 0.3) 0%, rgba(0, 0, 0, 0) 60%)',
            scale: 1.5,
            opacity: 0,
            transition: { duration: 1.5, ease: "easeOut" } // Flash out
        },
        ERROR: {
            background: 'radial-gradient(circle at 50% 50%, rgba(239, 68, 68, 0.3) 0%, rgba(0, 0, 0, 0) 60%)',
            x: [0, -10, 10, -10, 10, 0], // Shake effect
            opacity: 1,
            transition: { duration: 0.5 }
        }
    };

    return (
        <div className="fixed inset-0 pointer-events-none -z-50 overflow-hidden">
            <AnimatePresence mode="wait">
                <motion.div
                    key={mood}
                    initial={{ opacity: 0 }}
                    animate={variants[mood as keyof typeof variants] || variants.IDLE}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 w-full h-full"
                />
            </AnimatePresence>

            {/* Base dark layer to ensure text readability */}
            <div className="absolute inset-0 bg-black/60 -z-40" />

            {/* Scanline/Grid Effect Overlay (Optional Cyberpunk touch) */}
            <div
                className="absolute inset-0 opacity-[0.03] pointer-events-none -z-30"
                style={{
                    backgroundImage: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
                    backgroundSize: '100% 2px, 3px 100%'
                }}
            />
        </div>
    );
}
