import type { Meta, StoryObj } from '@storybook/nextjs';
import LogTerminal from '../app/components/LogTerminal';

const SAMPLE_LOGS = [
    { timestamp: '10:00:01', level: 'info', message: 'System initialization started...' },
    { timestamp: '10:00:02', level: 'info', message: 'Loading modules: [Audio, Video, AI]' },
    { timestamp: '10:00:03', level: 'success', message: 'Modules loaded successfully.' },
    { timestamp: '10:00:05', level: 'warning', message: 'Deprecation warning: Torch v1.9 is old.' },
    { timestamp: '10:00:10', level: 'info', message: 'Connecting to WebSocket...' },
    { timestamp: '10:00:11', level: 'success', message: 'WebSocket connected.' },
    { timestamp: '10:15:00', level: 'error', message: 'Connection lost. Retrying in 5s...' },
    { timestamp: '10:15:05', level: 'info', message: 'Reconnecting...' },
    { timestamp: '10:15:06', level: 'success', message: 'Connection restored.' },
];

const meta: Meta<typeof LogTerminal> = {
    title: 'App/Organisms/LogTerminal',
    component: LogTerminal,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof LogTerminal>;

export const Default: Story = {
    args: {
        logs: SAMPLE_LOGS as any[],
        className: 'h-[400px] w-full',
    },
};

export const Empty: Story = {
    args: {
        logs: [],
        className: 'h-[300px] w-full',
    },
};

export const AutoScroll: Story = {
    args: {
        logs: [
            ...SAMPLE_LOGS,
            ...Array.from({ length: 20 }).map((_, i) => ({
                timestamp: `10:20:${String(i).padStart(2, '0')}`,
                level: 'info',
                message: `Processing batch frame ${i * 100}...`,
            })),
        ] as any[],
        className: 'h-[400px] w-full',
        autoScroll: true,
    },
};
