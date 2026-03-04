'use client';
import React from 'react';

import { WebSocketProvider } from '../context/WebSocketContext';
import { MoodProvider } from '../context/MoodContext';
import AmbientBackground from './AmbientBackground';
import SplashScreen from './SplashScreen';
import { Toaster } from 'sonner';
import { NeoSidebar } from './design-system/NeoSidebar';
import { NeoHeader } from './design-system/NeoHeader';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
    // State removed for new UI

    return (
        <MoodProvider>
            {/* AmbientBackground is kept for dynamic mood colors if needed */}
            <AmbientBackground />

            <WebSocketProvider>
                <SplashScreen>
                    {/* Main Container: Fixed Viewport matching Prototype */}
                    <div className="relative flex h-screen w-full overflow-hidden">
                        {/* Global Background Effects */}
                        <div className="absolute inset-0 bg-celestial-gradient z-0"></div>
                        <div className="absolute inset-0 star-field animate-pulse z-0"></div>
                        <div className="scanline-overlay"></div>
                        <div
                            className="absolute bottom-0 left-0 right-0 h-1/2 bg-grid-perspective opacity-20 pointer-events-none"
                            style={{ transform: 'perspective(1000px) rotateX(60deg) scale(2.5) translateY(100px)' }}
                        ></div>

                        {/* Left Sidebar */}
                        <NeoSidebar />

                        {/* Main App Content */}
                        <main className="flex-1 flex flex-col relative z-20 h-full overflow-hidden">
                            <NeoHeader />
                            {/* The children go inside the master grid wrapper */}
                            <div className="flex-1 p-6 gap-6 overflow-y-auto overflow-x-hidden relative custom-scrollbar">
                                {children}
                            </div>
                        </main>
                    </div>
                </SplashScreen>
                <Toaster position="top-right" theme="dark" richColors />
            </WebSocketProvider>
        </MoodProvider>
    );
}
