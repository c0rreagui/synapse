import type { Meta, StoryObj } from '@storybook/react';
import QuickActions from '../app/components/QuickActions';
import {
    PencilSquareIcon,
    TrashIcon,
    ShareIcon,
    DocumentDuplicateIcon
} from '@heroicons/react/24/outline';

const meta: Meta<typeof QuickActions> = {
    title: 'App/Molecules/QuickActions',
    component: QuickActions,
    tags: ['autodocs'],
    parameters: {
        layout: 'centered',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof QuickActions>;

export const Default: Story = {
    args: {
        actions: [
            {
                id: 'edit',
                label: 'Edit',
                icon: <PencilSquareIcon className="w-5 h-5" />,
                onClick: () => console.log('Edit clicked'),
                shortcut: 'Cmd+E'
            },
            {
                id: 'duplicate',
                label: 'Duplicate',
                icon: <DocumentDuplicateIcon className="w-5 h-5" />,
                onClick: () => console.log('Duplicate clicked'),
                shortcut: 'Cmd+D'
            },
            {
                id: 'share',
                label: 'Share',
                icon: <ShareIcon className="w-5 h-5" />,
                onClick: () => console.log('Share clicked'),
            },
        ]
    }
};

export const WithDestructiveAction: Story = {
    args: {
        actions: [
            {
                id: 'edit',
                label: 'Edit',
                icon: <PencilSquareIcon className="w-5 h-5" />,
                onClick: () => console.log('Edit clicked'),
            },
            {
                id: 'delete',
                label: 'Delete',
                icon: <TrashIcon className="w-5 h-5 text-red-400" />,
                onClick: () => console.log('Delete clicked'),
                shortcut: 'Del'
            },
        ]
    }
};
