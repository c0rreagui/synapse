import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock } from 'lucide-react';
import clsx from 'clsx';

interface TikTokTimePickerProps {
    value: string; // HH:mm format
    onChange: (value: string) => void;
}

export function TikTokTimePicker({ value, onChange }: TikTokTimePickerProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [inputValue, setInputValue] = useState(value);
    const containerRef = useRef<HTMLDivElement>(null);

    // Initial sync
    useEffect(() => {
        setInputValue(value);
    }, [value]);

    // Handle outside click
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
                validateAndSet(inputValue); // Validate on close
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [inputValue]);

    const validateAndSet = (input: string) => {
        // Validate HH:mm format
        const regex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
        if (regex.test(input)) {
            // Ensure padding
            const [h, m] = input.split(':').map(Number);
            const formatted = `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
            onChange(formatted);
            setInputValue(formatted);
        } else {
            // Revert to props value if invalid
            setInputValue(value);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            validateAndSet(inputValue);
            setIsOpen(false);
            (e.target as HTMLInputElement).blur();
        }
    };

    // Generate Arrays
    const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0'));
    const minutes = Array.from({ length: 12 }, (_, i) => (i * 5).toString().padStart(2, '0')); // 00, 05, 10...

    const [selectedHour, selectedMinute] = value.split(':');

    const handleWheelSelect = (type: 'hour' | 'minute', val: string) => {
        if (type === 'hour') {
            onChange(`${val}:${selectedMinute}`);
        } else {
            onChange(`${selectedHour}:${val}`);
        }
    };

    return (
        <div className="relative" ref={containerRef}>
            {/* Input Trigger */}
            <div
                className="flex items-center gap-3 px-4 py-2 bg-black/40 border border-white/5 rounded-full cursor-text hover:bg-white/5 transition-colors group focus-within:ring-1 focus-within:ring-synapse-purple/50"
            >
                <Clock className="w-4 h-4 text-gray-500 group-focus-within:text-synapse-purple transition-colors" />
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => {
                        setInputValue(e.target.value);
                        // Optional: Live validation or auto-format logic could go here
                    }}
                    onFocus={() => setIsOpen(true)}
                    onKeyDown={handleKeyDown}
                    maxLength={5}
                    className="bg-transparent border-none text-xs text-white focus:ring-0 p-0 font-mono w-10 placeholder-gray-600"
                    placeholder="HH:mm"
                />
            </div>

            {/* Dropdown (Wheel) */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.95 }}
                        className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-[#1a1a1a] border border-white/10 rounded-xl shadow-2xl p-2 z-[60] flex gap-2"
                    >
                        {/* Hours Column */}
                        <div className="h-40 overflow-y-auto w-12 custom-scrollbar snap-y snap-mandatory">
                            <div className="sticky top-0 bg-[#1a1a1a] py-1 z-10 text-[10px] text-center text-gray-500 font-bold uppercase">H</div>
                            {hours.map(h => (
                                <button
                                    key={h}
                                    onClick={() => handleWheelSelect('hour', h)}
                                    className={clsx(
                                        "w-full py-2 text-xs font-mono rounded-lg transition-colors snap-center",
                                        h === selectedHour
                                            ? "bg-blue-600/20 text-blue-400 font-bold border border-blue-500/30"
                                            : "text-gray-400 hover:text-white hover:bg-white/5"
                                    )}
                                >
                                    {h}
                                </button>
                            ))}
                            <div className="h-16" /> {/* Spacer */}
                        </div>

                        <div className="w-px bg-white/5 my-2" />

                        {/* Minutes Column */}
                        <div className="h-40 overflow-y-auto w-12 custom-scrollbar snap-y snap-mandatory">
                            <div className="sticky top-0 bg-[#1a1a1a] py-1 z-10 text-[10px] text-center text-gray-500 font-bold uppercase">M</div>
                            {minutes.map(m => (
                                <button
                                    key={m}
                                    onClick={() => handleWheelSelect('minute', m)}
                                    className={clsx(
                                        "w-full py-2 text-xs font-mono rounded-lg transition-colors snap-center",
                                        m === selectedMinute // Note: exact match only. If manual input is '13', no highlight here, which is fine.
                                            ? "bg-blue-600/20 text-blue-400 font-bold border border-blue-500/30"
                                            : "text-gray-400 hover:text-white hover:bg-white/5"
                                    )}
                                >
                                    {m}
                                </button>
                            ))}
                            <div className="h-16" /> {/* Spacer */}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
