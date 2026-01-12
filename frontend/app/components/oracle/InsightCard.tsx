import React from 'react';
import { motion } from 'framer-motion';

interface InsightCardProps {
    title: string;
    items: string[];
    delay?: number;
    icon?: React.ReactNode;
}

export const InsightCard: React.FC<InsightCardProps> = ({ title, items, delay = 0, icon }) => {
    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay }}
            className="bg-[#0a0a0f]/60 backdrop-blur-md border border-white/10 rounded-xl p-6 hover:border-[#00f3ff]/30 transition-colors"
        >
            <div className="flex items-center gap-3 mb-4">
                {icon && <div className="text-[#00f3ff]">{icon}</div>}
                <h3 className="text-xl font-bold text-white tracking-wide">{title}</h3>
            </div>
            <ul className="space-y-3">
                {items.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-300">
                        <span className="text-[#00f3ff] mt-1.5 text-xs">▶</span>
                        <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
                    </li>
                ))}
            </ul>
        </motion.div>
    );
};
