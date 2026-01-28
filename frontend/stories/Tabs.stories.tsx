import type { Meta, StoryObj } from '@storybook/nextjs';
import Tabs from '../app/components/Tabs';
import { UserIcon, CogIcon, BellIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof Tabs> = {
    title: 'App/Molecules/Tabs',
    component: Tabs,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof Tabs>;

export const Default: Story = {
    args: {
        tabs: [
            {
                id: 'profile',
                label: 'Profile',
                icon: <UserIcon className="w-4 h-4" />,
                content: <div className="p-4 text-gray-400">Profile Settings Content</div>,
            },
            {
                id: 'notifications',
                label: 'Notifications',
                icon: <BellIcon className="w-4 h-4" />,
                badge: 3,
                content: <div className="p-4 text-gray-400">You have 3 new notifications</div>,
            },
            {
                id: 'settings',
                label: 'Settings',
                icon: <CogIcon className="w-4 h-4" />,
                content: <div className="p-4 text-gray-400">Global Configuration</div>,
            },
        ],
    },
};
