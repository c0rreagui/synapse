'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

type Mood = 'IDLE' | 'PROCESSING' | 'ERROR' | 'SUCCESS';

interface MoodContextType {
    mood: Mood;
    setMood: (mood: Mood) => void;
}

const MoodContext = createContext<MoodContextType | undefined>(undefined);

export function MoodProvider({ children }: { children: ReactNode }) {
    const [mood, setMood] = useState<Mood>('IDLE');

    return (
        <MoodContext.Provider value={{ mood, setMood }}>
            {children}
        </MoodContext.Provider>
    );
}

export function useMood() {
    const context = useContext(MoodContext);
    if (context === undefined) {
        throw new Error('useMood must be used within a MoodProvider');
    }
    return context;
}
