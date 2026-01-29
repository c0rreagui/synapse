import type { Meta, StoryObj } from '@storybook/react';
import BatchUploadModal from '../app/components/batch/BatchModal';
// Mock fn
const fn = () => { };

// Mock Profiles
const MOCK_PROFILES = [
    { id: '1', label: 'Atlas Hunter', username: '@atlas_hunter', avatar_url: 'https://i.pravatar.cc/150?u=1', status: 'active' as const },
];

const meta = {
    title: 'Organisms/Batch/BatchModal',
    component: BatchUploadModal,
    parameters: {
        layout: 'fullscreen',
        docs: {
            story: {
                inline: false,
                iframeHeight: 800,
            },
        },
    },
    tags: ['autodocs'],
    args: {
        isOpen: true,
        onClose: fn,
        onSuccess: fn,
        profiles: MOCK_PROFILES,
    },
} satisfies Meta<typeof BatchUploadModal>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Open: Story = {
    args: {
        isOpen: true,
    },
};

export const Closed: Story = {
    args: {
        isOpen: false,
    },
};
