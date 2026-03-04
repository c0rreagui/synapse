import type { Meta, StoryObj } from '@storybook/react';
import BotCard from '../app/components/BotCard';

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
            options: ['online', 'offline', 'error', 'sleeping'],
        },
        role: {
            control: 'select',
            options: ['UPLOADER', 'FACTORY', 'MONITOR', 'SCHEDULER'],
        }
    },
} satisfies Meta<typeof BotCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Active: Story = {
    args: {
        id: '1',
        name: 'Atlas Hunter',
        role: 'FACTORY',
        status: 'online',
        uptime: '24h 12m',
        currentTask: 'Processing video',
        description: 'Generating optimized clips for TikTok',
    },
};

export const Sleeping: Story = {
    args: {
        id: '2',
        name: 'Forge Writer',
        role: 'UPLOADER',
        status: 'sleeping',
        uptime: '12h 30m',
        currentTask: 'SYSTEM_READY',
        description: 'Waiting for scheduled upload window',
    },
};

export const ErrorState: Story = {
    args: {
        id: '3',
        name: 'Watcher Eye',
        role: 'MONITOR',
        status: 'error',
        uptime: '2h 15m',
        currentTask: 'OFFLINE',
        description: 'Connection to Target Failed',
    },
};

export const Offline: Story = {
    args: {
        id: '4',
        name: 'Oracle Predictor',
        role: 'SCHEDULER',
        status: 'offline',
        uptime: '0h',
        currentTask: 'OFFLINE',
        description: 'System is shut down',
    },
};
