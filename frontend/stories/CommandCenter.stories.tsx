import type { Meta, StoryObj } from '@storybook/nextjs';
import CommandCenter from '../app/components/CommandCenter';
import { WebSocketContext } from '../app/context/WebSocketContext';
import { MoodContext } from '../app/context/MoodContext';
import { BackendStatus } from '../app/types';

const MOCK_STATUS_IDLE: BackendStatus = {
    state: 'idle',
    last_updated: new Date().toISOString(),
    job: {
        name: 'Idle',
        step: 'idle',
        progress: 0,
        logs: [],
    },
    system: {
        cpu_percent: 12,
        ram_percent: 34,
        disk_usage: 45,
    },
    bots: [],
};

const MOCK_STATUS_BUSY: BackendStatus = {
    state: 'busy',
    last_updated: new Date().toISOString(),
    job: {
        name: 'Processing Viral Video',
        step: 'processing_video',
        progress: 45,
        logs: [],
    },
    system: {
        cpu_percent: 88,
        ram_percent: 65,
        disk_usage: 45,
    },
    bots: [
        { id: '1', name: 'Bot 1', role: 'UPLOADER', status: 'online' }
    ],
};


const MockProvider = ({ children, status, mood = 'IDLE' }: { children: React.ReactNode, status: BackendStatus, mood?: any }) => (
    <WebSocketContext.Provider value={{
        isConnected: true,
        subscribe: (handlers) => {
            // Simulate immediate update
            setTimeout(() => handlers.onPipelineUpdate?.(status), 0);
            return () => { };
        }
    }}>
        <MoodContext.Provider value={{ mood, setMood: () => { } }}>
            {children}
        </MoodContext.Provider>
    </WebSocketContext.Provider>
);

const meta: Meta<typeof CommandCenter> = {
    title: 'App/Organisms/CommandCenter',
    component: CommandCenter,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story, context) => {
            // Mock Fetch for initial status load
            // @ts-ignore
            global.fetch = (url: string) => {
                if (url.includes('/api/v1/status')) {
                    return Promise.resolve({
                        ok: true,
                        json: async () => context.args.mockStatus || MOCK_STATUS_IDLE
                    });
                }
                return Promise.resolve({ ok: false });
            };

            return (
                <div className="w-full max-w-4xl mx-auto">
                    <MockProvider status={context.args.mockStatus || MOCK_STATUS_IDLE} mood={context.args.mockMood}>
                        <Story />
                    </MockProvider>
                </div>
            );
        },
    ],
};

// Define custom args for the story
interface StoryArgs extends React.ComponentProps<typeof CommandCenter> {
    mockStatus?: BackendStatus;
    mockMood?: string;
}

export default meta;
type Story = StoryObj<StoryArgs>;

export const Idle: Story = {
    args: {
        scheduledVideos: [],
        mockStatus: MOCK_STATUS_IDLE,
        mockMood: 'IDLE',
    },
};

export const Busy: Story = {
    args: {
        scheduledVideos: [],
        mockStatus: MOCK_STATUS_BUSY,
        mockMood: 'PROCESSING',
    },
};
