'use client';
import React from 'react';

import { WebSocketProvider } from '../context/WebSocketContext';
import { MoodProvider } from '../context/MoodContext';
import AmbientBackground from './AmbientBackground';
import SplashScreen from './SplashScreen';
import { Toaster } from 'sonner';
import { NeoSidebar } from '@/components/design-system/NeoSidebar';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
    // START: Client-side Sidebar Logic
    const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);

    // Auto-collapse on smaller screens
    React.useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 1280) { // xl breakpoint
                setIsSidebarCollapsed(true);
            } else {
                setIsSidebarCollapsed(false);
            }
        };

        // Initial check
        handleResize();

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);
    // END: Client-side Sidebar Logic

    return (
        <MoodProvider>
            {/* Global Ambient Glow (Reduces harshness of deep black) */}
            <AmbientBackground />

            <WebSocketProvider>
                <SplashScreen>
                    {/* Main Container: Fixed Viewport */}
                    <div className="flex h-screen w-full overflow-hidden bg-neo-bg text-neo-text-primary selection:bg-neo-primary/30 selection:text-white font-sans">

                        {/* 1. Global Navigation (Floating HUD) */}
                        <div className="relative z-50">
                            <NeoSidebar
                                collapsed={isSidebarCollapsed}
                                onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                            />
                        </div>

                        {/* 2. Main Content Area (Scrollable) */}
                        {/* margin-left calculated to clear the floating sidebar + gap */}
                        <main className={`flex-1 h-full overflow-y-auto p-4 md:p-8 relative z-10 bg-grid-pattern scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent transition-all duration-300 ${isSidebarCollapsed ? 'ml-[120px]' : 'ml-[320px]'}`}>
                            {children}
                        </main>
                    </div>
                </SplashScreen>
                <Toaster position="top-right" theme="dark" richColors />
            </WebSocketProvider>
        </MoodProvider>
    );
}
