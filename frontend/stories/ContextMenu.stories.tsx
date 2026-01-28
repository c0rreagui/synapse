import type { Meta, StoryObj } from '@storybook/nextjs';
import ContextMenu from '../app/components/ContextMenu';
import { PencilIcon, TrashIcon, DocumentDuplicateIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof ContextMenu> = {
    title: 'App/Molecules/ContextMenu',
    component: ContextMenu,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
    decorators: [
        (Story) => (
            <div className="h-[300px] w-[500px] flex items-center justify-center border border-dashed border-gray-700 rounded-xl">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof ContextMenu>;

export const Default: Story = {
    args: {
        children: (
            <div className="bg-gray-800 p-8 rounded-lg text-gray-300 cursor-context-menu hover:bg-gray-700 transition">
                Right Click Me
            </div>
        ),
        items: [
            {
                id: 'edit',
                label: 'Edit',
                icon: <PencilIcon className="w-4 h-4" />,
                shortcut: 'Ctrl+E',
                action: () => alert('Edit clicked'),
            },
            {
                id: 'duplicate',
                label: 'Duplicate',
                icon: <DocumentDuplicateIcon className="w-4 h-4" />,
                action: () => alert('Duplicate clicked'),
            },
            {
                id: 'delete',
                label: 'Delete',
                icon: <TrashIcon className="w-4 h-4" />,
                danger: true,
                shortcut: 'Del',
                action: () => alert('Delete clicked'),
            },
        ],
    },
};
