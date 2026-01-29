import type { Meta, StoryObj } from '@storybook/react';
import CommandPalette from '../app/components/CommandPalette';
// Mock fn
const fn = () => { };
import { Home, Settings, User, Plus } from 'lucide-react';

const MOCK_COMMANDS = [
    { id: '1', title: 'Go to Home', action: fn, icon: <Home size={18} />, category: 'Navigation', shortcut: 'G H' },
    { id: '2', title: 'Profile Settings', action: fn, icon: <User size={18} />, category: 'Navigation', shortcut: 'G P' },
    { id: '3', title: 'System Settings', action: fn, icon: <Settings size={18} />, category: 'Navigation' },
    { id: '4', title: 'New Project', action: fn, icon: <Plus size={18} />, category: 'Actions', shortcut: 'Ctrl+N' },
    { id: '5', title: 'Create Ticket', action: fn, category: 'Actions' },
];

const meta = {
    title: 'Organisms/CommandPalette',
    component: CommandPalette,
    parameters: {
        layout: 'fullscreen',
    },
    tags: ['autodocs'],
    args: {
        isOpen: true,
        onClose: fn,
        commands: MOCK_COMMANDS,
    },
} satisfies Meta<typeof CommandPalette>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Open: Story = {
    args: {
        isOpen: true,
    },
    decorators: [
        (Story) => (
            <div className="h-[500px] w-full bg-[#0d1117] relative">
                <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                    Press CMD+K to open (simulated)
                </div>
                <Story />
            </div>
        ),
    ],
};

export const Closed: Story = {
    args: {
        isOpen: false,
    },
};
