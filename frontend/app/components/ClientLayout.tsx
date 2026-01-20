'use client';

import { WebSocketProvider } from '../context/WebSocketContext';
import { MoodProvider } from '../context/MoodContext';
import AmbientBackground from './AmbientBackground';
import SplashScreen from './SplashScreen';
import { Toaster } from 'sonner';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
    return (
        <MoodProvider>
            <AmbientBackground />
            <WebSocketProvider>
                <SplashScreen>
                    {children}
                </SplashScreen>
                <Toaster position="top-right" theme="dark" richColors />
            </WebSocketProvider>
        </MoodProvider>
    );
}
