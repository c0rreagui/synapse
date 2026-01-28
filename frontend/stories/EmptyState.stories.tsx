import type { Meta, StoryObj } from '@storybook/nextjs';
import EmptyState from '../app/components/EmptyState';
import { InboxIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof EmptyState> = {
    title: 'App/Molecules/EmptyState',
    component: EmptyState,
    tags: ['autodocs'],
    parameters: {
        layout: 'padded',
        backgrounds: { default: 'dark' },
    },
};

export default meta;
type Story = StoryObj<typeof EmptyState>;

export const Default: Story = {
    args: {
        title: 'No Items Found',
        description: 'Try adjusting your filters or search query.',
    },
};

export const WithIcon: Story = {
    args: {
        icon: <MagnifyingGlassIcon style={{ width: 48, height: 48 }} />,
        title: 'No Search Results',
        description: 'We could not find what you were looking for.',
    },
};

export const WithAction: Story = {
    args: {
        icon: <InboxIcon style={{ width: 48, height: 48 }} />,
        title: 'Inbox Empty',
        description: 'You have no new messages at the moment.',
        action: {
            label: 'Refresh',
            onClick: () => alert('Refreshed!'),
        },
    },
};
