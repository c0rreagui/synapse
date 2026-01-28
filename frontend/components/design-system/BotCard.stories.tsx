import type { Meta, StoryObj } from '@storybook/nextjs';
import BotCard from './BotCard';

const meta: Meta<typeof BotCard> = {
    title: 'Design System/Molecules/BotCard',
    component: BotCard,
    tags: ['autodocs'],
    argTypes: {
        role: {
            control: 'select',
            options: ['UPLOADER', 'FACTORY', 'MONITOR', 'SCHEDULER'],
        },
        status: {
            control: 'select',
            options: ['online', 'offline', 'error', 'sleeping'],
        },
    },
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div style={{ width: '500px' }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof BotCard>;

export const Online: Story = {
    args: {
        id: 'bot-01',
        name: 'ATLAS-01',
        role: 'UPLOADER',
        status: 'online',
        currentTask: 'UPLOADING_CHUNK_42',
        uptime: '4h 20m',
        description: 'High-bandwidth transmission unit. Guaranteeing global propagation metrics.',
    },
};

export const FactoryMode: Story = {
    args: {
        id: 'bot-02',
        name: 'FORGE-X',
        role: 'FACTORY',
        status: 'online',
        currentTask: 'SYNTHESIZING_DATA',
        uptime: '12h 00m',
        description: 'Neural synthesis core. Assembling raw data into cognitive constructs.',
    },
};

export const MonitorOffline: Story = {
    args: {
        id: 'bot-03',
        name: 'WATCHER-V2',
        role: 'MONITOR',
        status: 'offline',
        description: 'Omniscient sentinel. Analyzing telemetry anomalies in real-time.',
    },
};

export const SchedulerSleeping: Story = {
    args: {
        id: 'bot-04',
        name: 'CHRONOS',
        role: 'SCHEDULER',
        status: 'sleeping',
        uptime: '48h 15m',
        description: 'Temporal alignment engine. Orchestrating event horizons.',
    },
};
