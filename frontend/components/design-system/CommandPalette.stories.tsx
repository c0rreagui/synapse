import type { Meta, StoryObj } from '@storybook/nextjs';
import CommandPalette from './CommandPalette';
import { HomeIcon, UserIcon, CogIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof CommandPalette> = {
    title: 'Design System/Organisms/CommandPalette',
    component: CommandPalette,
    tags: ['autodocs'],
    parameters: {
        layout: 'fullscreen',
        backgrounds: { default: 'dark' },
    },
    args: {
        isOpen: true,
    },
};

export default meta;
type Story = StoryObj<typeof CommandPalette>;

const mockCommands = [
    {
        id: 'home',
        title: 'Go to Dashboard',
        description: 'Navigate to the main command center',
        icon: <HomeIcon className="w-5 h-5" />,
        shortcut: 'G D',
        action: () => alert('Navigating to Dashboard'),
        category: 'Navigation',
    },
    {
        id: 'profile',
        title: 'Manage Profiles',
        description: 'Edit or create new user profiles',
        icon: <UserIcon className="w-5 h-5" />,
        shortcut: 'G P',
        action: () => alert('Navigating to Profiles'),
        category: 'Navigation',
    },
    {
        id: 'settings',
        title: 'System Settings',
        description: 'Configure API keys and preferences',
        icon: <CogIcon className="w-5 h-5" />,
        action: () => alert('Navigating to Settings'),
        category: 'Settings',
    },
    {
        id: 'upload',
        title: 'Upload New Video',
        description: 'Start the mass upload wizard',
        action: () => alert('Starting Upload'),
        category: 'Actions',
    },
    {
        id: 'scan',
        title: 'Scan Factory Folders',
        description: 'Trigger an immediate file system scan',
        shortcut: 'CTRL S',
        action: () => alert('Scanning...'),
        category: 'Actions',
    },
];

export const Default: Story = {
    args: {
        commands: mockCommands,
        onClose: () => console.log('Close requested'),
    },
};

export const Empty: Story = {
    args: {
        commands: [],
        onClose: () => console.log('Close requested'),
    },
};
