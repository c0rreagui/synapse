import React from 'react';
import { motion } from 'framer-motion';

interface ViralScoreGaugeProps {
    score: number; // 0-10
}

export const ViralScoreGauge: React.FC<ViralScoreGaugeProps> = ({ score }) => {
    // Normalize 0-10 to 0-100 for gauge
    const percentage = Math.min(Math.max(score * 10, 0), 100);

    // Color logic
    let color = '#ff003c'; // Red
    if (percentage >= 50) color = '#fcee0a'; // Yellow
    if (percentage >= 80) color = '#00f3ff'; // Cyan

    return (
        <div className="relative w-48 h-48 flex items-center justify-center">
            {/* Background Circle */}
            <svg className="w-full h-full transform -rotate-90">
                <circle
                    cx="96"
                    cy="96"
                    r="88"
                    stroke="#1a1a2e"
                    strokeWidth="12"
                    fill="transparent"
                />
                {/* Progress Circle */}
                <motion.circle
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: percentage / 100 }}
                    transition={{ duration: 2, ease: "easeOut" }}
                    cx="96"
                    cy="96"
                    r="88"
                    stroke={color}
                    strokeWidth="12"
                    fill="transparent"
                    strokeDasharray="553" // 2 * PI * 88
                    strokeLinecap="round"
                    className="drop-shadow-[0_0_10px_rgba(0,243,255,0.5)]"
                />
            </svg>

            {/* Score Text */}
            <div className="absolute flex flex-col items-center">
                <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-5xl font-bold font-mono text-white"
                >
                    {score.toFixed(1)}
                </motion.span>
                <span className="text-xs text-uppercase tracking-widest text-gray-400 mt-1">VIRALITY</span>
            </div>
        </div>
    );
};
