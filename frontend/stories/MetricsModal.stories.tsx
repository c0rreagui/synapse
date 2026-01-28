import type { Meta, StoryObj } from '@storybook/nextjs';
import MetricsModal from '../app/components/MetricsModal';
import { WebSocketContext } from '../app/context/WebSocketContext';
import { useState, ReactNode } from 'react';

// Mock WebSocket Context
const MockWebSocketProvider = ({ children }: { children: ReactNode }) => {
    return (
        <WebSocketContext.Provider value={{
            isConnected: true,
            subscribe: () => () => { }
        }}>
            {children}
        </WebSocketContext.Provider>
    );
};

// Mock Fetch Global
// We define the mock logic outside the story to keep it clean, but apply it inside the decorator
// Avoiding 'as Response' casting which confuses acorn parser
const mockFetch = (url: string): Promise<any> => {
    return new Promise((resolve) => {
        if (url.includes('/ingest/files')) {
            resolve({
                ok: true,
                json: async () => ({
                    queued: [{ name: 'video1.mp4', size: 52428800, modified: new Date().toISOString(), path: '/data/queued/video1.mp4' }],
                    processing: [{ name: 'generating_caption.mp4', size: 125829120, modified: new Date().toISOString(), path: '/data/processing' }],
                    completed: [
                        { name: 'final_cut.mp4', size: 47185920, modified: new Date().toISOString(), path: '/data/completed' },
                        { name: 'short_clip.mov', size: 15728640, modified: new Date().toISOString(), path: '/data/completed' }
                    ],
                    failed: [{ name: 'corrupted.avi', size: 0, modified: new Date().toISOString(), path: '/data/failed' }]
                })
            });
            return;
        }
        if (url.includes('/scheduler/list')) {
            resolve({
                ok: true,
                json: async () => ([
                    { id: '1', video_path: 'final_cut.mp4', scheduled_time: new Date().toISOString(), status: 'pending', profile_id: 'tiktok_main' }
                ])
            });
            return;
        }
        resolve({ ok: false });
    });
};

const meta: Meta<typeof MetricsModal> = {
    title: 'App/Organisms/MetricsModal',
    component: MetricsModal,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => {
            // Monkey patch fetch safely
            // @ts-ignore
            global.fetch = mockFetch;
            return (
                <MockWebSocketProvider>
                    <div className="h-screen w-full bg-[#050505] flex items-center justify-center">
                        <Story />
                    </div>
                </MockWebSocketProvider>
            );
        }
    ]
};

export default meta;
type Story = StoryObj<typeof MetricsModal>;

export const Default = {
    render: () => {
        const [isOpen, setIsOpen] = useState(true);
        return (
            <>
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed top-4 left-4 px-4 py-2 bg-cyan-500 text-black font-bold rounded"
                >
                    Open Metrics
                </button>
                <MetricsModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
            </>
        );
    }
};

export const OpenOnQueued: Story = {
    args: {
        isOpen: true,
        initialTab: 'queued',
        onClose: () => { },
    }
};
