import type { Meta, StoryObj } from '@storybook/nextjs';
import IntegrationCard from '../app/components/IntegrationCard';
import { useState } from 'react';

const meta: Meta<typeof IntegrationCard> = {
    title: 'App/Molecules/IntegrationCard',
    component: IntegrationCard,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="w-[350px]">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof IntegrationCard>;

export const Connected: Story = {
    args: {
        name: 'TikTok',
        icon: 'tiktok', // Material symbol text
        iconColor: 'text-pink-500',
        iconBgColor: 'bg-pink-500/10',
        connected: true,
        status: 'connected',
        latency: '45ms',
        quota: '3/10',
        lastSync: '2 min ago',
    },
    render: (args) => {
        const [connected, setConnected] = useState(args.connected);
        return <IntegrationCard {...args} connected={connected} onToggle={setConnected} />;
    },
};

export const AwaitingToken: Story = {
    args: {
        name: 'YouTube Shorts',
        icon: 'smart_display',
        iconColor: 'text-red-500',
        iconBgColor: 'bg-red-500/10',
        connected: false,
        status: 'awaiting',
        lastSync: 'Never',
    },
    render: (args) => {
        const [connected, setConnected] = useState(args.connected);
        return <IntegrationCard {...args} connected={connected} onToggle={setConnected} />;
    },
};

export const Inactive: Story = {
    args: {
        name: 'Instagram Reels',
        icon: 'photo_camera',
        iconColor: 'text-purple-500',
        iconBgColor: 'bg-purple-500/10',
        connected: false,
        status: 'inactive',
    },
    render: (args) => {
        const [connected, setConnected] = useState(args.connected);
        return <IntegrationCard {...args} connected={connected} onToggle={setConnected} />;
    },
};
