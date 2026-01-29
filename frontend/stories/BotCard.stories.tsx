import type { Meta, StoryObj } from '@storybook/react';
import { BotCard } from '../app/components/BotCard';

const meta = {
    title: 'Molecules/BotCard',
    component: BotCard,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        status: {
            control: 'select',
            options: ['active', 'paused', 'error', 'idle'],
        },
        performance: {
            control: { type: 'range', min: 0, max: 100 },
        },
    },
} satisfies Meta<typeof BotCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Active: Story = {
    args: {
        bot: {
            id: '1',
            name: 'Atlas Hunter',
            type: 'ARCHIVIST',
            status: 'active',
            performance: 98,
            uptime: '24h 12m',
            last_action: 'Scanned 120 posts',
            next_scheduled: 'in 5m',
            logs: [],
        },
    },
};

export const Paused: Story = {
    args: {
        bot: {
            id: '2',
            name: 'Forge Writer',
            type: 'WRITER',
            status: 'paused',
            performance: 0,
            uptime: '12h 30m',
            last_action: 'Paused by user',
            next_scheduled: 'Manually',
            logs: [],
        },
    },
};

export const ErrorState: Story = {
    args: {
        bot: {
            id: '3',
            name: 'Watcher Eye',
            type: 'WATCHER',
            status: 'error',
            performance: 45,
            uptime: '2h 15m',
            last_action: 'Connection failed',
            next_scheduled: 'Retry in 1m',
            logs: [],
        },
    },
};

export const Idle: Story = {
    args: {
        bot: {
            id: '4',
            name: 'Oracle Predictor',
            type: 'PREDICTOR',
            status: 'idle',
            performance: 0,
            uptime: '48h 00m',
            last_action: 'Waiting for jobs',
            next_scheduled: 'in 15m',
            logs: [],
        },
    },
};
