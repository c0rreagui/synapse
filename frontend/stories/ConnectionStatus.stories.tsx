import type { Meta, StoryObj } from '@storybook/nextjs';
import ConnectionStatus from '../app/components/ConnectionStatus';

const meta: Meta<typeof ConnectionStatus> = {
    title: 'App/Molecules/ConnectionStatus',
    component: ConnectionStatus,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof ConnectionStatus>;

export const Online: Story = {
    args: {
        isOnline: true,
        lastUpdate: 'just now',
    },
};

export const Offline: Story = {
    args: {
        isOnline: false,
        lastUpdate: '5 mins ago',
    },
};
